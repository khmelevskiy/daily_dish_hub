import asyncio
import ipaddress
import logging
import math
import time
import uuid
from collections import defaultdict, deque
from urllib.parse import quote, urlparse, urlunparse

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings


logger = logging.getLogger(__name__)

# Optional Redis backend
_backend = (getattr(settings, "rate_limit_backend", "redis") or "redis").lower()
_redis_url = getattr(settings, "rate_limit_redis_url", None) or "redis://redis:6379/0"

# Emit at most one warning when proxy headers are enabled without trusted proxies.
_missing_trusted_proxy_warning_emitted = False


def _inject_password_if_needed(url: str, password: str | None) -> str:
    if not password:
        return url
    try:
        parsed = urlparse(url)
        # If username/password already present, keep as-is
        if parsed.password:
            return url
        # Build netloc with password only (no username)
        netloc = parsed.netloc
        if "@" in netloc:
            return url  # unexpected, but don't touch

        encoded_password = quote(password, safe="")
        username = parsed.username or ""
        hostname_raw = parsed.hostname or ""
        if not hostname_raw:
            return url
        if ":" in hostname_raw and not hostname_raw.startswith("["):
            host_display = f"[{hostname_raw}]"
        else:
            host_display = hostname_raw
        port = f":{parsed.port}" if parsed.port else ""

        if username:
            credentials = f"{username}:{encoded_password}"
        else:
            credentials = f":{encoded_password}"

        new_netloc = f"{credentials}@{host_display}{port}"

        return urlunparse(parsed._replace(netloc=new_netloc))
    except Exception:
        return url


_redis = None
RedisError = Exception
if _backend == "redis":
    try:
        import redis.asyncio as redis  # type: ignore
        from redis.exceptions import RedisError as _RedisError  # type: ignore

        _redis = redis.from_url(
            _inject_password_if_needed(url=_redis_url, password=getattr(settings, "redis_password", None)),
            encoding="utf-8",
            decode_responses=True,
        )
        RedisError = _RedisError
        logger.info("Rate limiter: using Redis backend")
    except Exception as e:  # pragma: no cover - optional path
        logger.warning(
            "Rate limiter: Redis backend requested but unavailable (%s). Falling back to memory.",
            e,
        )
        _backend = "memory"


class _BaseLimiter:
    async def is_allowed(
        self, client_ip: str, limit: int, window: int
    ) -> tuple[bool, int, int]:  # pragma: no cover - interface
        raise NotImplementedError


class RateLimiter(_BaseLimiter):
    def __init__(self) -> None:
        # Per-key buckets; each bucket is a deque of timestamps in seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = asyncio.Lock()
        # Next time when GC sweep may run
        self._gc_next_ts: float = 0.0

    def _sweep_gc(self, now: float, window: int) -> None:
        """Occasional sweep to drop stale buckets to keep memory bounded.

        Strategy: for each key, pop expired timestamps; if bucket empty -> delete key.
        Run infrequently (based on _gc_next_ts) to minimize overhead.
        """
        keys = list(self.requests.keys())
        for key in keys:
            dq = self.requests.get(key)
            if dq is None:
                continue
            # Drop expired items
            while dq and (now - dq[0]) >= window:
                dq.popleft()
            if not dq:
                # Free empty buckets
                self.requests.pop(key, None)

    async def is_allowed(self, client_ip: str, limit: int, window: int) -> tuple[bool, int, int]:
        """Return (allowed, remaining, reset_seconds).

        - remaining: requests left in current window
        - reset_seconds: seconds until this key's window naturally frees one slot
        """
        async with self.lock:
            now = time.time()

            # Run GC occasionally (at most once per max(60s, window))
            if now >= self._gc_next_ts:
                self._sweep_gc(now=now, window=window)
                self._gc_next_ts = now + max(60.0, float(window))

            dq = self.requests[client_ip]

            # Evict expired timestamps from the left (oldest first)
            while dq and (now - dq[0]) >= window:
                dq.popleft()

            # Compute reset based on current oldest item in bucket
            if dq:
                oldest = dq[0]
                reset_seconds = max(0, int(window - (now - oldest)))
            else:
                reset_seconds = window

            if len(dq) >= limit:
                # Not allowed; keep bucket as-is
                return False, 0, reset_seconds

            # Allow and record current request
            dq.append(now)
            remaining = max(0, limit - len(dq))

            # Recompute reset based on (possibly new) oldest
            oldest = dq[0]
            reset_seconds = max(0, int(window - (now - oldest)))

            return True, remaining, reset_seconds


