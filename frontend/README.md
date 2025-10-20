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

## 📁 Structure

```
frontend/
├── src/lib/components/    # Composants Svelte (chat, messages, etc.)
├── src/routes/            # Pages SvelteKit
└── static/                # Assets statiques
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

### Ajouter le widget

1. Ouvrir votre document Grist
2. Ajouter "Custom Widget"
3. Entrer l'URL du widget (ex: `http://localhost:5173`)
4. Accepter "Full document access"

Le widget récupère automatiquement le token d'accès et le contexte (document, table) pour transmettre à l'API backend.

## 💾 Persistance

Les conversations sont sauvegardées dans `localStorage` par document/table :
- Conversations restaurées automatiquement
- Limite de 20 messages (réinitialiser avec 🔄)

## ✅ Système de confirmation

Pour les opérations destructives (suppressions, modifications massives) :
- Aperçu des éléments affectés
- Confirmation utilisateur requise
- Persistante même après rechargement

## 🔧 Configuration

```env
# .env
PUBLIC_CHAT_URL='http://localhost:8000/api/v1/chat'
```

**Note** : Le frontend communique avec l'API backend via ce endpoint. Voir [backend README](../backend/README.md) pour les détails de l'API.

## 🎨 Technologies

- **Framework** : SvelteKit 2.x + Svelte 5
- **Langage** : TypeScript
- **Styling** : TailwindCSS
- **UI** : bits-ui, lucide-svelte
- **Chat SDK** : @ai-sdk/svelte
