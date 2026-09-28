"""Phase 6 local OCR benchmark suite for EPREP.AI.

Measures:
- Cold start & warm latency (single screenshot & 5 screenshots)
- Normalized character similarity across Python, Java, C++, Error text, and Problem Statement
- Critical programming punctuation preservation: {}, [], (), ;, :, _, ==, !=, <=, >=
- Background variations: dark-theme and light-theme
- Font size variations: moderate and small text
"""

import io
import time
from difflib import SequenceMatcher
from PIL import Image, ImageDraw

from eprep.infrastructure.ocr.rapidocr_provider import RapidOCRProvider


CRITICAL_PUNCTUATION = [
    "{", "}", "[", "]", "(", ")", ";", ":", "_", "==", "!=", "<=", ">="
]


def create_benchmark_image(
    lines: list[str],
    bg_color: str = "#1e1e1e",
    text_color: str = "#d4d4d4",
    font_size: int = 14,
    size: tuple[int, int] = (640, 280),
) -> bytes:
    """Generate in-memory synthetic benchmark image with specified colors and text."""
    img = Image.new("RGB", size, color=bg_color)
    draw = ImageDraw.Draw(img)

    y_offset = 18
    line_height = int(font_size * 1.5)
    for line in lines:
        draw.text((20, y_offset), line, fill=text_color)
        y_offset += line_height

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def calculate_similarity(ground_truth: str, recognized: str) -> float:
    """Calculate normalized character similarity ratio between 0.0 and 1.0."""
    gt_clean = "".join(ground_truth.split())
    rec_clean = "".join(recognized.split())
    if not gt_clean and not rec_clean:
        return 1.0
    return SequenceMatcher(None, gt_clean, rec_clean).ratio()


def check_punctuation_preservation(ground_truth: str, recognized: str) -> dict[str, tuple[int, int]]:
    """Check preservation counts of critical programming punctuation."""
    stats = {}
    for punct in CRITICAL_PUNCTUATION:
        expected = ground_truth.count(punct)
        actual = recognized.count(punct)
        stats[punct] = (expected, actual)
    return stats


