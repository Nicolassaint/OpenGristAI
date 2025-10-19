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
[![LangChain](https://img.shields.io/badge/🦜🔗_LangChain-0.3-green.svg)](https://python.langchain.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

*Interagissez avec vos documents [Grist](https://www.getgrist.com) en langage naturel*

[Documentation](docs/) • [Installation](#-installation-rapide) • [Démo](#-exemples) • [Contributing](#-contributing)

</div>

---

## 🎯 Qu'est-ce que OpenGristAI ?

OpenGristAI est un assistant IA open source qui permet d'interagir avec vos documents Grist via une interface conversationnelle en langage naturel. Posez des questions, modifiez vos données, créez des tables - tout en français !

### ✨ Fonctionnalités

- 🇫🇷 **Interface française** • Prompts et interactions en français
- 🤖 **13 outils Grist** • CRUD complet sur tables, colonnes et enregistrements
- ✅ **Confirmations intelligentes** • Protection pour les opérations destructives
- 🔐 **Multi-auth** • JWT token (widget) + API key
- 🚀 **Performance** • Architecture async avec FastAPI + httpx
- 🧪 **Testé** • Suite complète de tests unitaires et d'intégration
- 🐳 **Production-ready** • Docker + docker-compose

### 🛠 Stack

Python 3.10+ • FastAPI • LangChain • Pydantic • httpx • PostgreSQL • Redis • Docker

## 📦 Installation Rapide

### Avec Docker (recommandé)

```bash
# Cloner le repo
git clone https://github.com/nicolassaint/OpenGristAI.git
cd OpenGristAI

# Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos clés API

# Lancer
docker-compose up -d

# Vérifier
curl http://localhost:8000/api/v1/health
```

### Sans Docker

```bash
# Prérequis : Python 3.10+
pip install -r requirements.txt

# Lancer l'API
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

## 🚀 Utilisation

### Endpoint Principal

**POST** `/api/v1/chat`

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

### Exemples

<details>
<summary><b>💬 Questions & Analyses</b></summary>

```
"Quelles sont les tables disponibles ?"
"Montre-moi les 10 derniers clients"
"Quel est le total des ventes par région ?"
"Quelle est la moyenne d'âge des employés ?"
```
</details>

<details>
<summary><b>➕ Créations</b></summary>

```
"Crée une table Projets avec colonnes Nom, Budget, Statut"
"Ajoute une colonne Date_Debut à la table Projets"
"Ajoute un client : Marie Dupont, marie@email.fr, Paris"
```
</details>

<details>
<summary><b>✏️ Modifications</b></summary>

```
"Change le statut du projet Alpha à 'Terminé'"
"Augmente le budget de tous les projets actifs de 10%"
"Renomme la colonne Date_Debut en Date_Lancement"
```
</details>

<details>
<summary><b>🗑️ Suppressions (avec confirmation)</b></summary>

```
"Supprime les projets archivés"
"Supprime la colonne Notes de la table Clients"
```
</details>

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

OpenGristAI supporte **tous les providers compatibles OpenAI** :

| Provider | Base URL | Exemple |
|----------|----------|---------|
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o-mini` |
| **HuggingFace** | `https://api-inference.huggingface.co/v1` | `meta-llama/Meta-Llama-3.1-8B-Instruct` |
| **Ollama** | `http://localhost:11434/v1` | `llama3.2` |
| **LM Studio** | `http://localhost:1234/v1` | `llama-3.2-3b-instruct` |

Voir `.env.example` pour la configuration complète.

## 🧪 Développement

```bash
# Tests
pytest                          # Tous les tests
pytest --cov=app tests/         # Avec couverture

# Qualité du code
black app/ tests/               # Formatage
ruff app/ tests/                # Linting
mypy app/                       # Types
```

## 🏗 Architecture

**Architecture en 3 couches** : API → Core → Services

```
┌─────────────┐
│  API Layer  │  FastAPI endpoints + validation
└──────┬──────┘
       │
┌──────▼──────┐
│ Core Layer  │  Agent + LLM + 13 Tools + Confirmations
└──────┬──────┘
       │
┌──────▼──────┐
│  Services   │  Grist Client + Validation + Preview
└──────┬──────┘
       │
   ┌───┴───┐
┌──▼──┐ ┌──▼──┐
│Grist│ │ LLM │
└─────┘ └─────┘
```

**Points clés** :
- 🔄 **Custom Agent Loop** : Meilleur contrôle que AgentExecutor
- ✅ **Système de confirmation** : Protection pour opérations destructives
- 🎯 **Validation multicouche** : Tables, colonnes, données

📚 Détails complets : [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## 📖 Documentation

- 📚 **[Architecture](docs/ARCHITECTURE.md)** • Détails techniques complets
- 🔗 **[Intégration](docs/INTEGRATION.md)** • Guide d'intégration Grist
- 🚀 **[API Reference](docs/)** • Documentation complète des endpoints

## 🤝 Contributing

Contributions bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing-feature`)
3. Commit les changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

**Guidelines** :
- Ajouter des tests pour toute nouvelle fonctionnalité
- Suivre le style de code existant (black + ruff)
- Mettre à jour la documentation si nécessaire

## 🗺 Roadmap

- [x] **Phase 1** - Foundation (LLM + 5 outils essentiels)
- [x] **Phase 2** - Robustness (Validation + confirmations)
- [ ] **Phase 3** - Intelligence (Mémorisation + contexte)
- [ ] **Phase 4** - Monitoring (Observabilité + métriques)
- [ ] **Phase 5** - Scale (Streaming + parallélisation + cache)

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
