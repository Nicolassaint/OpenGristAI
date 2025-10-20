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

### API Endpoints

#### `POST /api/v1/chat`
```typescript
// Request
{
  messages: Message[],
  documentId: string,
  currentTableId?: string,
  currentTableName?: string
}

// Response
{
  response?: string,
  sql_query?: string,
  tool_calls?: ToolCall[],
  requires_confirmation?: boolean,
  confirmation_request?: ConfirmationRequest
}
```

#### `POST /api/v1/chat/confirm`
```typescript
// Request
{
  confirmation_id: string,
  approved: boolean,
  reason?: string
}

// Response
{
  status: "approved" | "rejected",
  result?: any,
  message?: string
}
```

### Système de Confirmation

Pour les opérations destructives, le système implémente un workflow de confirmation :

1. **Détection** : L'agent détecte une opération destructive
2. **Aperçu** : Génération d'un aperçu des éléments affectés
3. **Confirmation** : Interface utilisateur pour approuver/rejeter
4. **Exécution** : Exécution conditionnelle selon la décision

## 🐳 Déploiement

### Développement Local
```bash
# Script automatisé
./scripts/dev.sh

# Ou manuellement
docker-compose up -d
```

### Production
```bash
# Build complet
./scripts/build.sh

# Déploiement
docker-compose -f docker-compose.prod.yml up -d
```

## 🧪 Tests

### Backend
```bash
cd backend
pytest                    # Tests unitaires
pytest --cov=app tests/   # Avec couverture
```

### Frontend
```bash
cd frontend
npm run check            # TypeScript + Svelte
npm run test             # Tests unitaires
```

### Intégration
```bash
# Tests end-to-end
docker-compose up -d
./scripts/test-integration.sh
```

## 📊 Monitoring

### Métriques Backend
- Temps de réponse des agents
- Taux de succès des outils Grist
- Utilisation des modèles LLM

### Métriques Frontend
- Temps de chargement des composants
- Taux d'erreur des requêtes API
- Utilisation du localStorage

## 🔐 Sécurité

### Authentification
- **Backend** : API Key (Grist token)
- **Frontend** : Token automatique via Grist API

### Validation
- **Input** : Validation Pydantic côté backend
- **Output** : Sanitisation des réponses LLM
- **Confirmation** : Protection pour opérations destructives

### Rate Limiting
- Limite par utilisateur/document
- Cache Redis pour optimiser les performances
- Timeout pour les requêtes longues

## 🚀 Évolutivité

### Horizontal Scaling
- Backend : Load balancer + multiple instances
- Frontend : CDN + cache statique
- Database : Read replicas + connection pooling

### Vertical Scaling
- Backend : Plus de CPU/RAM pour les agents IA
- Frontend : Optimisation du bundle + lazy loading
- Database : SSD + plus de RAM pour le cache

## 📈 Roadmap Technique

- [ ] **Phase 1** : Monorepo + Architecture de base ✅
- [ ] **Phase 2** : Tests d'intégration complets
- [ ] **Phase 3** : Monitoring et observabilité
- [ ] **Phase 4** : Cache intelligent et optimisations
- [ ] **Phase 5** : Support multi-tenant
- [ ] **Phase 6** : API publique et SDK