# 🤖 Grist AI Chatbot

> Widget de chat IA pour Grist - Interface frontend simplifiée

Un widget de chat moderne qui s'intègre dans Grist pour permettre des interactions en langage naturel avec vos données.

## 🎯 Fonctionnalités

- ✅ **Interface de chat moderne** avec streaming en temps réel
- ✅ **Intégration native Grist** (Custom Widget)
- ✅ **Authentification automatique** via token Grist
- ✅ **Contexte intelligent** : Détection automatique de la table visualisée
- ✅ **Système de confirmation** élégant pour opérations destructives
- ✅ **Persistance complète** : Messages, métadonnées et confirmations dans localStorage
- ✅ **Affichage SQL** : Requêtes exécutées affichées avec badge
- ✅ **Limite de messages** configurable (20 par défaut)
- ✅ **Dark/Light mode** avec support complet
- ✅ **Design responsive** et accessible

## 📋 Prérequis

- Node.js 18.x ou supérieur
- npm
- Un backend API Python (voir `grist-api-v2`)

## 🚀 Installation

1. **Cloner le projet** :

```bash
git clone <repository-url>
cd grist-ai-front
```

2. **Installer les dépendances** :

```bash
npm install
```

3. **Configurer l'environnement** :
   Créer un fichier `.env` à la racine :

```env
PUBLIC_CHAT_URL='http://localhost:8000/chat'
```

4. **Lancer le serveur de développement** :

```bash
npm run dev
```

L'application sera disponible sur `http://localhost:5173`

## 📁 Structure du projet

```
grist-ai-front/
├── src/
│   ├── lib/
│   │   ├── components/
│   │   │   ├── chat.svelte              # Composant principal du chat
│   │   │   ├── chat-header.svelte       # Header avec bouton reset
│   │   │   ├── messages.svelte          # Container des messages
│   │   │   ├── multimodal-input.svelte  # Zone de saisie
│   │   │   ├── sql-query-badge.svelte   # Badge pour les requêtes SQL
│   │   │   ├── code-block.svelte        # Rendu des blocs de code
│   │   │   ├── icons/                   # Icônes SVG
│   │   │   ├── markdown/                # Composants de rendu markdown
│   │   │   ├── messages/                # Composants de messages
│   │   │   └── ui/                      # Composants UI (button, textarea, sonner)
│   │   ├── hooks/
│   │   │   ├── useApiKey.ts            # Gestion du token Grist
│   │   │   ├── local-storage.svelte.ts # Persistance localStorage
│   │   │   └── lock.ts                 # Utilitaire de verrouillage
│   │   └── utils/
│   │       ├── shadcn.ts               # Utilitaires UI
│   │       └── types.ts                # Types TypeScript
│   ├── routes/
│   │   ├── (chat)/
│   │   │   ├── +page.svelte            # Page principale du chat
│   │   │   ├── +layout.svelte          # Layout du chat
│   │   │   ├── +layout.server.ts       # Chargement côté serveur
│   │   │   └── +layout.ts              # Chargement client
│   │   └── +layout.svelte              # Layout racine (ThemeProvider)
│   ├── app.css                         # Styles globaux Tailwind
│   ├── app.d.ts                        # Types TypeScript globaux
│   ├── app.html                        # Template HTML
│   ├── hooks.server.ts                 # Hooks serveur SvelteKit
│   └── hooks.ts                        # Hooks client SvelteKit
├── static/
│   ├── bercyhub_logo.png              # Logo
│   └── fonts/                          # Fonts Geist
├── .env                                # Variables d'environnement
├── package.json                        # Dépendances npm
├── svelte.config.js                    # Config SvelteKit
├── tailwind.config.ts                  # Config Tailwind CSS
├── tsconfig.json                       # Config TypeScript
└── vite.config.ts                      # Config Vite

```

## 🛠️ Scripts disponibles

```bash
npm run dev          # Démarrer le serveur de développement
npm run dev-host     # Démarrer en mode réseau (accessible depuis d'autres machines)
npm run build        # Build de production
npm run preview      # Prévisualiser le build de production
npm run check        # Vérifier les erreurs TypeScript et Svelte
npm run lint         # Linter le code
npm run format       # Formater le code avec Prettier
```

## 🔌 Intégration dans Grist

### Comment ça marche

Ce widget est conçu pour être intégré comme **Custom Widget** dans Grist :

