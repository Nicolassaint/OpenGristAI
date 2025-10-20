# 🚀 Guide de Déploiement OpenGristAI

## 🛠️ Prérequis

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

## 🏠 Développement Local

### Docker Compose (Recommandé)

```bash
git clone https://github.com/nicolassaint/OpenGristAI.git
cd OpenGristAI

# Lancer avec hot-reload
docker-compose up -d

# Vérifier
curl http://localhost:8000/api/v1/health
```

### Manuel

```bash
git clone https://github.com/nicolassaint/OpenGristAI.git
cd OpenGristAI

# Installer les dépendances
make install

# Lancer le développement
make dev-backend    # Terminal 1
make dev-frontend   # Terminal 2
```

## 🏭 Production

### Docker Compose (Recommandé)

```bash
# Cloner le projet
git clone https://github.com/nicolassaint/OpenGristAI.git
cd OpenGristAI

# Créer un fichier .env
cp .env.example .env
# Éditer .env avec vos clés de production

# Lancer en production
docker-compose -f docker-compose.prod.yml up -d

# Vérifier
curl http://localhost:8000/api/v1/health
```

### Docker Run

```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-proj-... \
  -e OPENAI_BASE_URL=https://api.openai.com/v1 \
  -e OPENAI_MODEL=gpt-4o-mini \
  -e GRIST_BASE_URL=https://docs.getgrist.com \
  -e LOG_LEVEL=WARNING \
  -e ENVIRONMENT=production \
  --restart unless-stopped \
  --name opengristai \
  nicolassaint/opengristai:latest
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
