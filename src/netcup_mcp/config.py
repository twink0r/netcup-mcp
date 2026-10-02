"""Configuration and multi-account support.

Credentials come from a TOML config file listing named accounts. Each
account can either hold its credentials inline or point at an env file,
so secrets stay out of the config file itself::

    # netcup-mcp.toml
    default_account = "prod"

    [accounts.prod]
    env_file = "~/.config/netcup-mcp/prod.env"

    [accounts.staging]
    customernumber = "123456"
    apikey = "${NETCUP_STAGING_KEY}"    # read from the process environment
    apipassword = "${NETCUP_STAGING_PASSWORD}"

Values support ``${VAR}`` expansion against the process environment, in
both the config and the env files, so a secret never has to be written
down twice.

With no config file at all, a single implicit account is built from
``NETCUP_CUSTOMERNUMBER`` / ``NETCUP_APIKEY`` / ``NETCUP_APIPASSWORD``, so
the original single-account setup keeps working unchanged.

TOML is read with the standard library's ``tomllib``, so this adds no
dependency.
"""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_FILENAMES = ("netcup-mcp.toml", "netcup-mcp.config.toml")
CONFIG_ENV_VAR = "NETCUP_MCP_CONFIG"
DEFAULT_ACCOUNT_ENV_VAR = "NETCUP_MCP_ACCOUNT"

#: Name of the account synthesised when no config file exists.
IMPLICIT_ACCOUNT = "default"

CREDENTIAL_FIELDS = ("customernumber", "apikey", "apipassword")

_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


class ConfigError(RuntimeError):
    """The configuration is missing, unreadable, or inconsistent."""


def expand_vars(value: str) -> str:
    r"""Expand ``${VAR}`` and ``$VAR`` against the process environment.

    An unset variable expands to an empty string, matching the usual
    dotenv convention. Use ``${...}`` with a backslash for a literal
    dollar sign.
    """
    if "$" not in value:
        return value

    def replace(match: re.Match[str]) -> str:
        name = match.group(1) or match.group(2)
        return os.environ.get(name, "")

    return _VAR_PATTERN.sub(replace, value)


def parse_env_file(path: Path) -> dict[str, str]:
    """Read a ``.env``-style file into a dict.

    Understands ``KEY=value``, optional ``export`` prefixes, ``#`` comments,
    blank lines, and single or double quoted values.
    """
    if not path.is_file():
        raise ConfigError(f"env file not found: {path}")

    values: dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, sep, value = line.partition("=")
        if not sep:
            raise ConfigError(f"{path}:{lineno}: expected KEY=value, got {raw.strip()!r}")
        key = key.strip()
        if not key:
            raise ConfigError(f"{path}:{lineno}: empty key")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        else:
            # Strip trailing inline comments from unquoted values.
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        values[key] = expand_vars(value)
    return values


@dataclass(frozen=True)
class Account:
    """One netcup account: credentials plus where they came from."""

    name: str
    customernumber: str
    apikey: str
    apipassword: str
    #: Human-readable description, used by the list_accounts tool.
    description: str = ""
    #: Where the credentials were read from, for diagnostics.
    source: str = ""

    def __post_init__(self) -> None:
        missing = [f for f in CREDENTIAL_FIELDS if not getattr(self, f)]
        if missing:
            where = f" (account {self.name!r} in {self.source})" if self.source else ""
            raise ConfigError(
                "Missing credentials: "
                + ", ".join(missing)
                + where
                + ". Set them in the config file, in the account's env_file, "
                "in the process environment, or via NETCUP_CUSTOMERNUMBER / "
                "NETCUP_APIKEY / NETCUP_APIPASSWORD."
            )


@dataclass
class Config:
    """The resolved set of accounts the server can talk to."""

    accounts: dict[str, Account] = field(default_factory=dict)
    default_account: str = IMPLICIT_ACCOUNT
    #: Where the configuration came from, for diagnostics.
    path: Path | None = None

    def get(self, name: str | None = None) -> Account:
        """Look up an account, falling back to the default.

        Raises ConfigError with the known names when the account is unknown,
        so the model gets an actionable message instead of a KeyError.
        """
        key = name or self.default_account
        account = self.accounts.get(key)
        if account is None:
            known = ", ".join(sorted(self.accounts)) or "none configured"
            raise ConfigError(f"Unknown account {key!r}. Available accounts: {known}.")
        return account

    @property
    def names(self) -> list[str]:
        return sorted(self.accounts)