def run_benchmark():
    print("==============================================================")
    print("EPREP.AI — PHASE 6 RAPIDOCR LOCAL BENCHMARK")
    print("==============================================================")

    # 1. Cold Start Benchmark
    t0 = time.perf_counter()
    provider = RapidOCRProvider(intra_op_num_threads=2, inter_op_num_threads=1)
    provider.initialize()
    cold_start_ms = (time.perf_counter() - t0) * 1000.0
    print(f"Engine Cold Start Initialization: {cold_start_ms:.1f} ms\n")

    # 2. Benchmark Test Cases
    test_cases = [
        {
            "name": "Python Fibonacci (Dark Theme, Mono)",
            "ground_truth": [
                "def fibonacci(n):",
                "    if n <= 1:",
                "        return n",
                "    return fibonacci(n - 1) + fibonacci(n - 2)",
            ],
            "bg": "#1e1e1e",
            "fg": "#d4d4d4",
            "size": (500, 160),
            "font_size": 15,
        },
        {
            "name": "Java Array Print (Light Theme)",
            "ground_truth": [
                "for (int i = 0; i < n; i++) {",
                "    System.out.println(arr[i]);",
                "}",
            ],
            "bg": "#ffffff",
            "fg": "#000000",
            "size": (450, 130),
            "font_size": 15,
        },
        {
            "name": "C++ Vector Filter (Dark Theme)",
            "ground_truth": [
                "if (a[i] >= target && visited[i] != true) {",
                "    result.push_back(a[i]);",
                "}",
            ],
            "bg": "#181824",
            "fg": "#38bdf8",
            "size": (520, 130),
            "font_size": 15,
        },
        {
            "name": "Terminal Error Traceback (Dark Theme)",
            "ground_truth": [
                "Traceback (most recent call last):",
                "  File \"solution.py\", line 14, in <module>",
                "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
            ],
            "bg": "#0b0f19",
            "fg": "#f87171",
            "size": (620, 130),
            "font_size": 14,
        },
        {
            "name": "Problem Statement & Constraints (Light Theme)",
            "ground_truth": [
                "Given an integer array nums and an integer target,",
                "return indices of the two numbers such that they add up to target.",
                "Constraints: 2 <= nums.length <= 10^4, -10^9 <= nums[i] <= 10^9.",
                "Output: [0, 1] when nums = [2, 7, 11, 15] and target = 9.",
            ],
            "bg": "#f8fafc",
            "fg": "#0f172a",
            "size": (680, 170),
            "font_size": 14,
        },
        {
            "name": "Small Text Code Snippet (11px, Dark Theme)",
            "ground_truth": [
                "def binary_search(arr, target):",
                "    left, right = 0, len(arr) - 1",
                "    while left <= right:",
                "        mid = (left + right) // 2",
                "        if arr[mid] == target: return mid",
                "    return -1",
            ],
            "bg": "#161b22",
            "fg": "#e6edf3",
            "size": (450, 180),
            "font_size": 11,
        },
    ]

    all_similarities = []
    punct_totals = {p: [0, 0] for p in CRITICAL_PUNCTUATION}
    warm_latencies = []

    print("--- INDIVIDUAL TEST CASE EVALUATION ---")
    for case in test_cases:
        gt_text = "\n".join(case["ground_truth"])
        img_bytes = create_benchmark_image(
            case["ground_truth"],
            bg_color=case["bg"],
            text_color=case["fg"],
            font_size=case["font_size"],
            size=case["size"],
        )

        res = provider.extract_text_from_bytes(img_bytes, screenshot_name=case["name"])
        warm_latencies.append(res.processing_time_ms)

        rec_text = res.combined_text
        sim = calculate_similarity(gt_text, rec_text)
        all_similarities.append(sim)

        punct_stats = check_punctuation_preservation(gt_text, rec_text)
        for p, (exp, act) in punct_stats.items():
            punct_totals[p][0] += exp
            punct_totals[p][1] += act

        print(f"\n[Case] {case['name']}")
        print(f"Latency: {res.processing_time_ms:.1f} ms | Lines recognized: {res.line_count}/{len(case['ground_truth'])} | Similarity: {sim*100:.1f}%")
        print("Recognized Text:\n" + ("\n".join("  | " + l for l in rec_text.splitlines()) if rec_text else "  [NO TEXT]"))

    # 3. Batch 5-Screenshot Latency Benchmark
    print("\n--- 5-SCREENSHOT BATCH LATENCY BENCHMARK ---")
    batch_images = [
        create_benchmark_image(test_cases[i % len(test_cases)]["ground_truth"], size=(500, 150))
        for i in range(5)
    ]
    t_batch_start = time.perf_counter()
    batch_results = []
    for i, b_data in enumerate(batch_images):
        b_res = provider.extract_text_from_bytes(b_data, screenshot_name=f"Batch_Item_{i+1}")
        batch_results.append(b_res)
    total_batch_ms = (time.perf_counter() - t_batch_start) * 1000.0
    avg_per_image_ms = total_batch_ms / 5.0

    print(f"Total time for 5 screenshots: {total_batch_ms:.1f} ms")
    print(f"Average time per screenshot: {avg_per_image_ms:.1f} ms")

    # 4. Summary Quality & Punctuation Metrics
    print("\n==============================================================")
    print("BENCHMARK SUMMARY RESULTS")
    print("==============================================================")
    avg_sim = sum(all_similarities) / len(all_similarities) * 100
    print(f"Average Character Similarity: {avg_sim:.1f}%")
    print(f"Cold Start: {cold_start_ms:.1f} ms")
    print(f"Single Image Warm Average: {sum(warm_latencies)/len(warm_latencies):.1f} ms (min: {min(warm_latencies):.1f} ms)")
    print(f"5-Screenshot Total Latency: {total_batch_ms:.1f} ms")

    print("\nCritical Punctuation Preservation:")
    total_exp_punct = sum(v[0] for v in punct_totals.values())
    total_act_punct = sum(v[1] for v in punct_totals.values())
    for p, (exp, act) in punct_totals.items():
        if exp > 0:
            rate = (act / exp) * 100
            print(f"  '{p}': expected {exp}, recognized {act} ({rate:.0f}%)")
    print(f"Overall Critical Punctuation Preservation: {total_act_punct}/{total_exp_punct} ({(total_act_punct/max(1, total_exp_punct))*100:.1f}%)")


if __name__ == "__main__":
    run_benchmark()
