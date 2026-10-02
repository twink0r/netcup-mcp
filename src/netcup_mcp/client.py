"""HTTP client for the netcup CCP domain webservice.

The webservice is SOAP, but it also accepts JSON when the endpoint is called
with ``?JSON``. The JSON form is what this client uses, so no XML stack is
needed.

Two details the endpoint is fussy about, both verified against the live API:

* The payload must be ``{"action": <name>, "param": {...}}``. Credentials sent
  as a flat object return ``4013 Invalid entry for field apikey`` no matter
  whether they are correct.
* ``customernumber`` must be a JSON number, not a string, and
  ``clientrequestid`` must always be present.

Session handling: every API call except ``login`` needs an
``apisessionid``. We log in lazily, cache the session id per client, and
re-login once on a session error.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from .config import IMPLICIT_ACCOUNT, Config

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


def _as_json_value(value: Any) -> Any:
    """Coerce a value into what the netcup JSON endpoint expects.

    ``customernumber`` and handle ids are JSON numbers on the wire; sending
    them as strings makes netcup reject the request.
    """
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.lstrip("-").isdigit():
            return int(text)
    if isinstance(value, dict):
        return {k: _as_json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_as_json_value(v) for v in value]
    return value


class NetcupClient:
    """Thin async client for the netcup domain webservice."""

    def __init__(
        self,
        customernumber: str,
        apikey: str,
        apipassword: str,
        *,
        name: str = IMPLICIT_ACCOUNT,
        endpoint: str = JSON_URL,
        timeout: float = 30.0,
    ) -> None:
        self.name = name
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
        return {"customernumber": int(self.customernumber), "apikey": self.apikey}

    async def _post(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        """Send one JSON request and return the decoded Responsemessage.

        netcup requires the parameters under a ``param`` key; a flat object is
        rejected with ``4013 Invalid entry for field apikey`` even when the
        credentials are correct.
        """
        # Drop unset values, always send clientrequestid, and coerce numeric fields.
        body: dict[str, Any] = {"clientrequestid": ""}
        for key, value in params.items():
            if value is not None:
                body[key] = _as_json_value(value)

        payload = {"action": action, "param": body}
        headers = {
            "Content-Type": "application/json",
            "SOAPAction": action,
        }
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=self._timeout)
        response = await self._http.post(self._endpoint, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise NetcupError(action, 0, "Malformed API response", str(data)[:200])
        return data

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    async def login(self) -> str:
        """Open an API session and cache the session id."""
        params = {"apipassword": self.apipassword, **self._auth_fields()}
        data = await self._post("login", params)
        self._raise_for_status("login", data)

        responsedata = data.get("responsedata") or {}
        if isinstance(responsedata, dict):
            session_id = str(responsedata.get("apisessionid") or "")
        else:
            session_id = str(responsedata)
        if not session_id:
            raise NetcupError("login", 0, "No session id in response", str(responsedata))

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
                "responsedata": {"apisessionid": await self.login()},
            }

        if not self._session_id:
            await self.login()

        # Drop unset values so the API sees only what the caller supplied.
        supplied = {k: v for k, v in params.items() if v is not None}
        request_params = {
            "apisessionid": self._session_id,
            **self._auth_fields(),
            **supplied,
        }
        data = await self._post(action, request_params)

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


class AccountRegistry:
    """Holds one lazily-created :class:`NetcupClient` per configured account.

    Each account gets its own client, and therefore its own API session, so
    switching accounts never reuses the wrong session id.
    """

    def __init__(self, config: Config, **client_kwargs: Any) -> None:
        self._config = config
        self._client_kwargs = client_kwargs
        self._clients: dict[str, NetcupClient] = {}

    @property
    def config(self) -> Config:
        return self._config

    @property
    def names(self) -> list[str]:
        return self._config.names

    def client(self, account: str | None = None) -> NetcupClient:
        """Return the client for an account, creating it on first use.

        Raises ConfigError if the account is not configured.
        """
        resolved = self._config.get(account)
        existing = self._clients.get(resolved.name)
        if existing is not None:
            return existing

        client = NetcupClient(
            resolved.customernumber,
            resolved.apikey,
            resolved.apipassword,
            name=resolved.name,
            **self._client_kwargs,
        )
        self._clients[resolved.name] = client
        return client

    async def aclose(self) -> None:
        """Close every client, ending the API sessions."""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()

    def describe(self) -> list[dict[str, Any]]:
        """Summarise the configured accounts, without secrets."""
        return [
            {
                "name": account.name,
                "default": account.name == self._config.default_account,
                "description": account.description,
                "customernumber": account.customernumber,
            }
            for account in (
                self._config.accounts[name] for name in self._config.names
            )
        ]
