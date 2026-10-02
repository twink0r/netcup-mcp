"""MCP server exposing the netcup CCP domain webservice as tools.

Built for the ``mcp`` 2.x SDK (``MCPServer``; ``FastMCP`` was the 1.x name).

Tool schemas are hand-written in :mod:`netcup_mcp.tool_specs` and taken from
the official netcup interface description. The SDK normally derives a schema
from the function signature, which would lose the per-field documentation, so
each registered tool gets its generated signature patched with the documented
schema.
"""

from __future__ import annotations

import inspect
import json
import logging
from typing import Any

from mcp.server.mcpserver import MCPServer

from .client import NetcupClient, NetcupError
from .tool_specs import TOOL_NAMES, TOOL_SPECS

logger = logging.getLogger(__name__)

INSTRUCTIONS = """\
Tools for the netcup domain webservice (CCP API).

Most calls need an API session; the server logs in on demand and keeps
the session alive, so you never handle credentials.

Typical flow:
1. listall_domains / listall_handle to see what the account owns.
2. info_domain, info_dns_zone, info_dns_records to inspect a domain.
3. update_dns_records to change DNS records. It replaces the whole record
   set, so call info_dns_records first and pass back everything you want
   to keep. Use hostname "@" for the zone apex.
4. create_handle before create_domain or transfer_domain, since domains
   need contact handle ids.

Destructive calls (cancel_domain, delete_handle, transfer_domain,
create_domain) cost money or cannot be undone. Confirm with the user
before calling them.
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


def _format_result(action: str, data: dict[str, Any]) -> str:
    payload: dict[str, Any] = {
        "action": action,
        "status": data.get("status"),
        "statuscode": data.get("statuscode"),
        "shortmessage": data.get("shortmessage"),
    }
    if data.get("longmessage"):
        payload["longmessage"] = data["longmessage"]

    responsedata = data.get("responsedata")
    if responsedata:
        if isinstance(responsedata, str):
            try:
                responsedata = json.loads(responsedata)
            except json.JSONDecodeError:
                pass
        payload["responsedata"] = responsedata

    return json.dumps(payload, indent=2, ensure_ascii=False, default=str)


def build_server(client: NetcupClient) -> MCPServer:
    """Create the MCP server with one tool per netcup API function."""
    from . import __version__

    server = MCPServer("netcup", instructions=INSTRUCTIONS, version=__version__)

    for action, spec in TOOL_SPECS.items():
        tool_name = TOOL_NAMES[action]
        schema = spec["inputSchema"]
        handler = _make_handler(client, action)
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

    return server


def _make_handler(client: NetcupClient, action: str) -> Any:
    """Build the tool coroutine for one API function.

    A fresh closure per function, so each tool captures its own schema rather
    than the last one registered.
    """
    async def handler(**kwargs: Any) -> str:
        # Argument shape is already validated by the SDK against the tool schema;
        # this only turns API and transport failures into readable model output.
        try:
            data = await client.call(action, **kwargs)
        except NetcupError as exc:
            return f"netcup API error: {exc}"
        except Exception as exc:  # network, malformed JSON, bad config
            logger.exception("call to %s failed", action)
            return f"Error calling {action}: {exc}"
        return _format_result(action, data)

    return handler


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    client = NetcupClient.from_env()
    build_server(client).run(transport="stdio")
