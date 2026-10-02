# netcup-mcp

A small MCP server for the [netcup CCP domain webservice](https://ccp.netcup.net/run/webservice/servers/endpoint.php).
It turns the netcup domain API into MCP tools so an agent can list domains,
inspect and edit DNS zones, and manage contact handles. Multiple netcup
accounts are supported through a config file.

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

Those three variables are enough for a single account. For several accounts,
use a config file instead.

## Configuration

Copy `netcup-mcp.example.toml` to `netcup-mcp.toml`:

```toml
default_account = "prod"

[accounts.prod]
description = "Production netcup account"
env_file = "~/.config/netcup-mcp/prod.env"

[accounts.staging]
description = "Staging netcup account"
customernumber = "123456"
apikey = "${NETCUP_STAGING_APIKEY}"
apipassword = "${NETCUP_STAGING_APIPASSWORD}"
```

An account can hold its credentials **inline** or point at an **env file**,
or mix both. Inline values win over `env_file`.

Both the config and the env files expand `${VAR}` against the process
environment, so a secret does not have to be written down twice.

Env files are ordinary `KEY=value` files. `export`, `#` comments, and quoted
values all work:

```sh
# ~/.config/netcup-mcp/prod.env
NETCUP_CUSTOMERNUMBER=123456
NETCUP_APIKEY=your-key
NETCUP_APIPASSWORD="your-password"
```

Relative `env_file` paths resolve against the config file's directory.

The config file is found in this order:

1. `--config PATH`
2. `$NETCUP_MCP_CONFIG`
3. `./netcup-mcp.toml` in the working directory
4. `$XDG_CONFIG_HOME/netcup-mcp/config.toml`, else `~/.config/netcup-mcp/config.toml`

If no config file is found, the server falls back to the three
`NETCUP_*` environment variables as a single account named `default`.

## Multiple accounts

Every tool takes an optional `account` argument. Leave it out to use
`default_account`. Each account gets its own API session, so switching
accounts never reuses the wrong session.

The model should call `list_accounts` to discover the configured names
rather than guessing one.

```sh
netcup-mcp --list-accounts                  # show what is configured
netcup-mcp --account staging                # override the default for this run
```

## Command line

```text
netcup-mcp [--config PATH] [--account NAME] [--list-accounts]
```

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
      "args": ["--directory", "/Users/akarl/Projects/netcup-mcp", "run", "netcup-mcp", "--config", "/Users/akarl/Projects/netcup-mcp/netcup-mcp.toml"],
      "env": {}
    }
  }
}
```

## Prime Agent

The server is registered as a stdio MCP server in Prime Agent:

```sh
prime-agent mcp add netcup --cwd /Users/akarl/Projects/netcup-mcp -- \
  uv run netcup-mcp --config /Users/akarl/Projects/netcup-mcp/netcup-mcp.toml
```

That writes an `mcpServers.netcup` entry to `~/.prime/agent/settings.json`.
Remove it again with `prime-agent mcp remove netcup`.

Call the tools from the agent's Python kernel through the pre-imported
`mcp` module. Note that inside Prime Agent the name `mcp` is already the
MCP **SDK**; the Prime Agent service module is `rlm.mcp`:

```python
from rlm import mcp

tools = await mcp.list_tools("netcup")
result = await mcp.call_tool("netcup", "list_accounts", {})
result = await mcp.call_tool("netcup", "info_domain",
                             {"domainname": "example.com", "account": "prod"})
```

`mcp.reload()` re-reads the settings and closes open connections, which
picks up config changes without restarting the session.

### One gotcha: environment variables do not cross the boundary

Prime Agent passes a stdio child only `HOME`, `PATH`, `TMPDIR`, `TEMP`, `TMP`
and any explicit `env` references. **`NETCUP_CUSTOMERNUMBER`,
`NETCUP_APIKEY` and `NETCUP_APIPASSWORD` are not passed through**, so the
environment fallback does not work when the server runs under Prime Agent.
Give each account an `env_file` (or inline values) instead.

A missing `--config` file is only a warning: the server falls back to config
discovery and then to the environment. Set `NETCUP_MCP_CONFIG_REQUIRED=1` to
make it a hard error.

## Tools

Read-only:

- `listall_domains`, `listall_handle`
- `info_domain`, `info_handle`, `info_dns_zone`, `info_dns_records`
- `price_topleveldomain`, `poll`, `get_authcode_domain`

Write:

- `update_dns_records`, `update_dns_zone`, `update_domain`
- `create_handle`, `update_handle`, `delete_handle`
- `change_owner_domain`, `cancel_domain`, `transfer_domain`, `create_domain`

Plus `list_accounts`, which shows the configured account names and which one
is the default.

`login` and `logout` are handled by the server itself. It opens a session on
first use, caches it per account, and re-authenticates once if the session
expires, so credentials never reach the model.

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
