# SYNAX (`.sx`) Language Support for Visual Studio Code

Official Visual Studio Code / Cursor / Antigravity IDE extension providing TextMate syntax highlighting, bracket & comment configuration, and verified kernel snippets for **SYNAX (`.sx`)**.

## Features

- **Dual-Format Syntax Highlighting (`.sx`):**
  - **Structured Kernel Syntax (`synax 0.1`):** `kernel`, `intent`, `require`, `safety`, `let`, `return`, `optimize`, `target`, tensor types (`tensor<f32>`, `f32`, `f64`, `i32`, `bool`), IEEE-754 Immune Shield policies (`nonfinite`, `range_check`, `input_bound`, `heal`, `preserve`, `reject`, `zero_output`), and math intrinsics (`sqrt`, `square`, `abs`, `clamp`, `min`, `max`, `sigmoid`, `tanh`, `relu`, `exp`, `log`, `sin`, `cos`).
  - **Declarative Intent Syntax:** `niyet:`, `kural:`, `hedef:`, `formül:` (and English `intent:`, `rule:`, `target:`, `formula:`).
  - **Comments:** `//` line comments, `#` line comments, and `/* ... */` block comments.
- **Built-in Code Snippets:**
  - `kernel` — Structured `synax 0.1` kernel scaffold with `safety` block.
  - `cpp` — Retrospective Coronary Perfusion Pressure (`dbp - cvp`) research kernel with `heal(0.0)` and `clamp(-50.0, 300.0)`.
  - `safety` — IEEE-754 `nonfinite`, `input_bound`, and `range_check` policy block.
  - `niyet` — Declarative `niyet:` / `kural:` / `hedef:` specification.

## Installation

### Option 1: Local Symlink (Development / Instant Activation)

Link this directory directly into your VS Code extensions folder and reload the window:

```bash
# macOS / Linux (VS Code)
ln -s "$(pwd)/editors/vscode-synax" ~/.vscode/extensions/synaxcode.synax-lang-0.5.0
```

### Option 2: Package and Install `.vsix`

```bash
cd editors/vscode-synax
npx @vscode/vsce package
code --install-extension synax-lang-0.5.0.vsix
```

## CLI Workflow Integration

Once you save a `.sx` file, verify and compile it from the integrated terminal:

```bash
# Static IR inspection + Dual-Reference IEEE-754 check
./synax check examples/hemodynamic_cpp.sx

# 19-suite differential verification + SIMD synthesis + warm-cache benchmark
./synax compile examples/hemodynamic_cpp.sx
```

## License & Research Disclaimer

Licensed under the [Apache License, Version 2.0](../../LICENSE). Biomedical examples are strictly for retrospective academic research and are **not** clinical medical devices; see [`MEDICAL_RESEARCH_DISCLAIMER.md`](../../MEDICAL_RESEARCH_DISCLAIMER.md).
