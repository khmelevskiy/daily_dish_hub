import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)

    admin_username: str  # required
    admin_password: str  # required

    bot_token: str = ""
    site_name: str = "Canteen Menu"
    site_description: str = "Fresh and tasty dishes every day"

    # Currency settings (public-safe)
    currency_code: str = "GEL"  # ISO 4217 code
    currency_symbol: str = "₾"  # display symbol
    currency_locale: str = "en-GE"  # locale for formatting prices

    # JWT settings
    secret_key: str  # required
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    jwt_issuer: str | None = None
    jwt_audience: str | None = None

    # Rate limiting settings
    rate_limit_public_requests: int = 1000  # requests per minute for public APIs
    rate_limit_admin_requests: int = 2000  # requests per minute for admin APIs
    rate_limit_auth_attempts: int = 50  # login attempts per minute
    rate_limit_window: int = 60  # window in seconds
    # Soft limit for public images (GET /images/{id})
    rate_limit_public_images_requests: int = 10000  # per minute for image downloads
    # Rate limit backend configuration
    rate_limit_backend: str = "redis"  # memory|redis
    rate_limit_redis_url: str | None = "redis://redis:6379/0"
    # Optional Redis password (if not embedded into URL); if set and URL has no auth part, the app injects it
    redis_password: str | None = None

    # Database settings
    database_url: str | None = None
    postgres_db: str  # required
    postgres_user: str  # required
    postgres_password: str  # required
    postgres_host: str  # required
    postgres_port: int = 5432
    postgres_host_external: str | None = None
    postgres_port_external: int | None = None

    # Upload limits
    max_upload_size_mb: int = 40  # from env MAX_UPLOAD_SIZE_MB

    # Trusted hosts and CORS
    trusted_hosts: str | None = None  # comma-separated list, e.g. "example.com,.example.com,localhost"
    # Proxy/IP headers handling
    enable_proxy_headers: bool = False  # when true, trust X-Forwarded-For/X-Real-IP
    trusted_proxies: str | None = None  # comma-separated list of proxy IPs/CIDRs
    # Deployment environment indicator (read-only; use ENV or ENVIRONMENT)
    # Values: development (default), staging, production
    # We intentionally do not expose this publicly via /public/settings
    # Prefer ENV to align with common platform envs
    # Note: we do not fail if ENV is unset — default is development
    # This field is not meant to be set from .env programmatically
    env: str = "development"

    cors_allow_origins: str | None = None  # comma-separated list of origins; empty disables CORS
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    cors_allow_headers: str = "Authorization,Content-Type"

    # Content Security Policy (CSP)
    # Base directives kept conservative; toggles allow opt-in hardening without breaking current UI
    csp_enable_nonce: bool = True  # enable nonce by default for stronger CSP
    csp_enable_strict_dynamic: bool = False  # when true, add 'strict-dynamic' to script-src (only with nonce)

    # Documentation exposure control (disable FastAPI docs in production)
    disable_docs: bool = True  # when true, hide /docs, /redoc, /openapi.json

    # Security middleware configuration
    # Blocked/allowed User-Agents (comma-separated, case-insensitive substrings)
    security_blocked_user_agents: str | None = "sqlmap,nikto,nmap,scanner,bot,crawler,spider"
    security_allowed_user_agents: str | None = None
    # Patterns for sensitive prefixes (/admin, /auth) applied to path and query (semicolon-separated regexes)
    security_patterns_sensitive: str | None = None
    # Patterns for public API query (/public/*), conservative subset (semicolon-separated regexes)
    security_patterns_api_query: str | None = None
    # Optional allowlist of path prefixes to skip security scanning (comma-separated)
    # Defaults to public/static paths to reduce false positives
    security_allowed_path_prefixes: str | None = "/static,/public/static,/images,/docs,/redoc,/openapi"
    # HSTS header toggle (set true only when served via HTTPS / TLS proxy)
    enable_hsts: bool = False

    @property
    def trusted_hosts_list(self) -> list[str]:
        if not self.trusted_hosts:
            # Default to allow all in dev unless explicitly restricted in env
            return ["*"]

        return [h.strip() for h in self.trusted_hosts.split(",") if h.strip()]

    @property
    def cors_allow_origins_list(self) -> list[str]:
        if not self.cors_allow_origins:
            return []

        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def cors_allow_methods_list(self) -> list[str]:
        return [m.strip() for m in (self.cors_allow_methods or "").split(",") if m.strip()]

    @property
    def cors_allow_headers_list(self) -> list[str]:
        return [h.strip() for h in (self.cors_allow_headers or "").split(",") if h.strip()]

    @property
    def trusted_proxies_list(self) -> list[str]:
        raw = self.trusted_proxies or ""

        return [x.strip() for x in raw.split(",") if x.strip()]

    # --- CSP helpers ---
    def build_csp(self, nonce: str | None = None) -> str:
        """Build a strict but compatible CSP string.

        - default-src 'self'
        - script-src 'self' [nonce] ['strict-dynamic' if enabled]
        - style-src 'self'
        - img-src 'self' data:
        - connect-src 'self'
        - object-src 'none'
        - base-uri 'self'
        - frame-src 'none'
        - frame-ancestors 'none'
        """
        default_src = ["'self'"]
        script_src = ["'self'"]
        if self.csp_enable_nonce and nonce:
            script_src.append(f"'nonce-{nonce}'")
            if self.csp_enable_strict_dynamic:
                script_src.append("'strict-dynamic'")
        style_src = ["'self'"]
        img_src = ["'self'", "data:"]
        connect_src = ["'self'"]
        object_src = ["'none'"]
        base_uri = ["'self'"]
        frame_src = ["'none'"]
        frame_ancestors = ["'none'"]

        directives = {
            "default-src": default_src,
            "script-src": script_src,
            "style-src": style_src,
            "img-src": img_src,
            "connect-src": connect_src,
            "object-src": object_src,
            "base-uri": base_uri,
            "frame-src": frame_src,
            "frame-ancestors": frame_ancestors,
        }

        return "; ".join(f"{k} {' '.join(v)}" for k, v in directives.items())

    # --- Security middleware helpers ---
    @property
    def blocked_user_agents_list(self) -> list[str]:
        raw = self.security_blocked_user_agents or ""

        return [x.strip().lower() for x in raw.split(",") if x.strip()]

    @property
    def allowed_user_agents_list(self) -> list[str]:
        raw = self.security_allowed_user_agents or ""

        return [x.strip().lower() for x in raw.split(",") if x.strip()]

    @property
    def security_patterns_sensitive_list(self) -> list[str]:
        # Defaults mirror previous hardcoded patterns
        default = [
            r"\.\./",
            r"\.\.\\",
            r"\bunion\s+select\b",
            r"\bdrop\s+table\b",
            r"\bor\s+1\s*=\s*1\b",
            r"\bexec\s*\(",
            r"\bsystem\s*\(",
            r"\brm\s+\-\w*\b",
            r"\b(cat|ls|bash|sh|nc)\b\s",
            r"`[^`]+`",
            r"\$\([^)]*\)",
            r"\|\s*(cat|ls|bash|sh|nc)\b",
            r"\\\\windows\\\\system32\\\\config\\\\sam$",
            r"/etc/passwd",
            r"/etc/shadow",
        ]
        if self.security_patterns_sensitive:
            return [p.strip() for p in self.security_patterns_sensitive.split(";") if p.strip()]

        return default

    @property
    def security_patterns_api_query_list(self) -> list[str]:
        # Conservative subset for public API query parameters
        default = [
            r"\bunion\s+select\b",
            r"\bdrop\s+table\b",
            r"\bor\s+1\s*=\s*1\b",
            r"\bexec\s*\(",
            r"\bsystem\s*\(",
            r"`[^`]+`",
            r"\$\([^)]*\)",
            r"\|\s*(cat|ls|bash|sh|nc)\b",
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
        ]
        if self.security_patterns_api_query:
            return [p.strip() for p in self.security_patterns_api_query.split(";") if p.strip()]

        return default

    @property
    def security_allowed_path_prefixes_list(self) -> list[str]:
        raw = self.security_allowed_path_prefixes or ""

        return [x.strip() for x in raw.split(",") if x.strip()]

    def validate(self) -> None:
        """Basic runtime config validation. Raises if critical settings are invalid."""
        key = (self.secret_key or "").strip()
        if not key:
            raise RuntimeError("SECRET_KEY is not set. Define SECRET_KEY in your environment/.env before starting.")
        # Enforce minimum length and reject common placeholders
        if len(key) < 32:
            raise RuntimeError("SECRET_KEY is too short. Use a strong random value with at least 32 characters.")
        lowered = key.lower()
        placeholder_tokens = (
            "your-secret",
            "your_secret",
            "secret-key",
            "change-this",
            "change_me",
            "placeholder",
        )
        if any(t in lowered for t in placeholder_tokens):
            raise RuntimeError("SECRET_KEY looks like a placeholder. Set a real strong random key (32+ chars).")

        # In production, TrustedHostMiddleware must not be wide-open
        env_value = os.getenv("ENV") or os.getenv("ENVIRONMENT") or "development"
        env_value = str(env_value).strip().lower()
        self.env = env_value
        if env_value in {"prod", "production"}:
            hosts = self.trusted_hosts_list
            # Disallow wildcard or empty (which maps to ["*"] by default)
            if not hosts or any(h == "*" for h in hosts):
                raise RuntimeError(
                    "In production (ENV=production), TRUSTED_HOSTS must be explicitly set "
                    "to allowed hostnames; wildcard '*' is forbidden."
                )


settings = Settings()  # type: ignore # required loaded from environment
