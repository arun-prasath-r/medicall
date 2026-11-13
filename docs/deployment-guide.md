# Medicall - Production Deployment & Operations Guide

**Project Name:** Medicall  
**Document Version:** 1.0.0  
**Status:** Operations & Deployment Specification  
**Deployment Target:** Production / Academic Cloud Infrastructure  
**Last Updated:** November 2026  

---

## 1. Deployment Architecture Overview

Medicall follows a modern, cost-efficient decoupled deployment pattern. Because the monorepo consists of a standalone React Single Page Application (SPA) and an asynchronous Python FastAPI service, each component is hosted on an infrastructure layer optimized for its workload.

```mermaid
flowchart LR
    subgraph Client["Users & Patients"]
        Browser["User Browser (Desktop / Mobile)"]
    end

    subgraph CDNLayer["Edge / Static Hosting (Vercel / Netlify / Cloudflare Pages)"]
        FrontendHost["Vite React SPA (Static HTML / CSS / JS)"]
    end

    subgraph ComputeLayer["Backend Cloud (Render / Railway / Docker Container)"]
        UvicornServer["FastAPI Asynchronous Engine (Uvicorn)"]
    end

    subgraph DataLayer["Managed Database (Render / Neon / Supabase / AWS RDS)"]
        PostgresDB[("PostgreSQL 15+ Database")]
    end

    subgraph External["Google Cloud Platform"]
        GeminiCloud["Google Gemini AI API"]
    end

    Browser -->|HTTPS / Port 443| FrontendHost
    Browser -->|HTTPS API Requests / SSE| UvicornServer
    UvicornServer -->|PostgreSQL TLS Connection| PostgresDB
    UvicornServer -->|HTTPS REST / gRPC| GeminiCloud
```

---

## 2. Frontend Deployment (`/frontend`)

### 2.1 Recommended Hosting Options
1. **Cloudflare Pages / Vercel / Netlify (Recommended for student & production setups):**
   - Free tier suitable for high-traffic static asset distribution.
   - Global CDN edge caching with zero server configuration.
   - Automatic TLS/SSL certificate issuance.
2. **Nginx Container (Self-hosted alternative):**
   - Packaged as a lightweight Alpine Docker container serving compiled `/dist` static files.

### 2.2 Production Build Steps
```bash
# Navigate to frontend directory
cd frontend

# Install production dependencies
npm ci

# Compile optimized static bundle
npm run build
# Output directory: frontend/dist
```

### 2.3 Single Page Application (SPA) Routing Configuration
Because React Router manages client-side routes (e.g., `/assistant`, `/doctors`), the web server must rewrite all non-file requests to `index.html`.
- **For Vercel (`vercel.json`):**
  ```json
  {
    "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
  }
  ```
- **For Netlify (`_redirects`):**
  ```text
  /*    /index.html   200
  ```

---

## 3. Backend Deployment (`/backend`)

### 3.1 Recommended Compute Environments
1. **PaaS Hosting (Render / Railway / Fly.io):**
   - Simple git-push deployments with automated build environments.
   - Built-in HTTPS endpoints and environment variable encryption.
2. **Docker Container Deployment:**
   - Reproducible containerized execution across any cloud provider (AWS ECS, Google Cloud Run, DigitalOcean App Platform).

### 3.2 Production Dockerfile (`backend/Dockerfile`)
```dockerfile
# Multi-stage lightweight Python 3.11 image
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies for PostgreSQL driver
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . .

# Run as non-privileged user for security
RUN useradd -m medicalluser && chown -R medicalluser:medicalluser /app
USER medicalluser

EXPOSE 8000

# Start Uvicorn with production worker concurrency
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers"]
```

---

## 4. Managed PostgreSQL Database Hosting

### 4.1 Recommended Database Providers
- **Neon / Supabase / Render Postgres:** Provides managed PostgreSQL 15+ with automated backups, SSL connections, and connection pooling.
- **Connection Security:** Require SSL mode: `sslmode=require` in database connection strings.

### 4.2 Automated Schema Migrations on Deployment
Incorporate Alembic migrations into the deployment pipeline before starting the web process:
```bash
# Execute within backend container startup script
alembic upgrade head
```

---

## 5. Production Environment Configuration

All sensitive keys must be injected via runtime environment variables. Never commit actual secrets into Git.

### 5.1 Backend Environment Template (`backend/.env.production`)
```ini
# Environment Mode
ENVIRONMENT=production
DEBUG=False

# Database Connectivity (Managed PostgreSQL)
DATABASE_URL=postgresql+asyncpg://medicall_user:SuperSecretPassword@db.host.cloud:5432/medicall_prod?ssl=require

# JWT Cryptography
JWT_SECRET_KEY=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Google Gemini AI Integration
GEMINI_API_KEY=AIzaSyA_ExampleGoogleGeminiKeyHere
GEMINI_MODEL=gemini-1.5-flash

# Regional Emergency Configuration
DEFAULT_COUNTRY_CODE=US
EMERGENCY_PHONE_NUMBER=911

# CORS Allowed Origins
CORS_ORIGINS=["https://medicall.example.com"]
```

### 5.2 Frontend Environment Template (`frontend/.env.production`)
```ini
# Backend API Base URL
VITE_API_BASE_URL=https://api.medicall.example.com/api/v1

# Emergency Phone Fallback
VITE_DEFAULT_EMERGENCY_PHONE=911
```

---

## 6. Production Security & HTTPS Hardening

1. **Strict Transport Security (HSTS):** Enforce `Strict-Transport-Security: max-age=31536000; includeSubDomains` on all responses.
2. **CORS Isolation:** The backend `CORS_ORIGINS` setting must strictly match the production frontend origin. Never allow `*` in production.
3. **API Key Guard:** Verify that `GEMINI_API_KEY` is never referenced in frontend code or Vite environment templates (`VITE_*`).
4. **Health Check Endpoint:** Expose a lightweight `GET /health` route returning `{ "status": "healthy" }` without database overhead for load balancer probes.

---

## 7. Database Backups & Recovery

1. **Daily Automated Snapshots:** Managed database providers (e.g., Neon, Render) execute daily automated snapshots with 7-day point-in-time recovery (PITR).
2. **Manual Logical Backup Script (`pg_dump`):**
   ```bash
   # Scheduled cron backup script
   pg_dump -U medicall_user -h db.host.cloud -d medicall_prod -F c -b -v -f "/backups/medicall_backup_$(date +%Y%m%d_%H%M%S).dump"
   ```

---

## 8. Logging, Monitoring & Observability

- **Structured JSON Logging:** FastAPI logs request method, path, response status, and duration in structured JSON format for log ingestion services (e.g., Better Stack, Datadog).
- **Audit Log Retention:** Ensure the `audit_logs` table is backed up regularly to retain access trails for clinical data compliance.
- **Uptime Probes:** Use a free uptime monitoring service (e.g., UptimeRobot) pinging `GET https://api.medicall.example.com/health` every 5 minutes.

