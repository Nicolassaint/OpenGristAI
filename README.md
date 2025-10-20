<div align="center">

<pre>
   ___                   ____       _     _     _    ___ 
  / _ \ _ __   ___ _ __ / ___|_ __ (_)___| |_  / \  |_ _|
 | | | | '_ \ / _ \ '_ \| |  _| '__|| / __| __|/ _ \  | | 
 | |_| | |_) |  __/ | | | |_| | |   | \__ \ |_/ ___ \ | | 
  \___/| .__/ \___|_| |_|\____|_|   |_|___/\__/_/   \_\___|
       |_|                                                  
</pre>

# OpenGristAI

**🤖 AI-Powered Assistant for Grist Documents**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-2.16-FF3E00.svg)](https://kit.svelte.dev)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

*Interagissez avec vos documents [Grist](https://www.getgrist.com) en langage naturel*

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

## 🚀 Installation

### Docker (Recommandé)

```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_openai_api_key \
  --name opengristai \
  nicolassaint/opengristai:latest
```

Accédez à http://localhost:8000

**Variables d'environnement** :
- `OPENAI_API_KEY` - Votre clé OpenAI (obligatoire)
- `OPENAI_BASE_URL` - URL du serveur OpenAI (défaut: `https://api.openai.com/v1`)
- `OPENAI_MODEL` - Modèle à utiliser (défaut: `gpt-4o-mini`)
- `GRIST_BASE_URL` - URL de votre instance Grist (défaut: `https://docs.getgrist.com`)
- `LOG_LEVEL` - Niveau de logs (défaut: `INFO`)

**Exemple complet** :
```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-proj-... \
  -e OPENAI_BASE_URL=https://api.openai.com/v1 \
  -e OPENAI_MODEL=gpt-4o-mini \
  -e GRIST_BASE_URL=https://grist.numerique.gouv.fr \
  -e LOG_LEVEL=INFO \
  --name opengristai \
  nicolassaint/opengristai:latest
```

### Docker Compose (Développement)

```bash
git clone https://github.com/nicolassaint/OpenGristAI.git
cd OpenGristAI
cp backend/.env.example backend/.env
# Éditer backend/.env avec votre OPENAI_API_KEY
docker-compose up -d
```

### Installation Locale

<details>
<summary>Cliquez pour voir les instructions</summary>

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Éditer .env
uvicorn app.api.main:app --reload

# Frontend (nouveau terminal)
cd frontend
npm install
npm run dev
```
</details>

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

## 💬 Utilisation

**API Backend** : `http://localhost:8000/docs` pour la documentation interactive

**Exemple de requête** :
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-grist-token" \
  -d '{
    "messages": [{
      "role": "user",
      "parts": [{"type": "text", "text": "Quelles tables sont dans mon document ?"}]
    }],
    "documentId": "your-doc-id"
  }'
```

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

Créez `frontend/.env` :

```env
# Backend API URL
PUBLIC_CHAT_URL='http://localhost:8000/api/v1/chat'
```

**Note** : Avec Docker Compose, utilisez `http://backend:8000/api/v1/chat` pour la communication inter-conteneurs.

## 🧪 Développement

### Commandes disponibles (Makefile)

```bash
make help           # Affiche toutes les commandes disponibles

# Installation
make install        # Installe toutes les dépendances (backend + frontend)

# Développement local
make dev-backend    # Lance le backend
make dev-frontend   # Lance le frontend

# Docker Compose
make docker-up      # Lance avec Docker
make docker-down    # Arrête les conteneurs
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

**Backend** :
```bash
# Via Makefile (recommandé)
make test-backend       # Tous les tests (unit + integration mocked)
make test-unit          # Tests unitaires seulement
make test-integration   # Tests d'intégration (mocked)
make test-api           # Tests avec API Grist réelle (nécessite GRIST_API_KEY)
make test-coverage      # Tests avec rapport de couverture

# Directement avec pytest
cd backend
pytest -v                              # Tous les tests mocked
pytest -v -m unit                      # Tests unitaires
pytest -v -m integration               # Tests d'intégration
pytest -v -m requires_api              # Tests avec API réelle
pytest --cov=app --cov-report=html     # Avec couverture

# Qualité du code
make lint-backend       # Linting (ruff)
make format-backend     # Formatage (black)
```

**Frontend** :
```bash
make test-frontend      # Type checking
cd frontend
npm run check           # Type checking
npm run lint            # ESLint
npm run format          # Prettier
```


## 📖 Documentation

- 📚 **[Architecture Backend](backend/README.md)** • API FastAPI et agents IA
- 🎨 **[Frontend Widget](frontend/README.md)** • Interface SvelteKit
- 🧪 **[Tests](backend/tests/README.md)** • Guide des tests

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