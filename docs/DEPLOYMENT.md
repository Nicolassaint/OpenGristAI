# 🚀 Guide de Déploiement OpenGristAI

## Vue d'ensemble

Ce guide couvre le déploiement d'OpenGristAI en développement, staging et production.

## 🛠️ Prérequis

### Développement
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optionnel)

### Production
- Docker & Docker Compose
- PostgreSQL 16+ (ou service cloud)
- Redis 7+ (ou service cloud)
- Domaine avec SSL (recommandé)

## 🏠 Développement Local

### Option 1 : Script Automatisé (Recommandé)

```bash
# Cloner le projet
git clone https://github.com/nicolassaint/OpenGristAI.git
cd OpenGristAI

# Lancer le développement complet
./scripts/dev.sh
```

Le script va :
- ✅ Vérifier les prérequis
- ✅ Configurer les environnements
- ✅ Installer les dépendances
- ✅ Lancer backend + frontend
- ✅ Tester la connectivité

### Option 2 : Docker Compose

```bash
# Configuration
cp backend/.env.example backend/.env
# Éditer backend/.env avec vos clés API

# Lancer tous les services
docker-compose up -d

# Vérifier
curl http://localhost:8000/api/v1/health  # Backend
curl http://localhost:5173                # Frontend
```

### Option 3 : Manuel

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.api.main:app --host 0.0.0.0 --port 8000

# Frontend (nouveau terminal)
cd frontend
npm install
npm run dev
```

## 🧪 Staging

### Configuration

```bash
# Variables d'environnement staging
export ENVIRONMENT=staging
export LOG_LEVEL=INFO
export OPENAI_API_KEY=your-staging-key
```

### Déploiement

```bash
# Build de staging
./scripts/build.sh

# Déploiement
cd dist
docker-compose -f docker-compose.prod.yml up -d
```

## 🏭 Production

### Architecture Recommandée

```
┌─────────────────────────────────────────┐
│              🌐 Load Balancer           │
│  Nginx + SSL + Rate Limiting            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              🎨 Frontend               │
│  SvelteKit (Static) + CDN              │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              🔧 Backend API             │
│  FastAPI + Multiple Instances           │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
    ┌───▼───┐           ┌───▼───┐
    │PostgreSQL│         │ Redis │
    └─────────┘           └───────┘
```

### Configuration Production

#### 1. Variables d'Environnement

```bash
# backend/.env.production
ENVIRONMENT=production
LOG_LEVEL=WARNING

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0

# OpenAI
OPENAI_API_KEY=your-production-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Security
SECRET_KEY=your-secret-key
CORS_ORIGINS=https://yourdomain.com
```

#### 2. Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    restart: unless-stopped
    deploy:
      replicas: 3

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - PUBLIC_CHAT_URL=https://api.yourdomain.com/api/v1/chat
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: opengristai
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
```

### Déploiement Production

#### 1. Build et Test

```bash
# Build de production
./scripts/build.sh

# Tests de production
cd dist
docker-compose -f docker-compose.prod.yml up -d
./scripts/test-production.sh
```

#### 2. Déploiement avec Nginx

```nginx
# /etc/nginx/sites-available/opengristai
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 3. Script de Déploiement

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Déploiement OpenGristAI en production"

# Backup de la base de données
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Pull des dernières modifications
git pull origin main

# Build de production
./scripts/build.sh

# Redémarrage des services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Vérification
curl -f http://localhost:8000/api/v1/health || exit 1
curl -f http://localhost:5173 || exit 1

echo "✅ Déploiement réussi"
```

## ☁️ Déploiement Cloud

### AWS

#### ECS avec Fargate

```yaml
# ecs-task-definition.json
{
  "family": "opengristai",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-registry/opengristai-backend:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"}
      ]
    }
  ]
}
```

#### RDS + ElastiCache

```bash
# Créer RDS PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier opengristai-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password your-password

# Créer ElastiCache Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id opengristai-redis \
  --cache-node-type cache.t3.micro \
  --engine redis
```

### Google Cloud

#### Cloud Run

```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: opengristai-backend
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containers:
      - image: gcr.io/your-project/opengristai-backend
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
```

### DigitalOcean

#### App Platform

```yaml
# .do/app.yaml
name: opengristai
services:
- name: backend
  source_dir: backend
  github:
    repo: your-username/OpenGristAI
    branch: main
  run_command: uvicorn app.api.main:app --host 0.0.0.0 --port 8080
  environment_slug: python
  instance_count: 2
  instance_size_slug: basic-xxs
  envs:
  - key: ENVIRONMENT
    value: production

- name: frontend
  source_dir: frontend
  github:
    repo: your-username/OpenGristAI
    branch: main
  run_command: npm run build && npm run preview
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs
```

## 📊 Monitoring

### Métriques Essentielles

```bash
# Health checks
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/stats

# Logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Alerting

```yaml
# monitoring/alerts.yml
alerts:
  - name: "Backend Down"
    condition: "backend_health_check == 0"
    action: "send_slack_notification"
  
  - name: "High Error Rate"
    condition: "error_rate > 5%"
    action: "send_email_alert"
```

## 🔒 Sécurité

### SSL/TLS

```bash
# Let's Encrypt avec Certbot
certbot --nginx -d yourdomain.com
```

### Firewall

```bash
# UFW Configuration
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### Secrets Management

```bash
# Docker Secrets
echo "your-secret" | docker secret create openai_api_key -

# Utilisation dans docker-compose
services:
  backend:
    secrets:
      - openai_api_key
```

## 🚨 Troubleshooting

### Problèmes Courants

#### Backend ne démarre pas
```bash
# Vérifier les logs
docker-compose logs backend

# Vérifier la configuration
cat backend/.env

# Tester la connectivité DB
docker-compose exec backend python -c "import psycopg2; print('DB OK')"
```

#### Frontend ne se charge pas
```bash
# Vérifier les logs
docker-compose logs frontend

# Vérifier la configuration
cat frontend/.env

# Tester l'API backend
curl http://localhost:8000/api/v1/health
```

#### Base de données
```bash
# Connexion à PostgreSQL
docker-compose exec postgres psql -U grist_ai -d grist_ai_db

# Vérifier Redis
docker-compose exec redis redis-cli ping
```

### Performance

#### Optimisation Backend
```python
# backend/app/config.py
class Settings:
    # Connection pooling
    DATABASE_POOL_SIZE = 20
    DATABASE_MAX_OVERFLOW = 30
    
    # Cache
    REDIS_TTL = 3600
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = 60
```

#### Optimisation Frontend
```javascript
// frontend/vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['svelte', '@sveltejs/kit']
        }
      }
    }
  }
})
```

## 📈 Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 5
    environment:
      - WORKER_PROCESSES=4
```

### Load Balancing

```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location /api/ {
        proxy_pass http://backend;
    }
}
```

## 🔄 CI/CD

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy
        run: |
          ./scripts/build.sh
          ./scripts/deploy.sh
```

## 📚 Ressources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [SvelteKit Deployment](https://kit.svelte.dev/docs/adapter-vercel)
- [PostgreSQL Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Best Practices](https://redis.io/docs/manual/admin/)
