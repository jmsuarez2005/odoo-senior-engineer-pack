---
name: deployment
description: Deploy Odoo 17 — Odoo.sh, self-hosted with nginx + workers + longpolling, multi-DB, Docker, backups. Use when planning deployment, troubleshooting production issues, or moving between environments.
---

# Deployment (Odoo 17)

## When to use this skill

Going to production. Or already in production and something is wrong: workers OOM, longpolling broken, slow under load, multi-DB confusion, or Odoo.sh-vs-self-hosted differences.

## Three deployment options

| Option | When | Tradeoffs |
|---|---|---|
| **Odoo.sh** | Want managed, integrated CI/CD, branches as staging | Locked into Odoo's stack; pricing scales with users + DB size |
| **Self-hosted (server)** | Full control, custom infra | You operate everything: backups, monitoring, security patches |
| **Docker / Kubernetes** | Cloud-native, want orchestration | Same as self-hosted plus container orchestration complexity |

The configuration of Odoo itself (`odoo.conf`) is largely the same across all three.

## The configuration file

`/etc/odoo/odoo.conf` (or wherever you mount it):

```ini
[options]
; Server identity
admin_passwd = <secret>                  ; database manager master password — KEEP SAFE
db_host = postgres-host
db_port = 5432
db_user = odoo
db_password = <secret>

; Multi-DB
; If unset, Odoo serves all DBs the user can list
; If set, Odoo restricts to listed DBs (or uses dbfilter to pick by hostname)
dbfilter = ^%h$                          ; only the DB whose name == hostname
list_db = False                          ; hide DB picker from selector

; Addons
addons_path = /opt/odoo/odoo/addons,/opt/odoo/enterprise,/opt/odoo/custom

; Ports (only if you don't reverse-proxy)
http_port = 8069
gevent_port = 8072                       ; longpolling — needed for chat, live updates

; Workers (production)
workers = 4                              ; CPU-bound HTTP workers — typically 2*cores - 1
max_cron_threads = 2                     ; cron workers
limit_memory_soft = 671088640            ; 640 MB
limit_memory_hard = 805306368            ; 768 MB
limit_request = 8192                     ; reqs per worker before recycle
limit_time_cpu = 60                      ; CPU sec per request
limit_time_real = 120                    ; wall sec per request
limit_time_real_cron = 0                 ; cron has no wall limit (set carefully)

; Logging
logfile = /var/log/odoo/odoo.log
log_level = info
log_handler = :INFO

; Email
email_from = noreply@example.com
smtp_server = smtp.example.com
smtp_port = 587
smtp_user = ...
smtp_password = <secret>
smtp_ssl = True

; Misc
proxy_mode = True                        ; trust X-Forwarded-* — REQUIRED behind nginx
without_demo = True                      ; never load demo in prod
data_dir = /var/lib/odoo                 ; sessions, filestore
```

### `workers = N` is mandatory in production

Without `workers`, Odoo runs single-threaded (gunicorn-style). Set it. Rule of thumb: `2 * CPU - 1`, then bench.

When `workers > 0`:
- HTTP requests handled by HTTP workers
- Cron handled by cron threads
- Longpolling handled by the gevent process (separate port)

## nginx reverse proxy

```nginx
upstream odoo_backend {
    server 127.0.0.1:8069;
}

upstream odoo_longpolling {
    server 127.0.0.1:8072;
}

server {
    listen 443 ssl http2;
    server_name odoo.example.com;

    ssl_certificate     /etc/letsencrypt/live/odoo.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/odoo.example.com/privkey.pem;

    proxy_read_timeout    720s;
    proxy_connect_timeout 720s;
    proxy_send_timeout    720s;
    client_max_body_size  500m;

    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;

    # Longpolling — IMPORTANT: separate location, separate upstream
    location /websocket {
        proxy_pass http://odoo_longpolling;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    location /longpolling {
        proxy_pass http://odoo_longpolling;
    }

    # Static files (let nginx serve)
    location ~* /web/static/ {
        proxy_cache_valid 200 60m;
        proxy_buffering on;
        expires 864000;
        proxy_pass http://odoo_backend;
    }

    location / {
        proxy_pass http://odoo_backend;
        proxy_redirect off;
    }

    # GZIP
    gzip on;
    gzip_min_length 1100;
    gzip_buffers 4 32k;
    gzip_types text/css text/less text/plain text/xml application/xml application/json application/javascript;
    gzip_vary on;
}

server {
    listen 80;
    server_name odoo.example.com;
    return 301 https://$server_name$request_uri;
}
```

Critical nginx points:
- Separate upstream for longpolling on port 8072 — without this, chat and live updates don't work.
- Set `proxy_mode = True` in odoo.conf so X-Forwarded-* are trusted.
- `client_max_body_size` matches your max attachment size.

## systemd service (self-hosted)

```ini
# /etc/systemd/system/odoo.service
[Unit]
Description=Odoo 17
After=network.target postgresql.service

[Service]
Type=simple
SyslogIdentifier=odoo
PermissionsStartOnly=true
User=odoo
Group=odoo
ExecStart=/opt/odoo/venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo/odoo.conf
KillMode=mixed
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now odoo
sudo journalctl -u odoo -f         # live logs
```

