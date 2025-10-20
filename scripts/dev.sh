#!/bin/bash

# 🚀 Script de développement OpenGristAI
# Lance le backend et frontend en parallèle

set -e

echo "🤖 OpenGristAI - Démarrage du développement"
echo "=============================================="

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les logs avec couleur
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

# Vérifier les prérequis
log "Vérification des prérequis..."

# Python
if ! command -v python3 &> /dev/null; then
    error "Python 3 n'est pas installé"
    exit 1
fi

# Node.js
if ! command -v node &> /dev/null; then
    error "Node.js n'est pas installé"
    exit 1
fi

# Docker (optionnel)
if ! command -v docker &> /dev/null; then
    warning "Docker n'est pas installé - mode développement local uniquement"
fi

success "Prérequis OK"

# Configuration backend
log "Configuration du backend..."

if [ ! -f "backend/.env" ]; then
    if [ -f "backend/.env.example" ]; then
        log "Création du fichier .env à partir de .env.example"
        cp backend/.env.example backend/.env
        warning "⚠️  N'oubliez pas de configurer vos clés API dans backend/.env"
    else
        error "Fichier backend/.env.example introuvable"
        exit 1
    fi
fi

# Configuration frontend
log "Configuration du frontend..."

if [ ! -f "frontend/.env" ]; then
    log "Création du fichier frontend/.env"
    cat > frontend/.env << EOF
PUBLIC_CHAT_URL='http://localhost:8000/api/v1/chat'
EOF
    success "Fichier frontend/.env créé"
fi

# Installation des dépendances backend
log "Installation des dépendances backend..."
cd backend

if [ ! -d "venv" ]; then
    log "Création de l'environnement virtuel Python"
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
success "Dépendances backend installées"

cd ..

# Installation des dépendances frontend
log "Installation des dépendances frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    log "Installation des dépendances Node.js"
    npm install
    success "Dépendances frontend installées"
else
    log "Dépendances frontend déjà installées"
fi

cd ..

# Fonction pour nettoyer les processus à la sortie
cleanup() {
    log "Arrêt des services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Capturer Ctrl+C
trap cleanup SIGINT

# Lancement du backend
log "🚀 Démarrage du backend (port 8000)..."
cd backend
source venv/bin/activate
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Attendre que le backend soit prêt
log "Attente du démarrage du backend..."
sleep 3

# Test de santé du backend
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    success "✅ Backend démarré avec succès"
else
    error "❌ Échec du démarrage du backend"
    cleanup
fi

# Lancement du frontend
log "🎨 Démarrage du frontend (port 5173)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Attendre que le frontend soit prêt
log "Attente du démarrage du frontend..."
sleep 5

# Test de santé du frontend
if curl -s http://localhost:5173 > /dev/null; then
    success "✅ Frontend démarré avec succès"
else
    warning "⚠️  Frontend en cours de démarrage..."
fi

echo ""
echo "🎉 OpenGristAI est maintenant en cours d'exécution !"
echo ""
echo "📍 URLs disponibles :"
echo "   🔧 Backend API  : http://localhost:8000"
echo "   🎨 Frontend     : http://localhost:5173"
echo "   📚 API Docs     : http://localhost:8000/docs"
echo ""
echo "🛑 Pour arrêter : Ctrl+C"
echo ""

# Attendre que les processus se terminent
wait $BACKEND_PID $FRONTEND_PID
