# EPREP.AI

EPREP.AI is a local-first Windows desktop AI coding assistant built in Python.

It assists users in solving programming problems from screenshots and inserting approved code into their preferred editor via a safe, hotkey-controlled workflow. The project operates with a ₹0 recurring-cost model with zero cloud dependencies.

> **Status**: Under active phase-by-phase development. Currently at Phase 4 (Screenshot Input & Session Management).

---

## Implemented Capabilities (Phase 4)

- Local image file upload (`PNG`, `JPEG`, `WebP`)
- Drag-and-drop screenshot loading
- Image clipboard paste (`Ctrl+V`)
- Memory-first session management (zero permanent disk storage)
- Invariant limit of maximum 5 screenshots per problem
- Real-time thumbnail preview cards with individual remove and clear all

---

## Supported Programming Languages (V1)

EPREP.AI V1 is strictly focused on:
- Python
- Java
- C
- C++
- JavaScript
- TypeScript

---

## Development Setup

### 1. Activate Environment

In PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install Development Package

Install the project in editable mode with development dependencies:
```powershell
python -m pip install -e ".[dev]"
```

### 3. Launch Desktop UI

Run the desktop application:
```powershell
eprep-ai
```
*(or `python -m eprep.main`)*

### 4. Run Tests

Execute the automated test suite:
```powershell
python -m pytest
```

---

## Architecture Documentation

See [`docs/architecture.md`](docs/architecture.md) for the complete, approved system architecture.