class RedisRateLimiter(_BaseLimiter):
    """Redis-based sliding-window limiter using a sorted set per key.

    Key structure: {prefix}:{client_ip}
    Score/value: request timestamps in milliseconds
    """

    def __init__(self, client, prefix: str, *, retry_backoff: float = 30.0) -> None:
        self.client = client
        self.prefix = prefix
        self._fallback = RateLimiter()
        self._retry_backoff = retry_backoff
        self._retry_until = 0.0
        self._warned = False

    def _key(self, client_ip: str) -> str:
        return f"{self.prefix}:{client_ip}"

    async def _fallback_call(self, client_ip: str, limit: int, window: int) -> tuple[bool, int, int]:
        return await self._fallback.is_allowed(client_ip=client_ip, limit=limit, window=window)

    async def is_allowed(self, client_ip: str, limit: int, window: int) -> tuple[bool, int, int]:
        if not self.client:
            return await self._fallback_call(client_ip, limit, window)

        now_monotonic = time.monotonic()
        if now_monotonic < self._retry_until:
            return await self._fallback_call(client_ip, limit, window)

        key = self._key(client_ip)
        now_ms = int(time.time() * 1000)
        window_ms = int(window * 1000)

        try:
            # Pipeline for atomic-ish operations (non-Lua acceptable for our case)
            p = self.client.pipeline()
            # Drop old entries outside window
            p.zremrangebyscore(key, 0, now_ms - window_ms)
            # Count current
            p.zcard(key)
            res = await p.execute()
            count = int(res[-1]) if res else 0

            if count >= limit:
                # Get oldest to compute reset
                oldest = await self.client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_score = int(oldest[0][1])
                    reset_sec = max(0, math.ceil((window_ms - (now_ms - oldest_score)) / 1000))
                else:
                    reset_sec = window

                return False, 0, reset_sec

            # Allow and record
            member = f"{now_ms}-{uuid.uuid4().hex}"
            p = self.client.pipeline()
            p.zadd(key, {member: now_ms})
            p.expire(key, window)  # keep keys bounded in time
            p.zcard(key)
            p.zrange(key, 0, 0, withscores=True)
            zres = await p.execute()
            new_count = int(zres[2]) if len(zres) >= 3 else (count + 1)
            oldest = zres[3] if len(zres) >= 4 else []
            if oldest:
                oldest_score = int(oldest[0][1])
                reset_sec = max(0, math.ceil((window_ms - (now_ms - oldest_score)) / 1000))
            else:
                reset_sec = window
            remaining = max(0, limit - new_count)

            # Redis succeeded -> reset fallback window & warning flag
            self._retry_until = 0.0
            self._warned = False

            return True, remaining, reset_sec
        except (RedisError, asyncio.TimeoutError, OSError) as exc:  # pragma: no cover - redis optional
            if not self._warned:
                logger.warning(
                    "Rate limiter: Redis backend unavailable (%s). Falling back to in-memory for %.0f seconds.",
                    exc,
                    self._retry_backoff,
                )
                self._warned = True
            self._retry_until = time.monotonic() + self._retry_backoff

            return await self._fallback_call(client_ip, limit, window)


# Create rate limiter instances for different request types (memory or redis)
if _backend == "redis" and _redis is not None:
    public_limiter = RedisRateLimiter(_redis, "rl:public")
    admin_limiter = RedisRateLimiter(_redis, "rl:admin")
    auth_limiter = RedisRateLimiter(_redis, "rl:auth")
    images_limiter = RedisRateLimiter(_redis, "rl:images")
else:
    if _backend != "memory":
        logger.warning("Unknown RATE_LIMIT_BACKEND=%s, using in-memory.", _backend)
    public_limiter = RateLimiter()
    admin_limiter = RateLimiter()
    auth_limiter = RateLimiter()
    images_limiter = RateLimiter()


def _parse_ip(ip_str: str) -> str | None:
    try:
        # Normalize IP (validate IPv4/IPv6)
        ipaddress.ip_address(ip_str)
        return ip_str
    except Exception:
        return None


