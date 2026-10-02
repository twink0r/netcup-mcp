"""Tests for the netcup MCP server.

Run with: uv run pytest
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from netcup_mcp.client import AccountRegistry, NetcupClient, NetcupError
from netcup_mcp.config import Account, Config, IMPLICIT_ACCOUNT
from netcup_mcp.server import build_server
from netcup_mcp.tool_specs import TOOL_NAMES, TOOL_SPECS

HIDDEN_PARAMS = {"customernumber", "apikey", "apipassword", "apisessionid"}


def make_config(names: tuple[str, ...] = ("default",)) -> Config:
    return Config(
        accounts={
            name: Account(name=name, customernumber=f"1000{index}",
                          apikey="key", apipassword="password")
            for index, name in enumerate(names)
        },
        default_account=names[0],
    )


def make_registry(names: tuple[str, ...] = ("default",), **kwargs) -> AccountRegistry:
    return AccountRegistry(make_config(names), **kwargs)


def make_client(**kwargs) -> NetcupClient:
    return NetcupClient("123456", "key", "password", **kwargs)


def test_tool_names_are_snake_case() -> None:
    for action, name in TOOL_NAMES.items():
        assert name == name.lower()
        assert " " not in name
        assert action in TOOL_SPECS


def test_session_params_are_never_exposed() -> None:
    """Credentials must not reach the model through any schema."""
    for action, spec in TOOL_SPECS.items():
        for param in spec["inputSchema"].get("properties", {}):
            assert param not in HIDDEN_PARAMS, f"{action} exposes {param}"


def test_every_spec_field_is_documented() -> None:
    for action, spec in TOOL_SPECS.items():
        assert spec["description"].strip(), f"{action} has no description"
        for param, schema in spec["inputSchema"].get("properties", {}).items():
            assert schema.get("description", "").strip(), f"{action}.{param} undocumented"


def test_server_registers_all_tools() -> None:
    server = build_server(make_registry())
    tools = asyncio.run(server.list_tools())
    assert {t.name for t in tools} == set(TOOL_NAMES.values()) | {"list_accounts"}


def test_server_serves_documented_schema() -> None:
    server = build_server(make_registry())
    tools = {t.name: t for t in asyncio.run(server.list_tools())}
    # The DNS record tool must expose the nested record shape, not a bare string.
    schema = tools["update_dns_records"].input_schema
    records = schema["properties"]["dnsrecordset"]["properties"]["dnsrecords"]["items"]
    assert {"hostname", "type", "destination"} <= set(records["properties"])


def mock_handler(responses: dict[str, dict]) -> object:
    """Return an httpx MockTransport handler driven by the call action."""

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        action = payload.get("action", "")
        return httpx.Response(200, json=responses[action])

    return httpx.MockTransport(handler)


def test_login_is_cached_across_calls() -> None:
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        calls.append(payload)
        if payload.get("action") == "login":
            return httpx.Response(200, json={"status": "success", "responsedata": "SESSION123"})
        return httpx.Response(
            200,
            json={"status": "success", "responsedata": json.dumps([{"domainname": "example.com"}])},
        )

    client = NetcupClient("123456", "key", "password")
    client._post = lambda payload: _run(handler, payload)  # type: ignore[method-assign]

    asyncio.run(client.call("infoDomain", domainname="example.com"))
    asyncio.run(client.call("infoDomain", domainname="other.com"))

    assert [c.get("action") for c in calls] == ["login", "infoDomain", "infoDomain"]
    assert calls[1]["apisessionid"] == "SESSION123"
    # Credentials are added by the client, not required from the model.
    assert calls[1]["apikey"] == "key"


def test_session_error_triggers_one_relogin() -> None:
    sequence = [
        {"status": "success", "responsedata": "SESSION1"},
        {"status": "error", "statuscode": 4010, "shortmessage": "Session invalid"},
        {"status": "success", "responsedata": "SESSION2"},
        {"status": "success", "responsedata": json.dumps({"ok": True})},
    ]
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        seen.append(payload)
        return httpx.Response(200, json=sequence[len(seen) - 1])

    client = NetcupClient("123456", "key", "password")
    client._post = lambda payload: _run(handler, payload)  # type: ignore[method-assign]

    result = asyncio.run(client.call("infoDomain", domainname="example.com"))

    assert json.loads(result["responsedata"]) == {"ok": True}
    assert [p.get("action") for p in seen] == ["login", "infoDomain", "login", "infoDomain"]
    assert seen[3]["apisessionid"] == "SESSION2"


def test_api_error_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "error",
                "statuscode": 4013,
                "shortmessage": "Validation Error.",
                "longmessage": "Invalid entry for field apikey",
            },
        )

    client = NetcupClient("123456", "key", "password")
    client._post = lambda payload: _run(handler, payload)  # type: ignore[method-assign]

    with pytest.raises(NetcupError) as excinfo:
        asyncio.run(client.call("infoDomain", domainname="example.com"))
    assert excinfo.value.statuscode == 4013
    assert "apikey" in excinfo.value.longmessage


def test_unset_parameters_are_not_sent() -> None:
    sent: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        sent.append(payload)
        if payload.get("action") == "login":
            return httpx.Response(200, json={"status": "success", "responsedata": "S"})
        return httpx.Response(200, json={"status": "success", "responsedata": "{}"})

    client = NetcupClient("123456", "key", "password")
    client._post = lambda payload: _run(handler, payload)  # type: ignore[method-assign]

    asyncio.run(client.call("infoDomain", domainname="example.com", registryinformationflag=None))

    assert "registryinformationflag" not in sent[-1]


def test_tool_rejects_unknown_argument() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "success", "responsedata": "{}"})

    registry = make_registry()
    client = registry.client()
    client._post = lambda payload: _run(handler, payload)  # type: ignore[method-assign]
    server = build_server(registry)
    tool = server._tool_manager.get_tool("info_domain")

    # Undeclared arguments are rejected rather than silently dropped.
    with pytest.raises(Exception):
        asyncio.run(tool.run({"domainname": "example.com", "bogus": 1}, context=None))


def test_each_tool_validates_against_its_own_schema() -> None:
    """Regression: handlers must not share the last-registered tool's schema."""
    server = build_server(make_registry())

    # listall_domains takes no arguments; domainname belongs to other tools.
    with pytest.raises(Exception):
        asyncio.run(
            server._tool_manager.get_tool("listall_domains").run({"domainname": "x"}, context=None)
        )


