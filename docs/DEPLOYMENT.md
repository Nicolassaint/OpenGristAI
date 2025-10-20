# 🚀 Guide de Déploiement OpenGristAI

## 🛠️ Prérequis

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

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

## 🏭 Production

### Variables d'Environnement

```bash
# backend/.env.production
ENVIRONMENT=production
LOG_LEVEL=WARNING
OPENAI_API_KEY=your-production-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
CORS_ORIGINS=https://yourdomain.com
```

### Docker Compose

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

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - PUBLIC_CHAT_URL=https://api.yourdomain.com/api/v1/chat
    restart: unless-stopped
```

### Déploiement

```bash
# Lancer en production
docker-compose -f docker-compose.prod.yml up -d

# Vérifier
curl http://localhost:8000/api/v1/health
curl http://localhost:5173
```

Pour un déploiement cloud (AWS, GCP, DigitalOcean), consulter la documentation officielle de ces plateformes.

## 🚨 Troubleshooting

### Backend ne démarre pas
```bash
# Vérifier les logs
docker-compose logs backend

# Vérifier la configuration
cat backend/.env
```

### Frontend ne se charge pas
```bash
# Vérifier les logs
docker-compose logs frontend

# Tester l'API backend
curl http://localhost:8000/api/v1/health
```

### Logs en temps réel
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```
