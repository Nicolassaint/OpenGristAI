# Contributing to OpenGristAI

🎉 Merci de votre intérêt pour contribuer à OpenGristAI !

## Comment Contribuer

### 🐛 Signaler un Bug

1. Vérifier que le bug n'a pas déjà été signalé dans [Issues](https://github.com/your-org/OpenGristAI/issues)
2. Créer une issue avec le template "Bug Report"
3. Inclure :
   - Description claire du problème
   - Étapes pour reproduire
   - Comportement attendu vs comportement observé
   - Version de Python, OS, etc.
   - Logs pertinents

### 💡 Proposer une Fonctionnalité

1. Vérifier que la fonctionnalité n'est pas déjà proposée
2. Créer une issue avec le template "Feature Request"
3. Décrire :
   - Le cas d'usage
   - La solution proposée
   - Les alternatives considérées

### 📝 Améliorer la Documentation

- Corrections de typos : PR directe bienvenue
- Améliorations majeures : Créer une issue d'abord pour discuter

## Développement Local

```bash
# Fork et clone
git clone https://github.com/nicolassaint/OpenGristAI.git
cd OpenGristAI

# Installation (voir README.md)
make install

# Lancer les tests
make test-backend
make test-frontend

# Qualité du code
make lint-backend
make format-backend
```

## Guidelines

### Style de Code

- **Python** : PEP 8, formatage avec `black`, linting avec `ruff`
- **Types** : Ajouter des type hints
- **Docstrings** : Format Google style

### Commit Messages

Format : `<type>(<scope>): <description>`

**Types** :
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation uniquement
- `style`: Formatage, typos
- `refactor`: Refactoring (pas de changement fonctionnel)
- `test`: Ajout/modification de tests
- `chore`: Maintenance, dépendances

**Exemples** :
```
feat(tools): add remove_table tool
fix(agent): handle timeout errors correctly
docs(readme): update installation instructions
test(integration): add tests for confirmation workflow
```

### Tests

- Couverture > 80%
- Tests unitaires + intégration
- Utiliser fixtures du `conftest.py`
- Voir [tests/README.md](backend/tests/README.md) pour détails

## Pull Request Process

### Checklist

1. ✅ Tous les tests passent
2. ✅ Code formaté (`black`, `ruff`)
3. ✅ Documentation à jour
4. ✅ CHANGELOG.md mis à jour

### Workflow

1. Fork le repo
2. Créer une branche (`git checkout -b feat/my-feature`)
3. Commit et push
4. Ouvrir une PR sur `main`
5. Attendre review d'un maintainer

## Questions ?

- 💬 [Discussions](https://github.com/nicolassaint/OpenGristAI/discussions)
- 🐛 [Issues](https://github.com/nicolassaint/OpenGristAI/issues)
- 📧 Email : nicolas.saint78@gmail.com

---

Merci de contribuer à OpenGristAI ! 🚀