def _client_ip_from_proxy_headers(request: Request, peer_ip: str) -> str | None:
    """Resolve client IP from proxy headers when enabled and (optionally) the peer is trusted.
    - Prefer X-Real-IP, then left-most value from X-Forwarded-For.
    - Only trust when settings.enable_proxy_headers is True.
    - If trusted_proxies_list is non-empty, require peer_ip to match one of them (IP or CIDR).
    Returns a validated IP string or None if not applicable.
    """
    if not settings.enable_proxy_headers:
        return None

    # If a trusted proxy list is configured, ensure peer_ip matches one entry
    trusted = settings.trusted_proxies_list
    if not trusted:
        global _missing_trusted_proxy_warning_emitted
        if not _missing_trusted_proxy_warning_emitted:
            logger.warning(
                "ENABLE_PROXY_HEADERS is true but TRUSTED_PROXIES is empty; ignoring forwarded client IP headers."
            )
            _missing_trusted_proxy_warning_emitted = True
        return None
    if trusted:
        peer_ok = False
        try:
            peer = ipaddress.ip_address(peer_ip)
        except Exception:
            peer = None
        if peer is not None:
            for entry in trusted:
                try:
                    net = ipaddress.ip_network(entry, strict=False)
                    if peer in net:
                        peer_ok = True
                        break
                except Exception:
                    # Not a network; try exact IP string match
                    if peer_ip == entry:
                        peer_ok = True
                        break
        if not peer_ok:
            return None

    headers = request.headers
    # Prefer X-Real-IP
    x_real_ip = headers.get("X-Real-IP") or headers.get("x-real-ip")
    if x_real_ip:
        ip = _parse_ip(ip_str=x_real_ip.strip())
        if ip:
            return ip
    # Fallback to X-Forwarded-For (left-most is original client)
    xff = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
    if xff:
        # Take first non-empty token
        first = xff.split(",")[0].strip()
        ip = _parse_ip(ip_str=first)
        if ip:
            return ip
    return None


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    peer_ip = request.client.host if request.client else "unknown"
    forwarded_ip = _client_ip_from_proxy_headers(request=request, peer_ip=peer_ip)
    client_ip = forwarded_ip or peer_ip
    path = request.url.path

    # Determine request type and corresponding limits
    if path.startswith("/admin/"):
        # Admin APIs - strict limits
        limiter = admin_limiter
        limit = settings.rate_limit_admin_requests
        window = settings.rate_limit_window
        error_message = "Too many requests to admin APIs. Please try again later."
    elif path.startswith("/auth/"):
        limiter = auth_limiter
        limit = settings.rate_limit_auth_attempts
        window = settings.rate_limit_window
        error_message = (
            "Too many login attempts. Please try again later."
            if path.startswith("/auth/login")
            else "Too many auth requests. Please try again later."
        )
    elif path.startswith("/public/"):
        # Public APIs - moderate limits
        limiter = public_limiter
        limit = settings.rate_limit_public_requests
        window = settings.rate_limit_window
        error_message = "Too many requests to public APIs. Please try again later."
    elif request.method.upper() == "GET" and path.startswith("/images/"):
        # Public images - soft limit to mitigate mass download
        limiter = images_limiter
        limit = settings.rate_limit_public_images_requests
        window = settings.rate_limit_window
        error_message = "Too many image requests. Please slow down and try again."
    else:
        # Static files and others - no limits
        return await call_next(request)

    # Check limit
    allowed, remaining, reset_sec = await limiter.is_allowed(client_ip=client_ip, limit=limit, window=window)
    if not allowed:
        logger.warning("Rate limit exceeded for IP %s on path %s", client_ip, path)
        # Build unified headers for 429
        headers = {
            "Retry-After": str(reset_sec),
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Window": str(window),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_sec),
        }

        # Unified JSON body including rate limit meta
        body = {
            "detail": error_message,
            # retry_after should reflect time to reset, not full window
            "retry_after": reset_sec,
            "rate_limit": {
                "limit": limit,
                "window": window,
                "remaining": remaining,
                "reset": reset_sec,
            },
        }

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=body,
            headers=headers,
        )

    # Continue processing the request
    response = await call_next(request)

    # Add headers with rate limit info (unified for limited paths)
    if (
        path.startswith("/admin/")
        or path.startswith("/auth/login")
        or path.startswith("/public/")
        or (request.method.upper() == "GET" and path.startswith("/images/"))
    ):
        response.headers["X-RateLimit-Limit"] = str(limit)
        # Window is expressed in seconds
        response.headers["X-RateLimit-Window"] = str(window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        # Reset/Retry-After indicate seconds until a slot frees in current window
        response.headers["X-RateLimit-Reset"] = str(reset_sec)

    return response
