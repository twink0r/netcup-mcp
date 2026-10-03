"""Live smoke tests against the real netcup API.

These need NETCUP_CUSTOMERNUMBER / NETCUP_APIKEY / NETCUP_APIPASSWORD in the
environment. Without them they skip.

    uv run pytest -m live
"""

from __future__ import annotations

import os

import pytest

from netcup_mcp.client import NetcupClient

pytestmark = pytest.mark.live

CREDENTIALS = ("NETCUP_CUSTOMERNUMBER", "NETCUP_APIKEY", "NETCUP_APIPASSWORD")

# Where credentials live. Credentials in env_files need a config file, so use
# the same discovery the server itself uses rather than a fixed path.
def _find_config() -> str | None:
    from netcup_mcp.config import find_config

    try:
        found = find_config()
    except Exception:
        return None
    return str(found) if found else None


CONFIG_PATH = _find_config()
HAVE_ENV = all(os.environ.get(name) for name in CREDENTIALS)
HAVE_CONFIG = bool(CONFIG_PATH and os.path.isfile(CONFIG_PATH))


def _client(account: str | None = None) -> NetcupClient:
    """Build a client from the config file, falling back to the environment."""
    from netcup_mcp.client import AccountRegistry
    from netcup_mcp.config import load_config

    if HAVE_CONFIG:
        return AccountRegistry(load_config(CONFIG_PATH)).client(account)
    return NetcupClient.from_env()


@pytest.mark.skipif(
    not (HAVE_ENV or HAVE_CONFIG),
    reason="no netcup credentials: set NETCUP_* or provide a config file",
)
def test_login_and_listall_domains() -> None:
    """log in, then list domains.

    ``listallDomains`` needs a reseller account; on a normal customer
    account netcup answers 4020. Accept either, but reject anything else.
    """
    import asyncio

    from netcup_mcp.client import NetcupError

    client = _client()

    async def go() -> None:
        try:
            session_id = await client.login()
            assert session_id, "login returned no session id"
            try:
                data = await client.call("listallDomains")
            except NetcupError as exc:
                # 4020 = not a reseller. That is a valid answer for a
                # customer account, not a failure of this client.
                assert exc.statuscode == 4020, exc
                return
            assert data["status"] == "success"
        finally:
            await client.aclose()

    asyncio.run(go())


@pytest.mark.skipif(
    not (HAVE_ENV or HAVE_CONFIG),
    reason="no netcup credentials: set NETCUP_* or provide a config file",
)
def test_every_configured_account_logs_in() -> None:
    """Each account in the config file must authenticate independently."""
    import asyncio

    from netcup_mcp.client import AccountRegistry
    from netcup_mcp.config import load_config

    config = load_config(os.environ.get("NETCUP_CONFIG"))
    if config.path is None:
        pytest.skip("no config file")

    registry = AccountRegistry(config)

    async def go() -> None:
        try:
            for name in config.names:
                session_id = await registry.client(name).login()
                assert session_id, f"{name}: no session id"
        finally:
            await registry.aclose()

    asyncio.run(go())


@pytest.mark.skipif(
    not (HAVE_ENV or HAVE_CONFIG),
    reason="no netcup credentials: set NETCUP_* or provide a config file",
)
def test_bad_credentials_raise_netcup_error() -> None:
    import asyncio

    from netcup_mcp.client import NetcupError

    client = NetcupClient("123456", "not-a-real-key", "not-a-real-password")

    async def go() -> None:
        try:
            await client.login()
        finally:
            await client.aclose()

    with pytest.raises(NetcupError) as excinfo:
        asyncio.run(go())
    assert excinfo.value.statuscode == 4013
