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


def _client() -> NetcupClient:
    return NetcupClient.from_env()


@pytest.mark.skipif(
    not all(os.environ.get(name) for name in CREDENTIALS),
    reason="netcup credentials not set",
)
def test_login_and_listall_domains() -> None:
    import asyncio

    client = _client()

    async def go() -> dict:
        try:
            session_id = await client.login()
            assert session_id
            return await client.call("listallDomains")
        finally:
            await client.aclose()

    data = asyncio.run(go())
    assert data["status"] == "success"


@pytest.mark.skipif(
    not all(os.environ.get(name) for name in CREDENTIALS),
    reason="netcup credentials not set",
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