def test_required_arguments_are_enforced() -> None:
    server = build_server(make_registry())
    tool = server._tool_manager.get_tool("info_domain")
    with pytest.raises(Exception):
        asyncio.run(tool.run({}, context=None))


def test_required_fields_are_declared() -> None:
    """A tool with no required argument must genuinely take none."""
    for action, spec in TOOL_SPECS.items():
        required = spec["inputSchema"].get("required", [])
        assert set(required) <= set(spec["inputSchema"]["properties"]), action


def test_tool_reports_api_error_to_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"status": "error", "statuscode": 4013, "shortmessage": "Validation Error."},
        )

    registry = make_registry()
    client = registry.client()
    client._post = lambda payload: _run(handler, payload)  # type: ignore[method-assign]
    server = build_server(registry)
    tool = server._tool_manager.get_tool("info_domain")

    result = asyncio.run(tool.run({"domainname": "example.com"}, context=None))
    assert "netcup API error" in _text(result)


def _text(result) -> str:
    """Flatten a tool result, which may be a string or content blocks."""
    if isinstance(result, str):
        return result
    return "".join(getattr(block, "text", "") for block in result.content)


def _run(handler, payload):
    """Call the mock transport synchronously for the async _post."""
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            request = client.build_request(
                "POST", "https://example.test/?JSON", json=payload,
                headers={"Content-Type": "application/json"},
            )
            response = await client.send(request)
            return response.json()

    return go()
