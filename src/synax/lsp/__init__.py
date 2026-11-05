"""
SYNAX Language Server Protocol Package (`src/synax/lsp/__init__.py`)
=====================================================================
Provides real-time IDE diagnostics, hover semantics, and document formatting
for SYNAX (.sx) programs via standard JSON-RPC 2.0 (LSP 3.17).
"""

from .server import SynaxLanguageServer, run_lsp_server

__all__ = ["SynaxLanguageServer", "run_lsp_server"]