def _account_from_mapping(
    name: str, data: dict, config_dir: Path, config_path: Path
) -> Account:
    """Build an Account from one ``[accounts.<name>]`` table."""
    if not isinstance(data, dict):
        raise ConfigError(f"{config_path}: [accounts.{name}] must be a table")

    where = f"{config_path} -> accounts.{name}"
    sources: dict[str, str] = {}

    # 1. env_file(s), applied first so inline values win.
    env_files = data.get("env_file") or data.get("env_files") or []
    if isinstance(env_files, str):
        env_files = [env_files]
    if not isinstance(env_files, list):
        raise ConfigError(f"{where}: env_file must be a path or a list of paths")

    from_env: dict[str, str] = {}
    for raw_path in env_files:
        env_path = Path(expand_vars(str(raw_path))).expanduser()
        if not env_path.is_absolute():
            env_path = (config_dir / env_path).resolve()
        from_env.update(parse_env_file(env_path))
        sources["env_file"] = str(env_path)

    resolved: dict[str, str] = {}
    for key in CREDENTIAL_FIELDS:
        # Accept both the bare name and the NETCUP_-prefixed spelling, so an
        # env file written for the single-account setup works unchanged.
        aliases = (key, f"NETCUP_{key.upper()}")
        inline = next((data[a] for a in aliases if data.get(a) is not None), None)
        if inline is not None:
            resolved[key] = expand_vars(str(inline))
            sources[key] = "config"
            continue

        from_file = next((from_env[a] for a in aliases if from_env.get(a)), None)
        if from_file is not None:
            resolved[key] = from_file
            sources[key] = sources.get("env_file", "env_file")
            continue

        # Last resort: the process environment, so a single-account setup
        # keeps working alongside a config file.
        env_name = f"NETCUP_{key.upper()}"
        fallback = os.environ.get(env_name, "")
        resolved[key] = expand_vars(fallback)
        sources[key] = "environment" if fallback else ""

    return Account(
        name=name,
        customernumber=resolved["customernumber"],
        apikey=resolved["apikey"],
        apipassword=resolved["apipassword"],
        description=expand_vars(str(data.get("description", ""))),
        source=where,
    )


def _implicit_account() -> Account:
    """Build the single account used when no config file exists."""
    return Account(
        name=IMPLICIT_ACCOUNT,
        customernumber=expand_vars(os.environ.get("NETCUP_CUSTOMERNUMBER", "")),
        apikey=expand_vars(os.environ.get("NETCUP_APIKEY", "")),
        apipassword=expand_vars(os.environ.get("NETCUP_APIPASSWORD", "")),
        description="Implicit account from the process environment.",
        source="environment",
    )


def find_config(start: Path | None = None) -> Path | None:
    """Locate a config file: $NETCUP_MCP_CONFIG, then cwd, then XDG config."""
    explicit = os.environ.get(CONFIG_ENV_VAR)
    if explicit:
        path = Path(expand_vars(explicit)).expanduser()
        if not path.is_file():
            raise ConfigError(f"{CONFIG_ENV_VAR} points at a file that does not exist: {path}")
        return path

    candidates: list[Path] = []
    base = start or Path.cwd()
    candidates.extend(base / name for name in CONFIG_FILENAMES)

    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        candidates.append(Path(xdg) / "netcup-mcp" / "config.toml")
    else:
        candidates.append(Path.home() / ".config" / "netcup-mcp" / "config.toml")

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    return None


def load_config(
    path: str | Path | None = None, *, start: Path | None = None
) -> Config:
    """Load the configuration.

    Args:
        path: explicit config file. Missing files are an error.
        start: directory to search for a config file when ``path`` is None.
    """
    if path is not None:
        config_path = Path(path).expanduser()
        if not config_path.is_file():
            raise ConfigError(f"config file not found: {config_path}")
    else:
        config_path = find_config(start)
        if config_path is None:
            return Config(
                accounts={IMPLICIT_ACCOUNT: _implicit_account()},
                default_account=IMPLICIT_ACCOUNT,
            )

    try:
        raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{config_path}: invalid TOML: {exc}") from exc

    config_dir = config_path.parent.resolve()

    accounts_raw = raw.get("accounts", {})
    if not isinstance(accounts_raw, dict):
        raise ConfigError(f"{config_path}: [accounts] must be a table")
    if not accounts_raw:
        raise ConfigError(
            f"{config_path}: no [accounts.<name>] tables found. "
            "Add at least one, for example:\n\n"
            "[accounts.prod]\nenv_file = \"~/.config/netcup-mcp/prod.env\""
        )

    accounts: dict[str, Account] = {}
    for name, data in accounts_raw.items():
        account = _account_from_mapping(name, data, config_dir, config_path)
        accounts[name] = account

    default_account = raw.get("default_account") or raw.get("default")
    if not default_account:
        default_account = os.environ.get(DEFAULT_ACCOUNT_ENV_VAR) or next(iter(accounts))
    if default_account not in accounts:
        known = ", ".join(sorted(accounts))
        raise ConfigError(
            f"{config_path}: default_account {default_account!r} is not defined. "
            f"Available accounts: {known}."
        )

    return Config(accounts=accounts, default_account=default_account, path=config_path)
