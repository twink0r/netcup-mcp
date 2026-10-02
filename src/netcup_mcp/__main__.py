"""Entry point: ``netcup-mcp``, ``python -m netcup_mcp``.

Usage:
    netcup-mcp [--config PATH] [--account NAME] [--list-accounts]
"""

from __future__ import annotations

import argparse
import json
import sys

from .config import ConfigError, load_config


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="netcup-mcp",
        description="MCP server for the netcup CCP domain webservice.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="config file to use; defaults to $NETCUP_MCP_CONFIG, then "
        "./netcup-mcp.toml, then ~/.config/netcup-mcp/config.toml",
    )
    parser.add_argument(
        "--account",
        metavar="NAME",
        help="override the default account for this run",
    )
    parser.add_argument(
        "--list-accounts",
        action="store_true",
        help="print the configured accounts as JSON and exit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Run the netcup MCP server over stdio."""
    args = _parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"netcup-mcp: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.account:
        if args.account not in config.accounts:
            known = ", ".join(sorted(config.accounts)) or "none configured"
            print(
                f"netcup-mcp: unknown account {args.account!r}. "
                f"Available accounts: {known}.",
                file=sys.stderr,
            )
            raise SystemExit(1)
        config.default_account = args.account

    if args.list_accounts:
        summary = {
            "config_file": str(config.path) if config.path else None,
            "default_account": config.default_account,
            "accounts": [
                {
                    "name": account.name,
                    "default": account.name == config.default_account,
                    "customernumber": account.customernumber,
                    "description": account.description,
                }
                for account in (
                    config.accounts[name] for name in sorted(config.accounts)
                )
            ],
        }
        print(json.dumps(summary, indent=2))
        return

    try:
        from .server import main as run_server

        run_server(config)
    except ConfigError as exc:
        print(f"netcup-mcp: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
