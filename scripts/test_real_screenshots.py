"""Real-world screenshot validation script for Phase 6."""

import io
from PIL import Image, ImageDraw
from eprep.infrastructure.ocr.rapidocr_provider import RapidOCRProvider


def create_notepad_mock() -> bytes:
    # Notepad: Pure white, Lucida/Consolas look, plain black text
    img = Image.new("RGB", (550, 200), color="#ffffff")
    d = ImageDraw.Draw(img)
    d.text((15, 15), "# Solution for QuickSort", fill="#000000")
    d.text((15, 45), "def quicksort(items):", fill="#000000")
    d.text((15, 75), "    if len(items) <= 1:", fill="#000000")
    d.text((15, 105), "        return items", fill="#000000")
    d.text((15, 135), "    pivot = items[len(items) // 2]", fill="#000000")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_vscode_mock() -> bytes:
    # VS Code dark theme with syntax colors
    img = Image.new("RGB", (620, 220), color="#1e1e1e")
    d = ImageDraw.Draw(img)
    d.text((20, 15), "// C++ Two Pointers Approach", fill="#6a9955")
    d.text((20, 45), "int maxArea(vector<int>& height) {", fill="#dcdcaa")
    d.text((40, 75), "    int left = 0, right = height.size() - 1;", fill="#9cdcfe")
    d.text((40, 105), "    int max_water = 0;", fill="#9cdcfe")
    d.text((40, 135), "    while (left < right) {", fill="#c586c0")
    d.text((60, 165), "        max_water = max(max_water, min(height[left], height[right]));", fill="#dcdcaa")
    d.text((20, 195), "}", fill="#dcdcaa")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_question_mock() -> bytes:
    # Programming question screenshot
    img = Image.new("RGB", (700, 240), color="#ffffff")
    d = ImageDraw.Draw(img)
    d.text((20, 15), "1. Two Sum (Easy)", fill="#1a1a1a")
    d.text((20, 45), "Given an array of integers nums and an integer target, return indices of the two numbers.", fill="#333333")
    d.text((20, 75), "You may assume that each input would have exactly one solution.", fill="#333333")
    d.text((20, 115), "Example 1:", fill="#1a1a1a")
    d.text((20, 140), "Input: nums = [2,7,11,15], target = 9", fill="#444444")
    d.text((20, 165), "Output: [0,1]", fill="#444444")
    d.text((20, 195), "Constraints: 2 <= nums.length <= 10^4", fill="#555555")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_terminal_mock() -> bytes:
    # Windows Terminal / PowerShell: dark background with red error and yellow warning
    img = Image.new("RGB", (650, 180), color="#0c0c0c")
    d = ImageDraw.Draw(img)
    d.text((15, 15), "PS D:\\Personal project\\EPREP.AI> python main.py", fill="#cccccc")
    d.text((15, 45), "Traceback (most recent call last):", fill="#e74856")
    d.text((25, 75), "  File \"test_run.py\", line 42, in <module>", fill="#e74856")
    d.text((45, 105), "    val = calculate_score(data[\"key\"])", fill="#e74856")
    d.text((15, 135), "KeyError: 'key' not found in dictionary", fill="#e74856")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def validate_real_screens():
    provider = RapidOCRProvider(intra_op_num_threads=2, inter_op_num_threads=1)
    provider.initialize()

    scenarios = [
        ("1. Notepad Code", create_notepad_mock()),
        ("2. VS Code Editor", create_vscode_mock()),
        ("3. Programming Question", create_question_mock()),
        ("4. Terminal / Error", create_terminal_mock()),
    ]

    for name, data in scenarios:
        res = provider.extract_text_from_bytes(data, screenshot_name=name)
        print(f"\n=== {name} (Time: {res.processing_time_ms:.1f}ms, Lines: {res.line_count}) ===")
        for line in res.lines:
            print(f"  [{line.confidence:.2f}] {line.text}")


if __name__ == "__main__":
    validate_real_screens()
