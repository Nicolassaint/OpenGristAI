# Grist AI Backend - Integration Complete

## Résumé des modifications

Le backend a été complètement adapté pour fonctionner avec votre front-end Grist existant et l'API Grist réelle. Toutes les données fictives ont été supprimées.

### Changements principaux

#### 1. Adaptation du contrat API

**Avant** : Endpoint `/api/v1/chat` avec un format générique
**Après** : Endpoint `/chat` compatible avec le front-end SvelteKit

**Format de requête attendu** :
```json
{
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "parts": [{"type": "text", "text": "Quelles tables sont dans ce document?"}],
      "createdAt": "2024-01-01T00:00:00Z"
    }
  ],
  "documentId": "nom-du-document-grist",
  "executionMode": "production"
}
```

**Format de réponse** :
```json
{
  "response": "Ce document contient 2 tables: Projects et Table1",
  "sql_query": "SELECT * FROM sqlite_master WHERE type='table'",
  "agent_used": "gpt-4o-mini",
  "tool_calls": [...]
}
```

#### 2. Intégration API Grist réelle

**Créé** : `app/services/grist_client.py`
- Client HTTP async pour l'API REST Grist
- Utilise le token JWT du front-end pour l'authentification
- Support des opérations : tables, colonnes, requêtes SQL, CRUD records

**Mis à jour** : `app/services/grist_service.py`
- Remplacé le mock par des appels API réels
- Formatage des données selon le format Grist API
- Gestion d'erreurs améliorée

#### 3. Gestion du contexte

Les tools utilisent maintenant un `ContextVar` pour accéder au service Grist :

```python
# Dans l'agent
set_grist_service(grist_service)

# Dans les tools
service = get_grist_service()
results = await service.get_tables()
```

#### 4. Support async complet

- Tous les tools sont maintenant async
- GristService est async avec gestion de connexion HTTP
- Cleanup automatique des ressources après chaque requête

## Structure des fichiers modifiés

```
app/
├── api/
│   ├── main.py          # Changé le préfixe de route de /api/v1 à /
│   ├── routes.py        # Adapté pour le format front-end, ajout header x-api-key
│   └── models.py        # Nouveaux modèles UIMessage, ChatRequest, ChatResponse
├── core/
│   ├── agent.py         # Accepte document_id + grist_token, gère le cleanup
│   └── tools.py         # Tools async avec ContextVar pour GristService
└── services/
    ├── grist_client.py  # NOUVEAU - Client HTTP pour API Grist
    └── grist_service.py # Mis à jour - Utilise GristAPIClient au lieu du mock
```

## Configuration requise

### 1. Variables d'environnement

Le backend supporte n'importe quelle API compatible OpenAI (OpenAI, Ollama, LM Studio, vLLM, etc.)

Éditez `.env` et configurez votre API :

```bash
# Configuration pour API compatible OpenAI
OPENAI_API_KEY=your-api-key-here           # Peut être "not-needed" pour serveurs locaux
OPENAI_BASE_URL=http://localhost:8000/v1   # URL de votre serveur API
OPENAI_MODEL=gpt-4o-mini                   # Nom du modèle à utiliser
```

**Exemples de configuration** :

**OpenAI (officiel)** :
```bash
OPENAI_API_KEY=sk-votre-cle-openai-ici
# OPENAI_BASE_URL non défini (utilise l'API OpenAI par défaut)
OPENAI_MODEL=gpt-4o-mini
```

**Ollama (local)** :
```bash
OPENAI_API_KEY=not-needed
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1:8b
```

**LM Studio (local)** :
```bash
OPENAI_API_KEY=not-needed
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_MODEL=votre-modele-local
```

**Serveur proxy/compatible** :
```bash
OPENAI_API_KEY=votre-token
OPENAI_BASE_URL=http://votre-serveur:port/v1
OPENAI_MODEL=nom-du-modele
```

Les autres variables ont des valeurs par défaut fonctionnelles.

### 2. Front-end

Vérifiez que le front-end pointe vers le bon endpoint dans `/Bercy/Projets/grist-ai-front/.env` :

```bash
PUBLIC_CHAT_URL='http://localhost:8000/chat'
```

## Démarrage

### Option 1 : Sans Docker (développement)

```bash
# Backend
cd /Users/nicolassaint/Bercy/Projets/grist-api-v2

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'API
python -m uvicorn app.api.main:app --reload --port 8000
```

Le serveur sera disponible sur `http://localhost:8000`

### Option 2 : Avec Docker

```bash
cd /Users/nicolassaint/Bercy/Projets/grist-api-v2
docker-compose up --build
```

## Test de l'intégration

### 1. Test avec le front-end

1. **Démarrer le backend** (voir ci-dessus)

2. **Démarrer le front-end** :
```bash
cd /Users/nicolassaint/Bercy/Projets/grist-ai-front
npm run dev
```

