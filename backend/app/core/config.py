from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Load env from repo root or backend/ (works regardless of CWD)
    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SchoolPOS"
    environment: str = "local"
    log_level: str = "INFO"

    # The user-provided ODBC connection string (without DB name is OK)
    sqlserver_odbc_connection: str
    sqlserver_db_name: str = "SchoolPOS"
    sqlserver_odbc_driver: str = "ODBC Driver 18 for SQL Server"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def _odbc_connect_param(self, database: str | None) -> str:
        """
        Build an ODBC connect string for pyodbc/aioodbc.
        We append/override Database and Driver to ensure consistency.
        """
        def _normalize_bool(v: str) -> str | None:
            vv = v.strip().lower()
            if vv in {"true", "1", "yes", "on"}:
                return "Yes"
            if vv in {"false", "0", "no", "off"}:
                return "No"
            return None

        base = self.sqlserver_odbc_connection.strip().rstrip(";")

        # Parse key/value pairs and normalize for ODBC Driver 18 expectations (Yes/No).
        kv: dict[str, str] = {}
        for seg in base.split(";"):
            seg = seg.strip()
            if not seg:
                continue
            if "=" not in seg:
                continue
            k, v = seg.split("=", 1)
            kv[k.strip()] = v.strip()

        # Normalize server keyword for MS ODBC Driver 18
        for k in list(kv.keys()):
            if k.strip().lower() == "data source" and "Server" not in kv and "SERVER" not in kv:
                kv["Server"] = kv.pop(k)

        # Normalize Windows auth
        for k in list(kv.keys()):
            if k.strip().lower() == "integrated security":
                nv = _normalize_bool(kv[k])
                if nv == "Yes":
                    kv["Trusted_Connection"] = "Yes"
                    kv.pop(k, None)

        if "Encrypt" in kv:
            nv = _normalize_bool(kv["Encrypt"])
            if nv:
                kv["Encrypt"] = nv
        if "TrustServerCertificate" in kv:
            nv = _normalize_bool(kv["TrustServerCertificate"])
            if nv:
                kv["TrustServerCertificate"] = nv
        if "MultipleActiveResultSets" in kv:
            nv = _normalize_bool(kv["MultipleActiveResultSets"])
            if nv:
                kv["MultipleActiveResultSets"] = nv

        # aioodbc + SQL Server often need MARS enabled when consecutive
        # statements are issued within the same session/connection context.
        kv["MultipleActiveResultSets"] = "Yes"

        kv["Driver"] = f"{{{self.sqlserver_odbc_driver}}}"
        if database:
            kv["Database"] = database

        return ";".join([f"{k}={v}" for k, v in kv.items()]) + ";"

    @property
    def sqlalchemy_database_uri(self) -> str:
        import urllib.parse

        odbc = self._odbc_connect_param(self.sqlserver_db_name)
        return "mssql+aioodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc)

    @property
    def sqlalchemy_master_uri(self) -> str:
        import urllib.parse

        odbc = self._odbc_connect_param("master")
        return "mssql+aioodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc)

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