1. Le widget appelle automatiquement `grist.ready({ requiredAccess: 'full' })`
2. Grist affiche une demande de permission à l'utilisateur
3. Une fois accepté, le widget récupère automatiquement :
    - Un **token d'accès** via `grist.docApi.getAccessToken()`
    - L'**ID du document** via `grist.docApi.getDocName()`
    - L'**ID de la table** actuellement visualisée via `grist.getTable().getTableId()`
    - Le **nom de la table** depuis `_grist_Tables`
4. Ces informations sont envoyées automatiquement à chaque requête au backend

**Aucune configuration manuelle requise !** 🎉

### Contexte transmis au backend

Le widget transmet automatiquement le contexte de visualisation :

```typescript
{
  documentId: "doc-abc123",           // Document Grist actuel
  currentTableId: "Clients",          // Table actuellement affichée
  currentTableName: "Clients"         // Nom lisible de la table
}
```

**Avantage** : L'IA privilégie automatiquement la table que vous visualisez, rendant les interactions plus naturelles :

- ❌ Avant : "Montre-moi les clients de la table Clients"
- ✅ Maintenant : "Montre-moi les clients" (la table Clients est déjà dans le contexte)

### Ajouter le widget dans Grist

1. Ouvrir votre document Grist
2. Ajouter une nouvelle page ou section
3. Cliquer "Add Widget" → "Custom Widget"
4. Entrer l'URL du widget (ex: `http://localhost:5173`)
5. Accepter "Full document access" quand demandé
6. C'est prêt ! 🚀

### Permissions requises

Le widget demande l'accès `full` pour :

- Lire les schémas et données des tables
- Exécuter des requêtes SQL via l'API Grist
- Fournir une analyse de données par l'IA

## 💾 Persistance des conversations

Les conversations sont automatiquement sauvegardées dans le `localStorage` du navigateur avec une clé unique par document et table :

```
grist-chat-{documentId}-{tableId}              # Messages
grist-chat-metadata-{documentId}-{tableId}     # Métadonnées (SQL, etc.)
grist-chat-confirmation-{documentId}-{tableId} # Confirmations en attente
```

### Avantages

- ✅ Conversations restaurées automatiquement après rechargement
- ✅ **Confirmations persistantes** : Même si vous changez de table et revenez, la confirmation est toujours affichée
- ✅ Isolation par document et table
- ✅ Pas de base de données externe nécessaire

### Limite de messages

Par défaut, la conversation est limitée à **20 messages** pour optimiser le contexte de l'IA. Un avertissement s'affiche à 80% de la limite.

Pour réinitialiser : cliquez sur le bouton 🔄 dans le header.

## ✅ Système de confirmation

Pour les opérations destructives (suppressions, modifications massives), le widget affiche un composant de confirmation élégant :

### Workflow de confirmation

1. **Détection automatique** : Le backend détecte les opérations nécessitant confirmation
2. **Aperçu détaillé** : Affichage du nombre d'éléments affectés, avertissements
3. **Confirmation utilisateur** : Composant sous le message de l'assistant
4. **Exécution** : Appel à `/api/v1/chat/confirm` avec la décision

### Design

- 🎨 **Minimaliste** : Design sobre avec couleurs zinc adaptées au chatbot
- 🌓 **Dark mode** : Support automatique du mode sombre
- 📍 **Position contextuelle** : Affichée directement sous le message concerné (pas en bas de page)
- 💾 **Persistante** : Survit aux rechargements et changements de table

### Opérations confirmables

- 🗑️ **Suppressions** :
    - Suppression d'enregistrements
    - Suppression de colonnes (avec aperçu des données affectées)

- ✏️ **Modifications massives** :
    - Modification de plus de 10 enregistrements
    - Changement de type de colonne avec perte potentielle de données

## 🔧 Configuration

### Variables d'environnement

```env
# URL de l'API backend Python
PUBLIC_CHAT_URL='http://localhost:8000/chat'
```

### Backend API

Le frontend communique avec une API Python (voir projet `grist-api-v2`).

#### 📤 Endpoint Principal : `POST /api/v1/chat`

**Headers requis** :

```
X-API-Key: <grist-widget-token>
Content-Type: application/json
```

**Structure de la requête** :