## Multi-DB setups

Two strategies:

### `dbfilter = ^%h$`
DB name is derived from hostname. `client1.example.com` → DB `client1`. Clean isolation per tenant.

### `dbfilter = ^%d$`
DB name from subdomain. `client1.example.com` → DB `client1` (only first subdomain part).

### `db_name = my_db`
Single-DB deployment — the DB selector is hidden, only `my_db` is served.

`list_db = False` always in production — exposing the DB list is a security smell.

## Backups

Odoo's filestore (attachments) lives at `data_dir/filestore/<db_name>/`. The DB has metadata; the filestore has the binary content. **Both** must be backed up.

```bash
# Database
pg_dump -U odoo -h localhost -F c my_db > my_db.dump

# Filestore
tar czf my_db_filestore.tar.gz /var/lib/odoo/filestore/my_db
```

Restore:
```bash
createdb -U odoo my_db
pg_restore -U odoo -d my_db my_db.dump
tar xzf my_db_filestore.tar.gz -C /var/lib/odoo/filestore/
```

For automation, use `db.dump_db` / `db.restore_db` via the database management API (or `odoo-bin`).

## Odoo.sh specifics

- Branches map to environments: `production`, `staging-N`, `dev-N`.
- Each push triggers a build (install/upgrade modules).
- `requirements.txt` at repo root is auto-installed.
- Custom system packages: `apt-packages.txt`.
- Container starts with the listed addons paths automatically — no addons_path config needed.
- Backups are automatic and downloadable from the dashboard.
- Limited shell access via SSH for debugging.
- No `--dev=all` in production; staging supports it.

## Docker example

```yaml
# docker-compose.yml
version: "3.8"
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
      POSTGRES_DB: postgres
    volumes:
      - pg-data:/var/lib/postgresql/data

  odoo:
    image: odoo:17
    depends_on:
      - postgres
    ports:
      - "8069:8069"
      - "8072:8072"
    environment:
      HOST: postgres
      USER: odoo
      PASSWORD: odoo
    volumes:
      - odoo-data:/var/lib/odoo
      - ./addons:/mnt/extra-addons
      - ./odoo.conf:/etc/odoo/odoo.conf

volumes:
  pg-data:
  odoo-data:
```

## Module install / upgrade in production

```bash
# Install a new module (ONCE)
odoo -c odoo.conf -d my_db -i hr_overtime --stop-after-init

# Upgrade an existing module (after code changes)
odoo -c odoo.conf -d my_db -u hr_overtime --stop-after-init

# Upgrade all installed modules (after a major change)
odoo -c odoo.conf -d my_db -u all --stop-after-init
```

Always:
- Take a backup first
- Test the upgrade on a staging DB
- Run with `--stop-after-init` (or it'll start the server again after)
- Schedule downtime — upgrades hold migration locks

## Monitoring

Key things to watch:
- HTTP 5xx rates
- Worker memory (RSS approaching `limit_memory_hard`)
- Postgres slow queries (`pg_stat_statements`)
- Filestore disk usage
- Mail queue length (`mail.mail` records with `state=outgoing`)

Hooks for monitoring:
- `/web/health` — exists in v17, returns 200 OK
- Odoo writes `[INFO]` logs every request; aggregate them with your log stack
- Postgres: `pg_stat_activity` + `pg_stat_statements`

## Common pitfalls

- `workers = 0` in production → single-threaded, slow.
- `proxy_mode = False` behind nginx → Odoo sees nginx's IP as the client; `request.httprequest.remote_addr` is wrong; CSRF and session security degrade.
- Longpolling not configured in nginx → chat / live updates broken even though everything else works.
- `limit_memory_hard` too low → workers killed mid-request, 502 from nginx.
- `--dev=all` in production → wide-open developer endpoints, never do this.
- Restoring a DB without restoring the filestore → all attachments broken (404 on download).
- Docker volume not persistent → `data_dir` lost on container recreate, sessions blow up, attachment links break.
- `dbfilter` regex mistake (e.g. `dbfilter = .*`) → multi-DB picker re-exposed unintentionally.
- Running `odoo -u all` without `--stop-after-init` → upgrade runs, then server starts in the same process.

## Pre-deployment checklist

- [ ] `proxy_mode = True` in odoo.conf
- [ ] `list_db = False`
- [ ] `dbfilter` set
- [ ] `workers > 0`
- [ ] Memory limits set
- [ ] `without_demo = True`
- [ ] Master `admin_passwd` is a strong secret
- [ ] HTTPS terminated at nginx
- [ ] Longpolling proxied separately (port 8072 / `/websocket`)
- [ ] Backups (DB + filestore) automated
- [ ] Monitoring on workers, DB, mail queue
- [ ] Staging environment exists for testing migrations

## References

- [Odoo 17 — Deploy](https://www.odoo.com/documentation/17.0/administration/on_premise/deploy.html)
- [Odoo 17 — Performance optimisation](https://www.odoo.com/documentation/17.0/administration/on_premise/source.html)
- [Odoo.sh documentation](https://www.odoo.com/documentation/17.0/administration/odoo_sh.html)
