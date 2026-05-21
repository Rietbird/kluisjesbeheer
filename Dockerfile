# syntax=docker/dockerfile:1.7

# ============================================================
# Stage 1 — Frontend build (Node)
# ============================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# Dependencies eerst (caching: package*.json verandert minder vaak dan src/)
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund

# Bron + build
COPY frontend/ ./
RUN npm run build

# ============================================================
# Stage 2 — Python runtime + cron + supervisord
# ============================================================
FROM python:3.13-slim AS runtime

# Systeem-deps:
# - cron       : voor dagelijkse leerling-sync
# - supervisor : draait gunicorn + cron als twee processen in 1 container
# - curl       : healthcheck
# - tini       : init-process voor correcte signal-handling (graceful shutdown)
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        cron supervisor curl tini ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/kluisjesbeheer

# Python deps (cached layer)
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install --no-cache-dir gunicorn

# Backend code
COPY backend/ /opt/kluisjesbeheer/backend/

# Frontend build uit stage 1
COPY --from=frontend-builder /build/dist /opt/kluisjesbeheer/frontend/dist

# Supervisord + cron config
# - supervisord-conf in /etc/supervisor/conf.d/ wordt automatisch geladen
# - /etc/cron.d/-files moeten 644 zijn en het user-veld bevatten (geen
#   crontab -u nodig); cron daemon pickt ze op bij start
COPY docker/supervisord.conf /etc/supervisor/conf.d/kluisjesbeheer.conf
COPY docker/cron-kluisjesbeheer /etc/cron.d/kluisjesbeheer
RUN chmod 644 /etc/cron.d/kluisjesbeheer

# Init-script (gebruikt door init-container in docker-compose)
COPY docker/init-config.sh /usr/local/bin/kluisjes-init.sh
RUN chmod 755 /usr/local/bin/kluisjes-init.sh

# App-user (gunicorn draait niet als root)
RUN useradd -r -u 1001 -d /opt/kluisjesbeheer -s /usr/sbin/nologin kluisjes && \
    chown -R kluisjes:kluisjes /opt/kluisjesbeheer

# Data-dir voor config.json + database + backups (zie docker-compose.yml)
# Alles persistent in één volume.
RUN mkdir -p /opt/kluisjesbeheer/backend/data/backups && \
    chown -R kluisjes:kluisjes /opt/kluisjesbeheer/backend/data
VOLUME ["/opt/kluisjesbeheer/backend/data"]

# Healthcheck: Flask antwoordt op /api/health
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:5000/api/health || exit 1

EXPOSE 5000

# tini als PID 1 -> propageert signals netjes naar supervisord
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
