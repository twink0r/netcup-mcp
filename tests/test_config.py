"""Tests for config loading and multi-account routing."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from netcup_mcp.client import AccountRegistry, NetcupError
from netcup_mcp.config import (
    Config,
    ConfigError,
    expand_vars,
    load_config,
    parse_env_file,
)
from netcup_mcp.server import build_server


# --- env file parsing ---


def test_parse_env_file_handles_quotes_comments_and_export(tmp_path) -> None:
    env = tmp_path / "prod.env"
    env.write_text(
        "# a comment\n"
        "\n"
        "export NETCUP_CUSTOMERNUMBER=123456\n"
        'NETCUP_APIKEY="quoted-key"\n'
        "NETCUP_APIPASSWORD='quoted-pass'\n"
        "OTHER=value # trailing comment\n",
        encoding="utf-8",
    )
    values = parse_env_file(env)
    assert values["NETCUP_CUSTOMERNUMBER"] == "123456"
    assert values["NETCUP_APIKEY"] == "quoted-key"
    assert values["NETCUP_APIPASSWORD"] == "quoted-pass"
    assert values["OTHER"] == "value"


def test_parse_env_file_rejects_malformed_line(tmp_path) -> None:
    env = tmp_path / "bad.env"
    env.write_text("this is not a pair\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="KEY=value"):
        parse_env_file(env)


def test_parse_env_file_missing_file(tmp_path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        parse_env_file(tmp_path / "nope.env")


def test_expand_vars(monkeypatch) -> None:
    monkeypatch.setenv("SECRET", "s3cr3t")
    assert expand_vars("${SECRET}") == "s3cr3t"
    assert expand_vars("prefix-${SECRET}-suffix") == "prefix-s3cr3t-suffix"
    assert expand_vars("$SECRET") == "s3cr3t"
    # An unset variable expands to empty rather than raising.
    monkeypatch.delenv("ABSENT", raising=False)
    assert expand_vars("${ABSENT}") == ""
    assert expand_vars("no vars here") == "no vars here"


# --- config loading ---


def write_config(tmp_path, body: str, name: str = "netcup-mcp.toml"):
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def test_load_config_with_env_file(tmp_path) -> None:
    (tmp_path / "prod.env").write_text(
        "NETCUP_CUSTOMERNUMBER=111\nNETCUP_APIKEY=k1\nNETCUP_APIPASSWORD=p1\n",
        encoding="utf-8",
    )
    path = write_config(
        tmp_path,
        'default_account = "prod"\n'
        '[accounts.prod]\ndescription = "Production"\nenv_file = "prod.env"\n',
    )

    config = load_config(path)

    assert config.default_account == "prod"
    assert config.names == ["prod"]
    account = config.get("prod")
    assert (account.customernumber, account.apikey, account.apipassword) == ("111", "k1", "p1")
    assert account.description == "Production"
    assert config.path == path


def test_env_file_path_resolves_relative_to_config(tmp_path) -> None:
    """A relative env_file is relative to the config file, not the cwd."""
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    (secrets / "a.env").write_text(
        "NETCUP_CUSTOMERNUMBER=222\nNETCUP_APIKEY=k\nNETCUP_APIPASSWORD=p\n",
        encoding="utf-8",
    )
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    path = write_config(
        cfg_dir, '[accounts.a]\nenv_file = "../secrets/a.env"\n', name="netcup-mcp.toml"
    )

    config = load_config(path)
    assert config.get("a").customernumber == "222"


def test_load_config_multiple_accounts(tmp_path) -> None:
    (tmp_path / "a.env").write_text(
        "NETCUP_CUSTOMERNUMBER=1\nNETCUP_APIKEY=k\nNETCUP_APIPASSWORD=p\n", encoding="utf-8"
    )
    (tmp_path / "b.env").write_text(
        "NETCUP_CUSTOMERNUMBER=2\nNETCUP_APIKEY=k\nNETCUP_APIPASSWORD=p\n", encoding="utf-8"
    )
    path = write_config(
        tmp_path,
        'default_account = "b"\n'
        '[accounts.a]\nenv_file = "a.env"\n'
        '[accounts.b]\nenv_file = "b.env"\n'
        '[accounts.c]\n'
        'customernumber = "3"\napikey = "k"\napipassword = "p"\n',
    )

    config = load_config(path)
    assert config.names == ["a", "b", "c"]
    assert config.default_account == "b"
    assert config.get("a").customernumber == "1"
    assert config.get("b").customernumber == "2"
    assert config.get("c").customernumber == "3"


def test_inline_values_win_over_env_file(tmp_path) -> None:
    (tmp_path / "a.env").write_text(
        "NETCUP_CUSTOMERNUMBER=1\nNETCUP_APIKEY=from-file\nNETCUP_APIPASSWORD=p\n",
        encoding="utf-8",
    )
    path = write_config(tmp_path, '[accounts.a]\nenv_file = "a.env"\napikey = "inline"\n')
    assert load_config(path).get("a").apikey == "inline"


def test_inline_values_support_var_expansion(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MY_KEY", "from-env")
    path = write_config(
        tmp_path,
        '[accounts.a]\ncustomernumber = "9"\napikey = "${MY_KEY}"\napipassword = "p"\n',
    )
    assert load_config(path).get("a").apikey == "from-env"


def test_unknown_account_error_lists_known_names(tmp_path) -> None:
    path = write_config(tmp_path, '[accounts.alpha]\ncustomernumber = "1"\napikey = "k"\napipassword = "p"\n')
    config = load_config(path)
    with pytest.raises(ConfigError, match="alpha"):
        config.get("nope")


def test_default_account_falls_back_to_first(tmp_path) -> None:
    path = write_config(tmp_path, '[accounts.only]\ncustomernumber = "1"\napikey = "k"\napipassword = "p"\n')
    assert load_config(path).default_account == "only"


def test_invalid_default_account_is_rejected(tmp_path) -> None:
    path = write_config(
        tmp_path,
        'default_account = "ghost"\n'
        '[accounts.real]\ncustomernumber = "1"\napikey = "k"\napipassword = "p"\n',
    )
    with pytest.raises(ConfigError, match="ghost"):
        load_config(path)


def test_missing_credentials_reported_with_account_name(tmp_path) -> None:
    path = write_config(tmp_path, '[accounts.partial]\ncustomernumber = "1"\n')
    with pytest.raises(ConfigError, match="apikey"):
        load_config(path)


def test_invalid_toml_is_reported(tmp_path) -> None:
    path = write_config(tmp_path, "this is not = = toml\n")
    with pytest.raises(ConfigError, match="invalid TOML"):
        load_config(path)


def test_config_without_accounts_is_rejected(tmp_path) -> None:
    path = write_config(tmp_path, "default_account = \"x\"\n")
    with pytest.raises(ConfigError, match="accounts"):
        load_config(path)


def test_no_config_file_uses_environment(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("NETCUP_CUSTOMERNUMBER", "555")
    monkeypatch.setenv("NETCUP_APIKEY", "k")
    monkeypatch.setenv("NETCUP_APIPASSWORD", "p")
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.path is None
    assert config.names == ["default"]
    assert config.get().customernumber == "555"


def test_no_config_and_no_credentials_fails(monkeypatch, tmp_path) -> None:
    for name in ("NETCUP_CUSTOMERNUMBER", "NETCUP_APIKEY", "NETCUP_APIPASSWORD"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigError, match="Missing credentials"):
        load_config()


def test_explicit_missing_config_is_an_error(tmp_path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "absent.toml")


# --- routing ---


def test_each_account_gets_its_own_client() -> None:
    config = Config(
        accounts={
            "a": _account("a", "111"),
            "b": _account("b", "222"),
        },
        default_account="a",
    )
    registry = AccountRegistry(config)

    client_a = registry.client("a")
    client_b = registry.client("b")

    assert client_a is not client_b
    assert client_a.customernumber == "111"
    assert client_b.customernumber == "222"
    # Repeated calls reuse the same client, so the session is reused too.
    assert registry.client("a") is client_a
    # Omitting the account uses the default.
    assert registry.client() is client_a


def test_unknown_account_at_call_time(tmp_path) -> None:
    path = write_config(tmp_path, '[accounts.alpha]\ncustomernumber = "1"\napikey = "k"\napipassword = "p"\n')
    registry = AccountRegistry(load_config(path))
    server = build_server(registry)
    tool = server._tool_manager.get_tool("info_domain")

    result = asyncio.run(tool.run({"domainname": "x.com", "account": "ghost"}, context=None))
    assert "Unknown account" in _text(result)
    assert "alpha" in _text(result)


def test_tool_routes_to_the_named_account() -> None:
    registry = AccountRegistry(
        Config(
            accounts={"a": _account("a", "111"), "b": _account("b", "222")},
            default_account="a",
        )
    )
    sent: list[dict] = []

    async def _post(payload: dict) -> dict:
        sent.append(payload)
        return {"status": "success", "responsedata": "{}"}

    registry.client("a")._post = _post  # type: ignore[method-assign]
    registry.client("b")._post = _post  # type: ignore[method-assign]

    server = build_server(registry)
    tool = server._tool_manager.get_tool("info_domain")

    asyncio.run(tool.run({"domainname": "x.com"}, context=None))
    asyncio.run(tool.run({"domainname": "y.com", "account": "b"}, context=None))

    # Both calls logged in first, so filter those out.
    calls = [p for p in sent if p.get("action") == "infoDomain"]
    assert [c["customernumber"] for c in calls] == ["111", "222"]


def test_list_accounts_reports_names_and_default() -> None:
    registry = AccountRegistry(
        Config(
            accounts={
                "prod": _account("prod", "111", "Live"),
                "staging": _account("staging", "222", "Test"),
            },
            default_account="prod",
        )
    )
    server = build_server(registry)
    tool = server._tool_manager.get_tool("list_accounts")

    payload = json.loads(_text(asyncio.run(tool.run({}, context=None))))
    assert payload["default_account"] == "prod"
    by_name = {a["name"]: a for a in payload["accounts"]}
    assert by_name["prod"]["default"] is True
    assert by_name["staging"]["default"] is False
    assert by_name["staging"]["description"] == "Test"
    # Credentials must never be listed.
    assert "apikey" not in json.dumps(payload)
    assert "apipassword" not in json.dumps(payload)


def test_account_argument_is_in_every_tool_schema() -> None:
    registry = AccountRegistry(
        Config(accounts={"prod": _account("prod", "1")}, default_account="prod")
    )
    tools = {t.name: t for t in asyncio.run(build_server(registry).list_tools())}

    for name in [t for t in tools if t != "list_accounts"]:
        schema = tools[name].input_schema
        assert "account" in schema["properties"], name
        # account is never required; omitting it must mean the default account
        assert "account" not in schema.get("required", []), name
        assert schema["properties"]["account"]["enum"] == ["prod"], name


def test_api_error_names_the_account() -> None:
    registry = AccountRegistry(
        Config(accounts={"prod": _account("prod", "1")}, default_account="prod")
    )

    async def _post(payload: dict) -> dict:
        return {"status": "error", "statuscode": 4013, "shortmessage": "Validation Error."}

    registry.client("prod")._post = _post  # type: ignore[method-assign]
    server = build_server(registry)
    tool = server._tool_manager.get_tool("info_domain")

    result = _text(asyncio.run(tool.run({"domainname": "x.com", "account": "prod"}, context=None)))
    assert "netcup API error" in result
    assert "prod" in result


def _account(name: str, number: str, description: str = "") -> object:
    from netcup_mcp.config import Account

    return Account(
        name=name,
        customernumber=number,
        apikey="k",
        apipassword="p",
        description=description,
        source="test",
    )


def _text(result) -> str:
    if isinstance(result, str):
        return result
    return "".join(getattr(block, "text", "") for block in result.content)
