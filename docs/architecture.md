# EPREP.AI — Architecture Specification (V1)

This document records the approved Phase 1 architecture as the repository source of truth.

---

## 1. Product Identity & Platform
- **Target Platform**: Windows x64 Desktop.
- **Runtime Target**: Python 3.12.x.
- **Cost Model**: ₹0 recurring software/API cost.
- **Operating Mode**: Local-first AI, fully offline-capable, no mandatory cloud API dependencies.
- **Data Persistence**: Zero permanent problem/session database. All analysis and image states are strictly session-based and cleared on exit.

---

## 2. Architectural Layers

The codebase follows a strict four-layer architecture:

1. **Presentation Layer** (`src/eprep/ui/`):
   - PySide6 (Qt 6) widgets, translucent snipping overlays, code viewer, and window lifecycle.
   - Runs exclusively on the Qt GUI thread.
2. **Application Layer** (`src/eprep/application/`):
   - Coordinates user workflows (screenshot ingestion, problem analysis requests, output execution).
   - Manages workflow state transitions without UI coupling.
3. **Domain Layer** (`src/eprep/domain/`):
   - Core business logic, domain models, invariant rules (max 5 screenshots, exactly 6 supported languages), typing state machines, and domain exceptions.
   - Pure Python with zero external infrastructure dependencies.
4. **Infrastructure Layer** (`src/eprep/infrastructure/`):
   - Local Ollama HTTP client adapter.
   - Native Windows `RegisterHotKey` and `SendInput` adapters via `ctypes`.
   - Pillow-based image normalization.
   - Local configuration and sanitizing logger.

---

## 3. Locked Technology Stack

- **UI Framework**: PySide6 (Qt 6 for Python).
- **Imaging**: Pillow (PIL).
- **HTTP Client**: `httpx` (local Ollama REST communication at `http://127.0.0.1:11434`).
- **Data Modeling & Validation**: `pydantic`.
- **Testing**: `pytest`.
- **Hotkeys & Input Simulation**: Native Windows Win32 API (`RegisterHotKey`, `SendInput`) via Python standard library `ctypes`.
- **Packaging (Future)**: PyInstaller.

---

## 4. Screenshot Pipeline

- **Session Limit**: Maximum 5 screenshots per problem.
- **Storage Strategy**: Memory-first (`QImage` / `PIL.Image`). Disk caching is avoided unless explicitly needed by downstream tools; temporary files in `%LOCALAPPDATA%\EPREP.AI\temp` are cleaned deterministically.
- **Capture**: PySide6 `QScreen` on the GUI thread with interactive translucent selection overlays.
- **Adaptive Normalization**: Dimension inspection, aspect-ratio preservation, and contrast-aware resizing to preserve code font readability without premature downscaling.
- **Dual-Path Understanding**:
  - *Path A (Direct Vision)*: Image directly provided to a compact multimodal model.
  - *Path B (Hybrid OCR + Coder Fallback)*: Local OCR extracts text/code into structured context for a compact coding model.

---

## 5. AI Provider Architecture

- **Abstraction**: `BaseAIProvider` protocol decouples the application from model runtimes.
- **V1 Provider**: `LocalOllamaProvider` communicating with the local Ollama daemon.
- **Response Contract**: Structured `ProblemAnalysis` schema validated via Pydantic:
  - `detected_problem`
  - `constraints`
  - `input_description`
  - `output_description`
  - `examples`
  - `selected_language`
  - `explanation`
  - `generated_code`
  - `warnings`
- **Output Resilience**: Single controlled repair attempt on malformed model JSON; raises `AIResponseError` if invalid. Missing fields are never fabricated.

---

## 6. Output & Typing Engine

- **Safety Invariant**: Code output requires explicit, intentional user initiation. EPREP.AI never clicks or targets external windows autonomously.
- **Workflow**: User reviews code -> manually focuses target editor -> presses configured hotkey -> code inserted.
- **Output Modes**:
  - *Mode A (Safe Paste — Default)*: Inserts approved code via guarded clipboard paste to eliminate IDE auto-indentation and bracket duplication drift.
  - *Mode B (Simulated Typing — Fallback)*: Keystroke simulation via Windows `SendInput`.
- **Safety Controls**:
  - Global Start Hotkey (`RegisterHotKey`).
  - Global Emergency Stop Hotkey (`RegisterHotKey`) terminating typing immediately.
- **Clipboard Safety**:
  - EPREP.AI must not silently destroy existing non-text clipboard data.
  - Preserve supported clipboard formats where practical.
  - Never log clipboard contents.
  - Do not assume plain-text-only restoration is sufficient.
  - If a clipboard format cannot be restored safely, prefer preserving user data/correctness over aggressive automatic restoration.

---

## 7. Initial Supported Languages

Exactly 6 programming languages are supported in V1:
1. Python
2. Java
3. C
4. C++
5. JavaScript
6. TypeScript

---

## 8. Deferred Decisions

The following decisions are deliberately deferred to dedicated future phases:
1. **Final Local AI Model**: Deferred to the Local AI Benchmark & Integration phase (evaluating 1.5B–3B parameter candidates on the Athlon 3050U).
2. **OCR Engine Selection**: Deferred to the Local AI Benchmark & Integration phase.
3. **Adaptive Image Resolution Thresholds**: Deferred to the Screenshot & Vision Evaluation phase.
4. **PyInstaller Distribution Mode (Single-Folder vs Single-File)**: Deferred to the Packaging phase.
