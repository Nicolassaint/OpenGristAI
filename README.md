<div align="center">

```
   ___                   ____       _     _     _    ___ 
  / _ \ _ __   ___ _ __ / ___|_ __ (_)___| |_  / \  |_ _|
 | | | | '_ \ / _ \ '_ \| |  _| '__|| / __| __|/ _ \  | | 
 | |_| | |_) |  __/ | | | |_| | |   | \__ \ |_/ ___ \ | | 
  \___/| .__/ \___|_| |_|\____|_|   |_|___/\__/_/   \_\___|
       |_|                                                  
```

# OpenGristAI

**🤖 AI-Powered Assistant for Grist Documents**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-2.16-FF3E00.svg)](https://kit.svelte.dev)
[![LangChain](https://img.shields.io/badge/🦜🔗_LangChain-0.3-green.svg)](https://python.langchain.com)

*Interagissez avec vos documents [Grist](https://www.getgrist.com) en langage naturel*

[Documentation](docs/) • [Installation](#-installation-rapide) • [Démo](#-exemples) • [Contributing](#-contributing)

</div>

---

## 🎯 Qu'est-ce que OpenGristAI ?

OpenGristAI est un assistant IA open source complet qui permet d'interagir avec vos documents Grist via une interface conversationnelle moderne. Le projet comprend :

- **🔧 Backend API** : FastAPI avec 13 outils Grist et agents IA spécialisés
- **🎨 Frontend Widget** : Interface SvelteKit moderne intégrée nativement dans Grist
- **🤖 Intelligence** : Agents IA pour SQL, analyse et conversation naturelle

### ✨ Fonctionnalités

- 🇫🇷 **Interface française** • Prompts et interactions en français
- 🤖 **13 outils Grist** • CRUD complet sur tables, colonnes et enregistrements
- ✅ **Confirmations intelligentes** • Protection pour les opérations destructives
- 🔐 **Authentification automatique** • Token Grist intégré, aucune config manuelle
- 🚀 **Performance** • Architecture async avec FastAPI + SvelteKit
- 🧪 **Testé** • Suite complète de tests unitaires et d'intégration
- 🐳 **Production-ready** • Docker + docker-compose pour l'ensemble

### 🛠 Stack

**Backend** : Python 3.10+ • FastAPI • LangChain • Pydantic • httpx • PostgreSQL • Redis  
**Frontend** : SvelteKit 2.x • TypeScript • TailwindCSS • AI SDK

## 📦 Installation Rapide

### 🐳 Avec Docker (recommandé pour utilisateurs)

```bash
# Cloner le repo
git clone https://github.com/nicolassaint/OpenGristAI.git
cd OpenGristAI

# Configurer l'environnement
cp backend/.env.example backend/.env
# Éditer backend/.env avec vos clés API

# Lancer l'ensemble
make docker-up
# ou: docker-compose up -d

# Vérifier
curl http://localhost:8000/api/v1/health  # Backend
curl http://localhost:5173                # Frontend
```

### 💻 Développement local (recommandé pour développeurs)

**Option 1 : Utiliser les scripts (le plus simple)**

```bash
# 1. Configurer l'environnement
cp backend/.env.example backend/.env
# Éditer backend/.env avec vos clés API

# 2. Installer les dépendances
make install
# ou manuellement:
#   pip install -r backend/requirements.txt
#   cd frontend && npm install

# 3. Lancer le backend (terminal 1)
# Activez d'abord votre environnement Python (conda, venv, etc.)
conda activate your-env  # ou: source venv/bin/activate
make dev-backend
# ou: ./scripts/dev-backend.sh

# 4. Lancer le frontend (terminal 2)
make dev-frontend
# ou: ./scripts/dev-frontend.sh
```

**Option 2 : Commandes manuelles**

```bash
# Backend (terminal 1)
cd backend
# Activez votre environnement Python préféré
conda activate your-env  # ou venv, pyenv, etc.
pip install -r requirements.txt
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (terminal 2)
cd frontend
npm install
npm run dev
```

**Option 3 : Mix Docker + Local**

```bash
# Frontend via Docker
docker-compose up -d frontend

# Backend en local (pour debug intensif)
conda activate your-env
cd backend
uvicorn app.api.main:app --reload
```

## 🏗 Architecture du Monorepo

```
OpenGristAI/
├── 📁 backend/                    # API FastAPI + Agents IA
│   ├── app/                       # Code source Python
│   ├── tests/                     # Tests unitaires
│   ├── requirements.txt           # Dépendances Python
│   └── Dockerfile                # Image Docker backend
├── 📁 frontend/                   # Widget SvelteKit
│   ├── src/                       # Code source SvelteKit
│   ├── package.json              # Dépendances Node.js
│   └── svelte.config.js          # Config SvelteKit
├── 📁 docs/                      # Documentation unifiée
├── 📁 scripts/                   # Scripts de développement
│   ├── dev.sh                    # Lance backend + frontend
│   └── build.sh                  # Build de production
├── 📄 docker-compose.yml         # Déploiement complet
└── 📄 README.md                  # Ce fichier
```

## 🚀 Utilisation

### 1. Backend API

**Endpoint principal** : `POST /api/v1/chat`

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-grist-token" \
  -d '{
    "messages": [{
      "role": "user",
      "parts": [{"type": "text", "text": "Combien d'employés par département ?"}]
    }],
    "documentId": "your-doc-id"
  }'
```

### 2. Frontend Widget

1. **Développement** : `http://localhost:5173`
2. **Intégration Grist** : Ajouter comme Custom Widget
3. **Authentification** : Automatique via token Grist

## 🛠 Outils Disponibles

OpenGristAI dispose de **13 outils** organisés en 5 catégories :

| Catégorie | Outils | Description |
|-----------|--------|-------------|
| 📊 **Consultation** | `get_tables`<br>`get_table_columns`<br>`get_sample_records` | Explorer la structure et les données |
| 🔍 **Requêtes** | `query_document` | SQL SELECT (SQLite) avec agrégations |
| ➕ **Création** | `add_records`<br>`add_table`<br>`add_table_column` | Créer tables, colonnes, enregistrements |
| ✏️ **Modification** | `update_records`<br>`update_table_column` | Modifier données et structure |
| 🗑️ **Suppression** | `remove_records`<br>`remove_table_column` | Supprimer avec confirmation |

> 📝 **Note** : Les opérations de suppression et modifications massives requièrent une confirmation utilisateur.

## ⚙️ Configuration

### Backend (Python)

Voir `backend/.env.example` pour la configuration complète.

### Frontend (SvelteKit)

```env
# frontend/.env
PUBLIC_CHAT_URL='http://localhost:8000/api/v1/chat'
```

## 🧪 Développement

### Commandes disponibles (Makefile)

```bash
make help           # Affiche toutes les commandes disponibles

# Installation
make install        # Installe toutes les dépendances (backend + frontend)

# Développement local
make dev-backend    # Lance le backend (nécessite Python env activé)
make dev-frontend   # Lance le frontend

# Docker
make docker-up      # Lance tout via Docker
make docker-down    # Arrête tous les conteneurs
make docker-logs    # Affiche les logs

# Tests
make test-backend   # Teste le backend (pytest)
make test-frontend  # Teste le frontend (type checking)

# Qualité du code
make lint-backend   # Lint Python (ruff)
make format-backend # Format Python (black)
make lint-frontend  # Lint TypeScript (eslint)
make format-frontend # Format TypeScript (prettier)

# Nettoyage
make clean          # Supprime les fichiers temporaires
```

### Tests et qualité

```bash
# Backend
cd backend
pytest -v                       # Tests unitaires
pytest --cov=app                # Avec couverture
black app/ tests/               # Formatage
ruff app/ tests/                # Linting

# Frontend
cd frontend
npm run check                   # Type checking
npm run lint                    # ESLint
npm run format                  # Prettier
```

## 📖 Documentation

- 📚 **[Architecture Backend](backend/README.md)** • API FastAPI et agents IA
- 🎨 **[Frontend Widget](frontend/README.md)** • Interface SvelteKit
- 🔗 **[Intégration Grist](docs/INTEGRATION.md)** • Guide d'intégration
- 🚀 **[Déploiement](docs/DEPLOYMENT.md)** • Production et Docker

## 🤝 Contributing

Contributions bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing-feature`)
3. Commit les changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

**Guidelines** :
- Ajouter des tests pour toute nouvelle fonctionnalité
- Suivre le style de code existant (black + ruff pour Python, prettier + eslint pour JS/TS)
- Mettre à jour la documentation si nécessaire

## 🗺 Roadmap

- [x] **Phase 1** - Foundation (Backend API + 5 outils essentiels)
- [x] **Phase 2** - Frontend (Widget SvelteKit + intégration Grist)
- [x] **Phase 3** - Robustness (Validation + confirmations)
- [ ] **Phase 4** - Intelligence (Mémorisation + contexte)
- [ ] **Phase 5** - Monitoring (Observabilité + métriques)
- [ ] **Phase 6** - Scale (Streaming + parallélisation + cache)

## 📄 Licence

MIT License - voir [LICENSE](LICENSE) pour détails

## 💬 Support

- 🐛 **Issues** : [GitHub Issues](https://github.com/nicolassaint/OpenGristAI/issues)
- 💡 **Discussions** : [GitHub Discussions](https://github.com/nicolassaint/OpenGristAI/discussions)
- 📧 **Email** : nicolas.saint78@gmail.com

---

<div align="center">

**Made with ❤️ for the Grist community**

⭐ Si vous aimez ce projet, donnez-lui une étoile !

[Website](https://example.com) • [Documentation](docs/) • [Changelog](CHANGELOG.md)

</div>