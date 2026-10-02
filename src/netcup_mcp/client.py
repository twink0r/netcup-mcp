"""Minimal HTTP client for the netcup CCP domain webservice.

The webservice is SOAP, but the same endpoint answers JSON when called
with ``?JSON``. We use the JSON form so the whole client is a plain HTTP
POST with no SOAP/XML dependency.

Session handling: every API call except ``login`` needs an
``apisessionid``. We log in lazily, cache the session id in memory, and
re-login once on an auth error.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

ENDPOINT = "https://ccp.netcup.net/run/webservice/servers/endpoint.php"
JSON_URL = ENDPOINT + "?JSON"

# Status codes in netcup's 4xxx validation range that indicate the session id is no
# longer usable rather than a bad argument. Only these trigger a re-login.
_AUTH_ERROR_CODES = {4001, 4002, 4003, 4010, 4011, 4012, 4014, 4015}


class NetcupError(RuntimeError):
    """An error reported by the netcup API."""

    def __init__(self, action: str, statuscode: int, shortmessage: str, longmessage: str) -> None:
        self.action = action
        self.statuscode = statuscode
        self.shortmessage = shortmessage
        self.longmessage = longmessage
        super().__init__(f"{action} failed ({statuscode}): {shortmessage} - {longmessage}")


class NetcupClient:
    """Thin async client for the netcup domain webservice."""

    def __init__(
        self,
        customernumber: str,
        apikey: str,
        apipassword: str,
        *,
        endpoint: str = JSON_URL,
        timeout: float = 30.0,
    ) -> None:
        self.customernumber = str(customernumber)
        self.apikey = apikey
        self.apipassword = apipassword
        self._endpoint = endpoint
        self._timeout = timeout
        self._session_id: str | None = None
        self._http: httpx.AsyncClient | None = None

    @classmethod
    def from_env(cls, **kwargs: Any) -> "NetcupClient":
        """Build a client from NETCUP_CUSTOMERNUMBER / NETCUP_APIKEY / NETCUP_APIPASSWORD."""
        missing = [
            name
            for name in ("NETCUP_CUSTOMERNUMBER", "NETCUP_APIKEY", "NETCUP_APIPASSWORD")
            if not os.environ.get(name)
        ]
        if missing:
            raise RuntimeError(
                "Missing netcup credentials: " + ", ".join(missing) + ". "
                "Get them from the netcup CCP under API / Webservice."
            )
        return cls(
            os.environ["NETCUP_CUSTOMERNUMBER"],
            os.environ["NETCUP_APIKEY"],
            os.environ["NETCUP_APIPASSWORD"],
            **kwargs,
        )

    def _auth_fields(self) -> dict[str, Any]:
        return {"customernumber": self.customernumber, "apikey": self.apikey}

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "SOAPAction": payload.get("action", "login"),
        }
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=self._timeout)
        response = await self._http.post(self._endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    async def login(self) -> str:
        """Open an API session and cache the session id."""
        payload = {
            "action": "login",
            "apipassword": self.apipassword,
            **self._auth_fields(),
        }
        data = await self._post(payload)
        self._raise_for_status("login", data)
        session_id = data.get("responsedata") or ""
        # The session can come back as a bare id or as a serialized SessionObject.
        if session_id.strip().startswith("{"):
            session_id = json.loads(session_id).get("apisessionid", "")
        self._session_id = session_id
        return session_id

    async def logout(self) -> None:
        """Close the API session."""
        if not self._session_id:
            return
        try:
            await self.call("logout")
        finally:
            self._session_id = None
            await self.aclose()

    async def call(self, action: str, _retry: bool = True, **params: Any) -> dict[str, Any]:
        """Call an API function, opening a session first if needed.

        Returns the raw ``Responsemessage`` dict from netcup.
        """
        if action == "login":
            return {
                "action": "login",
                "status": "success",
                "responsedata": await self.login(),
            }

        if not self._session_id:
            await self.login()

        # Drop unset values so the API sees only what the caller supplied.
        supplied = {k: v for k, v in params.items() if v is not None}
        payload = {
            "action": action,
            "apisessionid": self._session_id,
            **self._auth_fields(),
            **supplied,
        }
        data = await self._post(payload)

        status = str(data.get("status", "")).lower()
        if status == "error" and _retry and data.get("statuscode") in _AUTH_ERROR_CODES:
            # Session expired or was invalidated server-side: log in again and retry once.
            self._session_id = None
            await self.login()
            return await self.call(action, _retry=False, **params)

        self._raise_for_status(action, data)
        return data

    @staticmethod
    def _raise_for_status(action: str, data: dict[str, Any]) -> None:
        status = str(data.get("status", "")).lower()
        if status in ("error", "warning"):
            raise NetcupError(
                action,
                int(data.get("statuscode") or 0),
                str(data.get("shortmessage") or ""),
                str(data.get("longmessage") or ""),
            )

    @staticmethod
    def parse_responsedata(data: dict[str, Any]) -> Any:
        """Decode the ``responsedata`` field, which is a JSON string."""
        raw = data.get("responsedata")
        if not raw:
            return None
        if not isinstance(raw, str):
            return raw
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
