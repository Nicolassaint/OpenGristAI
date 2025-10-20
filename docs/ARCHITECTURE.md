# 🏗️ Architecture OpenGristAI

## Vue d'ensemble

OpenGristAI est un monorepo contenant un backend FastAPI et un frontend SvelteKit, conçu pour fournir une interface IA conversationnelle intégrée à Grist.

## 📁 Structure du Monorepo

```
OpenGristAI/
├── 📁 backend/                    # API FastAPI + Agents IA
│   ├── app/                       # Code source Python
│   │   ├── api/                   # Endpoints FastAPI
│   │   ├── core/                  # Logique métier (agents)
│   │   ├── services/              # Services externes (Grist, LLM)
│   │   └── models/                # Modèles Pydantic
│   ├── tests/                     # Tests unitaires
│   ├── requirements.txt           # Dépendances Python
│   └── Dockerfile                # Image Docker backend
├── 📁 frontend/                   # Widget SvelteKit
│   ├── src/                       # Code source SvelteKit
│   │   ├── lib/                   # Composants et utilitaires
│   │   ├── routes/                # Pages et API routes
│   │   └── app.html               # Template HTML
│   ├── package.json              # Dépendances Node.js
│   └── Dockerfile                # Image Docker frontend
├── 📁 docs/                      # Documentation
├── 📁 scripts/                   # Scripts de développement
├── 📄 docker-compose.yml         # Orchestration complète
└── 📄 README.md                  # Documentation principale
```

## 🔧 Backend Architecture

### Stack Technique
- **Framework** : FastAPI 0.115+
- **Langage** : Python 3.10+
- **IA** : LangChain + OpenAI-compatible APIs
- **Base de données** : PostgreSQL 16
- **Cache** : Redis 7
- **Tests** : pytest + coverage

### Architecture en Couches

```
┌─────────────────────────────────────────┐
│              🌐 API Layer               │
│  FastAPI Endpoints + Validation         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              🧠 Core Layer              │
│  Agents + LLM + 13 Tools + Confirmations│
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│             🔌 Services Layer          │
│  Grist Client + Validation + Preview   │
└─────────────────┬───────────────────────┘
                  │
            ┌─────┴─────┐
            │           │
        ┌───▼───┐   ┌───▼───┐
        │ Grist │   │  LLM  │
        └───────┘   └───────┘
```

### Agents IA Spécialisés

1. **Agent de Routing** : Dirige les messages vers l'agent approprié
2. **Agent Générique** : Traite les questions générales et le petit talk
3. **Agent SQL** : Génère et exécute des requêtes SQL
4. **Agent d'Analyse** : Fournit des interprétations des résultats

### 13 Outils Grist

| Catégorie | Outils | Description |
|-----------|--------|-------------|
| 📊 **Consultation** | `get_tables`, `get_table_columns`, `get_sample_records` | Explorer la structure |
| 🔍 **Requêtes** | `query_document` | SQL SELECT avec agrégations |
| ➕ **Création** | `add_records`, `add_table`, `add_table_column` | Créer des éléments |
| ✏️ **Modification** | `update_records`, `update_table_column` | Modifier des éléments |
| 🗑️ **Suppression** | `remove_records`, `remove_table_column` | Supprimer avec confirmation |

## 🎨 Frontend Architecture

### Stack Technique
- **Framework** : SvelteKit 2.x
- **Langage** : TypeScript
- **Styling** : TailwindCSS
- **UI Components** : bits-ui, lucide-svelte
- **Chat SDK** : @ai-sdk/svelte
- **Build** : Vite

### Architecture des Composants

```
┌─────────────────────────────────────────┐
│              🎨 UI Layer                │
│  SvelteKit Routes + Components          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              🔗 Integration Layer      │
│  Grist API + Backend API + LocalStorage │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              🧠 State Management       │
│  Chat State + Confirmations + Context  │
└─────────────────┬───────────────────────┘
                  │
            ┌─────┴─────┐
            │           │
        ┌───▼───┐   ┌───▼───┐
        │ Grist │   │Backend│
        └───────┘   └───────┘
```

### Composants Principaux

- **`chat.svelte`** : Composant principal du chat
- **`multimodal-input.svelte`** : Zone de saisie avec support multimédia
- **`messages.svelte`** : Container des messages avec streaming
- **`confirmation.svelte`** : Système de confirmation pour opérations destructives

### Intégration Grist

Le widget s'intègre nativement dans Grist via :
1. **Authentification automatique** : `grist.docApi.getAccessToken()`
2. **Contexte intelligent** : Détection de la table visualisée
3. **Permissions** : Accès complet au document
4. **Persistance** : localStorage par document/table

## 🔄 Communication Backend ↔ Frontend

### Endpoints Principaux

- `POST /api/v1/chat` - Envoyer un message et recevoir la réponse de l'agent
- `POST /api/v1/chat/confirm` - Confirmer/rejeter une opération destructive

Voir [backend README](../backend/README.md) pour les détails complets de l'API.

## 🐳 Déploiement

Voir [DEPLOYMENT.md](DEPLOYMENT.md) pour le guide complet.

## 🧪 Tests

```bash
make test-backend   # Tests backend
make test-frontend  # Tests frontend
```

Voir [tests/README.md](../backend/tests/README.md) pour détails.

