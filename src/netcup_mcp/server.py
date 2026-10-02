"""MCP server exposing the netcup CCP domain webservice as tools.

Built for the ``mcp`` 2.x SDK (``MCPServer``; ``FastMCP`` was the 1.x name).

Tool schemas are hand-written in :mod:`netcup_mcp.tool_specs` and taken from
the official netcup interface description. The SDK normally derives a schema
from the function signature, which would lose the per-field documentation, so
each registered tool gets its generated signature patched with the documented
schema.

Every tool takes an optional ``account`` argument, which is injected here
rather than in the specs, since it belongs to the server rather than to the
netcup API.
"""

from __future__ import annotations

import inspect
import json
import logging
from typing import Any

from mcp.server.mcpserver import MCPServer

from .client import AccountRegistry, NetcupError
from .config import Config, ConfigError, load_config
from .tool_specs import TOOL_NAMES, TOOL_SPECS

logger = logging.getLogger(__name__)

INSTRUCTIONS = """\
Tools for the netcup domain webservice (CCP API).

Most calls need an API session; the server logs in on demand and keeps
the session alive, so you never handle credentials.

Multiple accounts: every tool takes an optional `account` argument. Leave
it out to use the default account, or call list_accounts to see what is
configured. Each account has its own session, so switching is safe. Never
guess an account name; ask or use list_accounts.

Typical flow:
1. list_accounts to see which accounts are available.
2. listall_domains / listall_handle to see what an account owns.
3. info_domain, info_dns_zone, info_dns_records to inspect a domain.
4. update_dns_records to change DNS records. It replaces the whole record
   set, so call info_dns_records first and pass back everything you want
   to keep. Use hostname "@" for the zone apex.
5. create_handle before create_domain or transfer_domain, since domains
   need contact handle ids.

Destructive calls (cancel_domain, delete_handle, transfer_domain,
create_domain) cost money or cannot be undone. Confirm with the user
before calling them, and make sure you are acting on the intended account.
"""

LIST_ACCOUNTS_DESCRIPTION = """\
List the configured netcup accounts, and show which one is the default.

Use this before any call that depends on which account is in play, or when a
tool returns an unknown-account error.
"""

_ANNOTATIONS: dict[str, Any] = {
    "string": str,
    "integer": int,
    "boolean": bool,
    "object": dict,
    "array": list,
    "null": type(None),
}


def _annotation_for(schema: dict[str, Any]) -> Any:
    """Python annotation for a JSON schema fragment.

    Only used for server-side argument checking; the schema the model sees
    comes from TOOL_SPECS.
    """
    json_type = schema.get("type", "string")
    if isinstance(json_type, list):
        json_type = next((t for t in json_type if t != "null"), "null")
    return _ANNOTATIONS.get(json_type, str)


def _signature_for(schema: dict[str, Any]) -> inspect.Signature:
    """Build a keyword-only signature matching a tool's input schema."""
    properties: dict[str, Any] = schema.get("properties", {})
    required: list[str] = schema.get("required", [])

    parameters = []
    for name, field_schema in properties.items():
        annotation = _annotation_for(field_schema)
        if name not in required:
            annotation = annotation | None
        parameters.append(
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=annotation,
                default=inspect.Parameter.empty if name in required else None,
            )
        )
    return inspect.Signature(parameters)


def _with_account(schema: dict[str, Any], names: list[str]) -> dict[str, Any]:
    """Add the ``account`` argument to a tool schema."""
    account_property: dict[str, Any] = {
        "type": "string",
        "description": (
            "Which netcup account to use. Omit for the default account. "
            "Call list_accounts to see the available names."
        ),
    }
    if names:
        account_property["enum"] = names

    properties = dict(schema.get("properties", {}))
    properties["account"] = account_property

    return {
        "type": "object",
        "properties": properties,
        "required": list(schema.get("required", [])),
    }


def _format_result(action: str, data: dict[str, Any], account: str | None = None) -> str:
    payload: dict[str, Any] = {
        "action": action,
        "status": data.get("status"),
        "statuscode": data.get("statuscode"),
        "shortmessage": data.get("shortmessage"),
    }
    if account:
        payload["account"] = account
    if data.get("longmessage"):
        payload["longmessage"] = data["longmessage"]

    responsedata = data.get("responsedata")
    if responsedata:
        # infoDnsRecords nests its records under a "dnsrecords" key.
        payload["responsedata"] = responsedata

    return json.dumps(payload, indent=2, ensure_ascii=False, default=str)


def build_server(
    registry: AccountRegistry,
) -> MCPServer:
    """Create the MCP server with one tool per netcup API function.

    Args:
        registry: supplies a per-account client.
    """
    from . import __version__

    names = registry.names
    server = MCPServer("netcup", instructions=INSTRUCTIONS, version=__version__)

    for action, spec in TOOL_SPECS.items():
        tool_name = TOOL_NAMES[action]
        schema = _with_account(spec["inputSchema"], names)
        handler = _make_handler(registry, action)
        handler.__name__ = tool_name
        handler.__signature__ = _signature_for(schema)  # type: ignore[attr-defined]
        handler.__doc__ = spec["description"]

        tool = server._tool_manager.add_tool(
            handler, name=tool_name, description=spec["description"]
        )
        # Hand the model the documented schema; the SDK's generated one drops descriptions.
        tool.parameters = schema
        # Reject arguments the schema does not declare instead of dropping them silently.
        arg_model = tool.fn_metadata.arg_model
        arg_model.model_config["extra"] = "forbid"
        arg_model.model_rebuild(force=True)

    server._tool_manager.add_tool(
        _make_list_accounts(registry),
        name="list_accounts",
        description=LIST_ACCOUNTS_DESCRIPTION,
    )

    return server


def _make_handler(registry: AccountRegistry, action: str) -> Any:
    """Build the tool coroutine for one API function.

    A fresh closure per function, so each tool captures its own schema rather
    than the last one registered.
    """

    async def handler(**kwargs: Any) -> str:
        # Argument shape is already validated by the SDK against the tool schema;
        # this only turns API and transport failures into readable model output.
        account = kwargs.pop("account", None)
        try:
            client = registry.client(account)
            data = await client.call(action, **kwargs)
        except ConfigError as exc:
            return f"Configuration error: {exc}"
        except NetcupError as exc:
            where = f" (account {account or registry.config.default_account!r})" if account else ""
            return f"netcup API error{where}: {exc}"
        except Exception as exc:  # network, malformed JSON, bad config
            logger.exception("call to %s failed", action)
            return f"Error calling {action}: {exc}"
        return _format_result(action, data, client.name)

    return handler


def _make_list_accounts(registry: AccountRegistry) -> Any:
    """Build the list_accounts tool coroutine."""

    async def list_accounts() -> str:
        config = registry.config
        payload: dict[str, Any] = {
            "default_account": config.default_account,
            "accounts": registry.describe(),
        }
        if config.path:
            payload["config_file"] = str(config.path)
        return json.dumps(payload, indent=2, ensure_ascii=False)

    return list_accounts


def main(config: Config | None = None) -> None:
    """Run the server on stdio using an already-loaded config."""
    logging.basicConfig(level=logging.INFO)
    config = config or load_config()
    logger.info(
        "netcup-mcp: %d account(s), default %r%s",
        len(config.accounts),
        config.default_account,
        f", from {config.path}" if config.path else " (from environment)",
    )
    registry = AccountRegistry(config)
    build_server(registry).run(transport="stdio")