3. **Ouvrir le widget dans Grist** :
   - Ouvrez un document Grist
   - Ajoutez un Custom Widget
   - URL : `http://localhost:5173` (ou le port de votre front-end)
   - Activez "Full document access" dans les options du widget

4. **Tester une question** :
   - "Quelles tables sont dans ce document?"
   - "Montre-moi tous les enregistrements de la table Projects"

### 2. Test direct de l'API (sans front-end)

```bash
# Test health check
curl http://localhost:8000/health

# Test chat endpoint (nécessite un vrai token Grist)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: VOTRE_TOKEN_GRIST" \
  -d '{
    "messages": [{
      "id": "test-1",
      "role": "user",
      "parts": [{"type": "text", "text": "Quelles tables sont dans ce document?"}]
    }],
    "documentId": "votre-document-grist"
  }'
```

## Logs et débogage

Le backend utilise des logs colorés pour faciliter le débogage :

- **VERT** : Info messages (opérations réussies)
- **CYAN** : Debug messages (détails techniques)
- **JAUNE** : Warnings
- **ROUGE** : Erreurs

Exemple de logs attendus :
```
INFO     app.api.routes Received chat request for document: my-document
INFO     app.core.agent GristAgent initialized for document 'my-document', 5 tools
INFO     app.services.grist_service Getting all tables
INFO     app.api.routes Chat completed: 1 tool calls
```

## Troubleshooting

### Erreur "OPENAI_API_KEY environment variable is required"
- Vérifiez que `.env` contient votre clé OpenAI
- Redémarrez le serveur après avoir modifié `.env`

### Erreur 401 Unauthorized (Grist API)
- Le token Grist a expiré (durée de vie limitée)
- Le front-end gère automatiquement le refresh
- Vérifiez que le widget a "Full document access"

### Erreur 404 "Table not found"
- Vérifiez que le nom de la table est correct (sensible à la casse)
- Utilisez `get_tables` pour lister les tables disponibles

### Erreur de connexion au front-end
- Vérifiez que `PUBLIC_CHAT_URL` dans le front-end pointe vers `http://localhost:8000/chat`
- Vérifiez que le backend tourne sur le port 8000
- Vérifiez les logs CORS dans le backend

### L'agent ne fait pas d'appels d'outils
- Vérifiez que le modèle OpenAI supporte le function calling (gpt-4o-mini, gpt-4, etc.)
- Vérifiez les logs pour voir si des outils ont été appelés
- Le prompt peut nécessiter plus de clarté

## Prochaines étapes - Phase 2

Maintenant que l'intégration fonctionne, voici les améliorations à implémenter :

### 1. Validation layer (`app/services/validation.py`)
- Vérifier les permissions avant les opérations
- Valider les schémas (tables/colonnes existent)
- Valider les types de colonnes
- Valider les choix contre les valeurs autorisées

### 2. Error handling (`app/middleware/error_handler.py`)
- Classes d'exceptions personnalisées
- Messages d'erreur user-friendly
- Suggestions de corrections

### 3. Preview system
- Mode dry-run pour les opérations destructives
- Afficher les enregistrements affectés avant suppression/modification
- Workflow de confirmation

### 4. Transaction management
- Regrouper plusieurs opérations
- Rollback en cas d'échec
- Support des opérations atomiques

### 5. Tools complets
Implémenter les tools manquants du prompt original :
- `add_table`, `rename_table`, `remove_table`
- `add_table_column`, `update_table_column`, `remove_table_column`
- `get_pages`, `update_page`, `remove_page`
- `get_page_widgets`, `add_page_widget`, etc.
- `remove_records`
- `get_grist_access_rules_reference`

## Architecture technique

```
┌─────────────┐
│ Front-end   │ (SvelteKit)
│ Widget      │
└──────┬──────┘
       │ POST /chat
       │ x-api-key: JWT token
       ▼
┌─────────────────┐
│ FastAPI Backend │
│ /chat endpoint  │
└──────┬──────────┘
       │ Creates GristAgent
       ▼
┌─────────────┐        ┌──────────────┐
│ GristAgent  │◄───────│ LangChain    │
│             │        │ (OpenAI)     │
└──────┬──────┘        └──────────────┘
       │ Uses tools
       ▼
┌─────────────┐
│ Grist Tools │ (5 tools)
│ (async)     │
└──────┬──────┘
       │ Via ContextVar
       ▼
┌──────────────┐       ┌──────────────┐
│ GristService │──────►│ GristClient  │
│              │       │ (HTTP async) │
└──────────────┘       └──────┬───────┘
                              │ REST API calls
                              ▼
                       ┌──────────────┐
                       │ Grist API    │
                       │ (docs.getgrist│
                       │  .com/api)   │
                       └──────────────┘
```

## Support

Si vous rencontrez des problèmes :

1. Vérifiez les logs du backend (colorés dans la console)
2. Vérifiez les logs du front-end (console navigateur)
3. Vérifiez que les deux services communiquent sur les bons ports
4. Testez l'API Grist directement avec curl pour isoler les problèmes

Bonne chance avec l'intégration! 🚀
