# 🔒 Security

## Important security settings

### 1. Mandatory changes before deployment

**You must manually set these values before deploying:**

#### Trusted hosts (production only)

In production (`ENV=production`), you must configure explicit trusted hostnames. Wildcard `*` is forbidden and the app will refuse to start otherwise.

```bash
TRUSTED_HOSTS=example.com,.example.com
```

#### JWT Secret Key

```bash
# Generate a strong secret key
SECRET_KEY=your-very-long-and-random-secret-key-here
```

#### Database password

```bash
POSTGRES_PASSWORD=your-very-strong-database-password
```

#### Admin credentials

```bash
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-very-strong-admin-password
```

#### Telegram Bot Token

```bash
BOT_TOKEN=your-telegram-bot-token
```

### 2. Generating strong secrets

**You must manually generate and set these secrets:**

#### For SECRET_KEY (at least 32 chars)

```bash
# Linux/Mac
openssl rand -base64 32

# Or using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### For passwords (at least 12 chars)

```bash
# Linux/Mac
openssl rand -base64 16

# Or using Python
python3 -c "import secrets; import string; print(''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(16)))"
```

### 3. Additional measures

#### Admin access restrictions

- Use VPN or IP whitelist for the admin panel
- Enable HTTPS in production
- Rotate passwords regularly

#### Monitoring

- Enable centralized logging
- Set up alerts for suspicious activity
- Review logs regularly
- Healthcheck available at `/health` (200 + version)

#### Headers and CSP

- Security headers enabled (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`).
- Content-Security-Policy (tightened):
  - `default-src 'self'; script-src 'self' [nonce]; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-src 'none'; frame-ancestors 'none'`.
- No inline scripts are used; static assets are served from `/static`.
- Optional HSTS (`Strict-Transport-Security`) can be enabled via `ENABLE_HSTS=true` when serving over HTTPS.

#### Updates

- Update dependencies regularly
- Track security advisories
- Use `uv audit` to scan dependencies

#### Do not commit secrets

- Never commit `.env` or any secret files to version control.
- Keep `.env` out of PRs; use `.env.example` for documentation only.
- Use pre-commit hooks with `detect-secrets`/`gitleaks` to scan diffs.

#### Proxy / Real client IP

- If deployed behind a proxy/load balancer, enable proxy headers handling:
  - Set `ENABLE_PROXY_HEADERS=true` to pass `--proxy-headers` to uvicorn.
  - Configure your proxy to set `X-Forwarded-For` / `X-Real-IP`.
  - Set `TRUSTED_PROXIES` to the proxy IPs/CIDRs; forwarded headers are ignored when this list is empty.
  - Optionally set `FORWARDED_ALLOW_IPS` to the proxy IPs/CIDRs (used by uvicorn itself).
- Restrict public hosts via `TRUSTED_HOSTS` and configure CORS via `CORS_*` env vars.
- Configure `TRUSTED_PROXIES` with IP/CIDR ranges. Only peers from this list are allowed to set client IP.

#### API docs exposure

- In production or when `DISABLE_DOCS=true`, OpenAPI schema and docs endpoints are disabled (`/openapi.json`, `/docs`, `/redoc`). Keep docs off in internet‑facing environments.

#### Rate limiting

- Limits are applied before authentication (per IP) by design, to protect endpoints regardless of token validity.
- Backend: `memory` (single-process) or `redis` (for horizontal scaling). For HPA, prefer Redis (enabled by default in docker-compose).

#### Auth token storage (Frontend)

- The admin UI uses a Bearer token stored in `localStorage` and sent via the `Authorization` header.
- CSRF is not a concern for Bearer headers (unlike cookies). Cookies would require additional CSRF mitigations and strict `SameSite` handling.
- XSS risk is mitigated by a strict CSP (no inline scripts, `object-src 'none'`, `base-uri 'self'`, `frame-src 'none'`) and by keeping the frontend free of unsafe dynamic script injection.

#### Image uploads

- Limit upload size via `MAX_UPLOAD_SIZE_MB` (default 40MB).
- Allowed formats by default: JPEG, PNG, WEBP, AVIF, TIFF. HEIF/HEIC require an additional plugin (e.g., pillow-heif).

#### Incident response: secrets rotation

When a secret is suspected to be leaked:

- Rotate `SECRET_KEY` (invalidates all JWTs). Redeploy with updated `.env`.
- Rotate all database credentials (`POSTGRES_USER`/`POSTGRES_PASSWORD`) and rebuild services.
- Rotate third-party tokens/keys (e.g., Telegram `BOT_TOKEN`).
- Invalidate active sessions/tokens and audit recent access logs.

### 4. Validation

After configuring, check:

```bash
# Dependency vulnerabilities
# Using pip-audit via uvx
uvx pip-audit --strict

# Configuration logs
./scripts/run_docker.sh logs-web | grep -i "error\|warning"
```

### 5. Backup & restore

Regular, tested backups are essential. Example commands for local/Docker setups:

- Backup (custom format, compressed)

  ```bash
  source .env
  PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h localhost -p 5433 -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -F c -Z 3 -f backup_$(date +%F_%H%M%S).dump
  ```

- Restore (drops objects, then restores)

  ```bash
  source .env
  PGPASSWORD="$POSTGRES_PASSWORD" pg_restore \
    -h localhost -p 5433 -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -c backup_YYYY-MM-DD_HHMMSS.dump
  ```

- Docker alternative (create inside container and copy out)
  
  ```bash
  docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -F c -Z 3 -f /tmp/backup.dump
  docker cp $(docker compose ps -q db):/tmp/backup.dump ./backup.dump
  ```

Recommendations

- Automate backups with rotation (e.g., daily/weekly), store off‑site/encrypted.
- Regularly test restore on a staging DB.
- Restrict access to backup files (contain secrets/data).

## ⚠️ Warning

**Do NOT use defaults in production.**

All values in `env.example` are examples for development only.

**SECRET_KEY must be manually set to a strong random value before starting the application.**
