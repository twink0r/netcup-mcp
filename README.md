# netcup-mcp

A small MCP server for the [netcup CCP domain webservice](https://ccp.netcup.net/run/webservice/servers/endpoint.php).
It turns the netcup domain API into MCP tools so an agent can list domains,
inspect and edit DNS zones, and manage contact handles.

The API is SOAP, but the same endpoint answers plain JSON when called with
`?JSON`, so the server needs no XML stack. Two runtime dependencies:
[`mcp`](https://pypi.org/project/mcp/) and `httpx`.

## Setup

```sh
uv sync
```

You need three values from the netcup CCP, under **API / Webservice**:

| Variable | Meaning |
| --- | --- |
| `NETCUP_CUSTOMERNUMBER` | Your customer number |
| `NETCUP_APIKEY` | API key from the CCP |
| `NETCUP_APIPASSWORD` | API password from the CCP |

## Run

```sh
uv run netcup-mcp
```

The server speaks MCP over stdio.

## MCP client config

```json
{
  "mcpServers": {
    "netcup": {
      "command": "uv",
      "args": ["--directory", "/Users/akarl/Projects/netcup-mcp", "run", "netcup-mcp"],
      "env": {
        "NETCUP_CUSTOMERNUMBER": "123456",
        "NETCUP_APIKEY": "your-key",
        "NETCUP_APIPASSWORD": "your-password"
      }
    }
  }
}
```

## Tools

Read-only:

- `listall_domains`, `listall_handle`
- `info_domain`, `info_handle`, `info_dns_zone`, `info_dns_records`
- `price_topleveldomain`, `poll`, `get_authcode_domain`

Write:

- `update_dns_records`, `update_dns_zone`, `update_domain`
- `create_handle`, `update_handle`, `delete_handle`
- `change_owner_domain`, `cancel_domain`, `transfer_domain`, `create_domain`

`login` and `logout` are handled by the server itself. It opens a session on
first use, caches it, and re-authenticates once if the session expires, so
credentials never reach the model.

## Editing DNS records

`update_dns_records` replaces the whole record set. Read the current records
with `info_dns_records` first and pass back everything you want to keep.
Use `{"hostname": "@"}` for the zone apex, and set `deleterecord` to drop a
record.

## Tests

```sh
uv run pytest            # unit tests, no network
uv run pytest -m live    # hits the real API, needs credentials in .env
```

## Notes

- `updateDnsRecords` can skip DNSSEC records when `keepdnssecrecords` is set.
- DNSSEC changes can only be made once every 24 hours.
- Several tools need a reseller account. Those return a clear API error on
  a normal customer account.
