"""Entry point: `netcup-mcp` or `python -m netcup_mcp`."""

from __future__ import annotations

import sys


def main() -> None:
    """Run the netcup MCP server over stdio."""
    from .server import main as run_server

    try:
        run_server()
    except RuntimeError as exc:
        print(f"netcup-mcp: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
