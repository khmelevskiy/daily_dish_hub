import logging
import re
import secrets

from fastapi import Request
from fastapi.responses import Response


logger = logging.getLogger(__name__)


async def security_middleware(request: Request, call_next):
    """Additional security middleware."""
    client_ip = request.client.host if request.client else "unknown"

    # Block dangerous HTTP methods early
    method = request.method.upper()
    if method in {"TRACE", "TRACK"}:
        # Explicitly disallow methods not used by the app
        # Prefer 405 Method Not Allowed to avoid any reflective behavior
        return Response(content="Method not allowed", status_code=405, media_type="text/plain")

    # Check User-Agent (allowlist takes precedence over blocklist)
    user_agent = request.headers.get("user-agent", "").lower()
    try:
        from app.core.config import settings

        allowed_ua = settings.allowed_user_agents_list
        blocked_ua = settings.blocked_user_agents_list
    except Exception:
        allowed_ua = []
        blocked_ua = []

    if any(token and token in user_agent for token in allowed_ua):
        pass  # explicitly allowed
    else:
        if any(token and token in user_agent for token in blocked_ua):
            logger.warning(
                "Blocked request from suspicious User-Agent: %s from IP: %s",
                user_agent,
                client_ip,
            )
            return Response(content="Access denied", status_code=403, media_type="text/plain")

    # Check URL for dangerous patterns
    path = request.url.path
    query = str(request.url.query)
    sensitive = path.startswith("/admin") or path.startswith("/auth")
    public_api = path == "/public" or path.startswith("/public/")

    # Allowlist for path prefixes (skip checks)
    try:
        allowed_prefixes = settings.security_allowed_path_prefixes_list
    except Exception:
        allowed_prefixes = []
    skip_deep_checks = any(path.startswith(pfx) for pfx in allowed_prefixes)

    # Check path (only on sensitive prefixes to reduce false positives)
    if not skip_deep_checks and sensitive:
        patterns = []
        try:
            patterns = settings.security_patterns_sensitive_list
        except Exception:
            patterns = []
        for pattern in patterns:
            if re.search(pattern, path, re.IGNORECASE):
                logger.warning(
                    "Blocked request with dangerous path pattern: %s from IP: %s",
                    pattern,
                    client_ip,
                )
                return Response(content="Access denied", status_code=403, media_type="text/plain")

    # Additional directory traversal check anywhere in the path
    if not skip_deep_checks and ".." in path:
        logger.warning(
            "Blocked request with directory traversal in path: %s from IP: %s",
            path,
            client_ip,
        )
        return Response(content="Access denied", status_code=403, media_type="text/plain")

    # Check query parameters on sensitive prefixes
    if not skip_deep_checks and sensitive and query:
        patterns = []
        try:
            patterns = settings.security_patterns_sensitive_list
        except Exception:
            patterns = []
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(
                    "Blocked request with dangerous query pattern: %s from IP: %s",
                    pattern,
                    client_ip,
                )
                return Response(content="Access denied", status_code=403, media_type="text/plain")

    # Conservative query checks for public API
    if not skip_deep_checks and public_api and query:
        patterns = []
        try:
            patterns = settings.security_patterns_api_query_list
        except Exception:
            patterns = []
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(
                    "Blocked request with dangerous API query pattern: %s from IP: %s",
                    pattern,
                    client_ip,
                )
                return Response(content="Access denied", status_code=403, media_type="text/plain")

    # Check request headers (temporarily disabled for debugging)
    # for header_name, header_value in request.headers.items():
    #     header_str = f"{header_name}: {header_value}"
    #     for pattern in DANGEROUS_PATTERNS:
    #         if re.search(pattern, header_str, re.IGNORECASE):
    #             logger.warning(f"Blocked request with dangerous header pattern: {pattern} from IP: {client_ip}")
    #             return Response(content="Access denied", status_code=403, media_type="text/plain")

    # Continue request processing
    response = await call_next(request)

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Modern defaults compatible with current UI
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
    # Content Security Policy from settings with optional nonce/strict-dynamic
    try:
        from app.core.config import settings

        nonce: str | None = None
        if settings.csp_enable_nonce:
            nonce = secrets.token_urlsafe(16)
            # expose nonce for templates if needed
            setattr(request.state, "csp_nonce", nonce)

        response.headers["Content-Security-Policy"] = settings.build_csp(nonce)
    except Exception:  # keep request resilient even if CSP generation fails
        pass

    # Optional HSTS if enabled in settings (serve via HTTPS / behind TLS proxy)
    try:
        from app.core.config import settings as _settings  # local import to avoid circulars

        if getattr(_settings, "enable_hsts", False):
            # 2 years, include subdomains, allow preload
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    except Exception:
        pass

    return response
