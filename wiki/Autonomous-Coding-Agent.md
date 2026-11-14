# SYNAX Studio IDE & Autonomous Coding Agent

## 1. SYNAX Studio IDE (`src/synax/studio_app.py`)

SYNAX runs both as a **Full-Screen VS Code Application (`synax.openStudio`)** and as a **Standalone macOS Desktop Application (`/Applications/SYNAX Studio.app`)**:

```bash
# Launch standalone SYNAX Studio App window
./synax studio

# Build / update /Applications/SYNAX Studio.app bundle
./synax studio --build-app
```

## 2. Autonomous Coding Agent (`src/synax/agent.py`)

`./synax code` launches an interactive, tool-calling software engineering agent confined to the workspace root with explicit approval gates:

- **Tools**: `list_files`, `read_file`, `grep`, `write_file`, `edit_file`, `bash`, `sx_check`, `sx_run`
- **Project Memory**: Automatically loads `SYNAX.md` at session startup.
- **Model Providers**: Supports Anthropic Claude, Google Gemini, OpenRouter, Groq, Z.ai GLM, and local Ollama.
