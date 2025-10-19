# OpenGristAI Documentation

Documentation complète pour OpenGristAI - API d'agent IA pour Grist.

## 📚 Documentation Disponible

### Architecture et Conception

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Architecture globale du système
  - Structure des modules
  - Flux de données
  - Choix techniques
  
- **[PHASE2.md](./PHASE2.md)** - Détails de la Phase 2
  - Système de confirmation
  - Nouveaux outils (table/column management)
  - Validation des données

### Intégration et Utilisation

- **[INTEGRATION.md](./INTEGRATION.md)** - Guide d'intégration
  - Intégration avec Grist
  - Configuration du widget custom
  - Authentification

### Diagnostics et Troubleshooting

- **[FUNCTION_CALLING_DIAGNOSTICS.md](./FUNCTION_CALLING_DIAGNOSTICS.md)** - Diagnostics du Function Calling
  - Validation de compatibilité LLM
  - Logging détaillé
  - Métriques et monitoring
  - Troubleshooting des problèmes courants
  - Compatibilité des différents providers

## 🚀 Quick Start

### Pour commencer rapidement

1. **Installation** : Voir le [README principal](../README.md)
2. **Configuration** : Copier `.env.example` vers `.env`
3. **Architecture** : Lire [ARCHITECTURE.md](./ARCHITECTURE.md)
4. **Intégration** : Suivre [INTEGRATION.md](./INTEGRATION.md)

### Pour tester un nouveau modèle LLM

1. **Configurer** le modèle dans `.env`
2. **Tester** avec le script de validation :
   ```bash
   python tests/test_function_calling_validation.py
   ```
3. **Lire** [FUNCTION_CALLING_DIAGNOSTICS.md](./FUNCTION_CALLING_DIAGNOSTICS.md) pour interpréter les résultats

## 🔧 Développement

### Structure du Code

```
app/
├── api/          # Endpoints FastAPI
├── core/         # Agent, LLM, tools, prompts
├── models/       # Modèles Pydantic
├── services/     # Services métier (Grist, confirmation, etc.)
└── middleware/   # Error handling, exceptions
```

### Tests

```bash
# Tests unitaires
pytest tests/unit/

# Tests d'intégration
pytest tests/integration/

# Test de validation LLM
python tests/test_function_calling_validation.py
```

## 📖 Guides par Cas d'Usage

### Je veux intégrer OpenGristAI dans mon Grist

→ Lire [INTEGRATION.md](./INTEGRATION.md)

### Je veux comprendre comment ça marche

→ Lire [ARCHITECTURE.md](./ARCHITECTURE.md)

### Je veux utiliser un autre modèle LLM (Mistral, Claude, etc.)

→ Lire [FUNCTION_CALLING_DIAGNOSTICS.md](./FUNCTION_CALLING_DIAGNOSTICS.md)

### Je veux développer de nouveaux outils

→ Lire [ARCHITECTURE.md](./ARCHITECTURE.md) section "Tools"

### J'ai des problèmes / bugs

1. Vérifier les logs de l'application
2. Activer le mode debug : `export AGENT_VERBOSE=true`
3. Lire [FUNCTION_CALLING_DIAGNOSTICS.md](./FUNCTION_CALLING_DIAGNOSTICS.md) section "Troubleshooting"

## 🤝 Contribution

Pour contribuer :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/ma-feature`)
3. Lire [CONTRIBUTING.md](../CONTRIBUTING.md)
4. Faire vos modifications avec des tests
5. Soumettre une Pull Request

## 📝 Changelog

Voir [CHANGELOG.md](../CHANGELOG.md) pour l'historique des versions.

## 📄 License

Ce projet est sous licence MIT. Voir [LICENSE](../LICENSE).

---

**Projet** : OpenGristAI  
**Version** : 0.2.0  
**Dernière mise à jour** : 2025-01-19

