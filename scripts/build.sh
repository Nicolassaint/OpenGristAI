#!/bin/bash

# 🏗️ Script de build OpenGristAI
# Build de production pour backend et frontend

set -e

echo "🏗️ OpenGristAI - Build de production"
echo "======================================"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "docker-compose.yml" ]; then
    error "Ce script doit être exécuté depuis la racine du projet OpenGristAI"
    exit 1
fi

# Créer le dossier de build
BUILD_DIR="dist"
log "Création du dossier de build : $BUILD_DIR"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# Build du backend
log "🔧 Build du backend..."

cd backend

# Vérifier l'environnement virtuel
if [ ! -d "venv" ]; then
    log "Création de l'environnement virtuel Python"
    python3 -m venv venv
fi

source venv/bin/activate

# Installation des dépendances
log "Installation des dépendances backend..."
pip install -r requirements.txt

# Tests backend
log "Exécution des tests backend..."
if pytest tests/ -v; then
    success "✅ Tests backend passés"
else
    error "❌ Tests backend échoués"
    exit 1
fi

# Qualité du code backend
log "Vérification de la qualité du code backend..."
black --check app/ tests/ || {
    warning "Code non formaté, formatage automatique..."
    black app/ tests/
}

ruff app/ tests/ || {
    error "Erreurs de linting détectées"
    exit 1
}

mypy app/ || {
    warning "Erreurs de type détectées (non bloquant)"
}

success "✅ Backend prêt pour la production"

cd ..

# Build du frontend
log "🎨 Build du frontend..."

cd frontend

# Installation des dépendances
if [ ! -d "node_modules" ]; then
    log "Installation des dépendances frontend..."
    npm install
fi

# Tests frontend
log "Exécution des tests frontend..."
if npm run check; then
    success "✅ Tests frontend passés"
else
    error "❌ Tests frontend échoués"
    exit 1
fi

# Build de production
log "Build de production frontend..."
npm run build

success "✅ Frontend prêt pour la production"

cd ..

# Copier les fichiers de build
log "Copie des fichiers de build..."

# Backend
mkdir -p $BUILD_DIR/backend
cp -r backend/app $BUILD_DIR/backend/
cp backend/requirements.txt $BUILD_DIR/backend/
cp backend/Dockerfile $BUILD_DIR/backend/

# Frontend
mkdir -p $BUILD_DIR/frontend
cp -r frontend/build $BUILD_DIR/frontend/
cp frontend/package.json $BUILD_DIR/frontend/

# Documentation
cp -r docs $BUILD_DIR/
cp README.md $BUILD_DIR/
cp LICENSE $BUILD_DIR/
cp docker-compose.yml $BUILD_DIR/

# Docker Compose de production
log "Création du docker-compose de production..."
cat > $BUILD_DIR/docker-compose.prod.yml << 'EOF'
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
      - PUBLIC_CHAT_URL=http://localhost:8000/api/v1/chat
    restart: unless-stopped
EOF

success "✅ Build de production terminé"

echo ""
echo "🎉 Build de production réussi !"
echo ""
echo "📁 Fichiers générés dans : $BUILD_DIR/"
echo "🐳 Pour déployer : cd $BUILD_DIR && docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "📍 URLs de production :"
echo "   🔧 Backend API  : http://localhost:8000"
echo "   🎨 Frontend     : http://localhost:5173"
echo ""
