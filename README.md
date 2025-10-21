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

**🤖 AI-Powered Widget Assistant for Grist Documents**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-2.16-FF3E00.svg)](https://kit.svelte.dev)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

*Interagissez avec vos documents [Grist](https://www.getgrist.com) en langage naturel*

</div>

---

## 🎯 Qu'est-ce que OpenGristAI ?

OpenGristAI est un assistant IA open source qui permet d'interagir avec vos documents Grist via un custom widget. Compatible avec n'importe quel modèle d'IA supportant le **function calling** via le protocole OpenAI (OpenAI, Anthropic, Mistral, modèles locaux via Ollama, etc.). 

## 🚀 Installation

### Docker (Recommandé)

**Option 1 : Docker Compose (Recommandé)**

```bash
# Cloner le projet
git clone https://github.com/nicolassaint/OpenGristAI.git
cd OpenGristAI

# Créer un fichier .env
cp .env.example .env
# Éditer .env avec votre vos variables

# Lancer en production
docker-compose -f docker-compose.prod.yml up -d
```

**Option 2 : Docker Run**

```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-proj-... \
  -e OPENAI_BASE_URL=https://api.openai.com/v1 \
  -e OPENAI_MODEL=gpt-4o-mini \
  -e GRIST_BASE_URL=https://grist.numerique.gouv.fr \
  -e CORS_ORIGINS=https://your-domain.com \
  -e LOG_LEVEL=INFO \
  -e ENVIRONMENT=production \
  --restart unless-stopped \
  --name opengristai \
  nicolassaint/opengristai:latest
```

Accédez à http://localhost:8000

**Variables d'environnement** :

**Obligatoires :**
- `OPENAI_API_KEY` - Votre clé API du fournisseur IA
- `OPENAI_BASE_URL` - URL du serveur API compatible OpenAI (défaut: `https://api.openai.com/v1`)
- `OPENAI_MODEL` - Modèle à utiliser (défaut: `gpt-4o-mini`)
- `CORS_ORIGINS` - Origines autorisées pour CORS, séparées par des virgules (défaut dev: `http://localhost:5173,http://localhost:8000`, prod: selon votre domaine)

**Optionnelles :**
- `GRIST_BASE_URL` - URL de votre instance Grist (défaut: `https://docs.getgrist.com`, DINUM: `https://grist.numerique.gouv.fr`)
- `LOG_LEVEL` - Niveau de logs (défaut: `INFO`)

**Configuration des ports (optionnels) :**
- `API_PORT` - Port du serveur backend (défaut: `8000`)
- `FRONTEND_PORT` - Port du serveur frontend en développement (défaut: `5173`)

**Paramètres LLM avancés (optionnels) :**
- `LLM_TEMPERATURE` - Créativité du modèle (défaut: `0.0` = déterministe)
- `LLM_MAX_TOKENS` - Limite de tokens par réponse (défaut: modèle par défaut)
- `LLM_TIMEOUT` - Timeout des requêtes en secondes (défaut: `60`)
- `LLM_MAX_RETRIES` - Nombre de tentatives en cas d'échec (défaut: `2`)

**Paramètres Agent (optionnels) :**
- `AGENT_MAX_ITERATIONS` - Nombre maximum d'appels d'outils (défaut: `15`)
- `AGENT_VERBOSE` - Logs détaillés de l'agent (défaut: `true`)

### Installation Locale (Développement)

<details>
<summary>Cliquez pour voir les instructions</summary>

```bash
git clone https://github.com/nicolassaint/OpenGristAI.git
cd OpenGristAI

# Installer les dépendances
make install

# Lancer le développement (Docker Compose avec hot-reload)
docker-compose up -d

# Ou manuellement
make dev-backend    # Terminal 1
make dev-frontend   # Terminal 2
```
</details>

## 📋 Intégration à Grist

Une fois OpenGristAI lancé, vous pouvez l'utiliser dans vos documents Grist :

1. **Ouvrez votre document Grist**
2. Cliquez sur **Add New** (en haut à gauche)
3. Sélectionnez **Add Widget to Page**
4. Choisissez **Custom Widget**
5. Sélectionnez la **table** que vous souhaitez lier à l'assistant
6. Cliquez sur **Add to Page**
7. Dans la configuration du widget :
   - **Custom URL** : `http://localhost:8000` (ou l'URL où OpenGristAI est hébergé)
8. Cliquez sur **Add Widget**


L'assistant IA est maintenant prêt à interagir avec votre document !

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

### Commandes de développement

```bash
make help           # Affiche toutes les commandes disponibles
make install        # Installe les dépendances
make dev-backend    # Lance le backend
make dev-frontend   # Lance le frontend
make docker-up      # Lance avec Docker Compose
```

Pour la liste complète des commandes (tests, lint, format, etc.), voir `make help`.

### Tests

```bash
make test-backend   # Tests backend (pytest)
make test-frontend  # Type checking frontend
```

Voir [Tests](backend/tests/README.md) pour les détails sur les tests unitaires, d'intégration et de couverture.


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

</div>