```typescript
{
  // Messages de la conversation (format AI SDK)
  messages: [
    {
      id: string,              // ID unique du message
      role: "user" | "assistant",
      parts: [                 // Parties du message (texte, images...)
        {
          type: "text",
          text: string
        }
      ],
      createdAt: string        // ISO timestamp
    }
  ],

  // Contexte du document
  documentId: string,          // ID/nom du document Grist
  currentTableId?: string,     // ID de la table actuellement visualisée
  currentTableName?: string,   // Nom de la table actuellement visualisée

  // Métadonnées (optionnelles)
  executionMode?: string,
  webhookUrl?: string
}
```

**Structure de la réponse** :

```typescript
{
  // Réponse de l'assistant
  response?: string,                    // Texte de réponse (peut être null si confirmation requise)

  // Métadonnées de l'exécution
  sql_query?: string,                   // Requête SQL exécutée (si applicable)
  agent_used?: string,                  // Modèle LLM utilisé
  data_analyzed?: any,                  // Données analysées

  // Outils appelés
  tool_calls?: [
    {
      tool_name: string,                // Nom de l'outil (ex: "get_tables")
      tool_input: object,               // Arguments passés à l'outil
      tool_output: any                  // Résultat de l'outil
    }
  ],

  // Gestion d'erreur
  error?: string,                       // Message d'erreur si échec

  // Système de confirmation
  requires_confirmation?: boolean,      // true si confirmation utilisateur requise
  confirmation_request?: {              // Détails de la confirmation demandée
    confirmation_id: string,
    tool_name: string,
    tool_args: object,
    preview: {
      operation_type: string,           // "DELETE_RECORDS" | "DELETE_COLUMN" | etc.
      description: string,              // Description en français
      affected_count: number,           // Nombre d'éléments affectés
      affected_items: any[],            // Aperçu des éléments
      warnings: string[],               // Avertissements
      is_reversible: boolean
    }
  }
}
```

#### 📥 Endpoint de Confirmation : `POST /api/v1/chat/confirm`

Utilisé pour approuver/rejeter une opération destructive.

**Structure de la requête** :

```typescript
{
  confirmation_id: string,     // ID de la confirmation (reçu dans confirmation_request)
  approved: boolean,           // true = approuver, false = rejeter
  reason?: string              // Raison du rejet (optionnel)
}
```

**Structure de la réponse** :

```typescript
{
  status: "approved" | "rejected",
  result?: any,                // Résultat de l'opération si approuvée
  message?: string
}
```

## 🎨 Technologies utilisées

- **Framework** : [SvelteKit](https://kit.svelte.dev/) 2.x avec Svelte 5
- **Langage** : TypeScript
- **Styling** : TailwindCSS
- **UI Components** : bits-ui, lucide-svelte
- **Chat SDK** : [@ai-sdk/svelte](https://sdk.vercel.ai/docs)
- **Toast Notifications** : svelte-sonner
- **Markdown** : svelte-exmarkdown

## 📦 Dépendances principales

```json
{
	"@ai-sdk/svelte": "^2.1.0",
	"@sveltejs/kit": "^2.16.0",
	"svelte": "^5.20.2",
	"tailwindcss": "^3.4.17",
	"lucide-svelte": "^0.475.0",
	"svelte-sonner": "^0.3.28"
}
```

## 🐛 Debugging

### Inspecter le localStorage

```javascript
// Console du navigateur
// Voir toutes les conversations sauvegardées
Object.keys(localStorage).filter((k) => k.startsWith('grist-chat-'));

// Voir une conversation spécifique
JSON.parse(localStorage.getItem('grist-chat-{docId}-{tableId}'));

// Effacer toutes les conversations
Object.keys(localStorage)
	.filter((k) => k.startsWith('grist-chat-'))
	.forEach((k) => localStorage.removeItem(k));
```

### Problèmes courants

**Le widget ne se charge pas**

- Vérifiez que le backend Python tourne sur le bon port
- Vérifiez la variable `PUBLIC_CHAT_URL` dans `.env`
- Vérifiez que "Full document access" est activé dans Grist

**Erreur 500**

- Vérifiez les logs du serveur frontend
- Vérifiez que le backend API est accessible

**Les messages ne sont pas sauvegardés**

- Vérifiez que le localStorage n'est pas plein (limite ~5-10MB)
- Ouvrez la console et cherchez des erreurs

**Made with ❤️ for Grist**
