# Contributing to OpenGristAI

🎉 Merci de votre intérêt pour contribuer à OpenGristAI !

## Table des Matières

- [Code of Conduct](#code-of-conduct)
- [Comment Contribuer](#comment-contribuer)
- [Développement Local](#développement-local)
- [Guidelines](#guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

Ce projet suit le [Contributor Covenant](https://www.contributor-covenant.org/). En participant, vous acceptez de respecter ce code de conduite.

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

### Setup

```bash
# Fork et clone
git clone https://github.com/nicolassaint/OpenGristAI.git
cd OpenGristAI

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Copier et configurer .env
cp .env.example .env
# Éditer .env avec vos clés API
```

### Lancer les Tests

```bash
# Tous les tests
pytest

# Avec couverture
pytest --cov=app tests/

# Tests spécifiques
pytest tests/unit/test_agent.py -v

# Avec logs détaillés
pytest -vv --log-cli-level=DEBUG
```

### Code Quality

```bash
# Formater le code
black app/ tests/

# Linter
ruff app/ tests/

# Type checking
mypy app/

# Tout en une fois
black app/ tests/ && ruff app/ tests/ && mypy app/ && pytest
```

## Guidelines

### Style de Code

- **Python** : Suivre [PEP 8](https://pep8.org/)
- **Formatage** : Utiliser `black` (ligne de 88 caractères)
- **Linting** : Passer `ruff` sans erreurs
- **Types** : Ajouter des type hints (vérifier avec `mypy`)
- **Docstrings** : Format Google style

### Exemple de Docstring

```python
def my_function(param1: str, param2: int) -> dict:
    """
    Brief description of function.

    Longer description if needed, explaining what the function does,
    when to use it, etc.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative

    Example:
        >>> my_function("hello", 42)
        {"result": "hello 42"}
    """
    ...
```

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

- **Couverture** : Viser > 80%
- **Tests unitaires** : Pour logique métier isolée
- **Tests d'intégration** : Pour workflows complets
- **Fixtures** : Utiliser pytest fixtures pour setup/teardown
- **Mocks** : Mocker les appels API externes (Grist, OpenAI)

**Exemple** :
```python
import pytest
from app.core.agent import GristAgent

@pytest.fixture
def mock_grist_service(mocker):
    """Mock GristService for testing."""
    service = mocker.Mock()
    service.get_tables.return_value = [
        {"id": "Table1", "label": "Table 1"}
    ]
    return service

def test_agent_initialization(mock_grist_service):
    """Test that agent initializes correctly."""
    agent = GristAgent(
        document_id="test-doc",
        grist_token="test-token"
    )
    assert agent.document_id == "test-doc"
    assert len(agent.tools) == 13
```

## Pull Request Process

### Avant de Soumettre

1. ✅ Tous les tests passent
2. ✅ Code formaté avec `black`
3. ✅ Pas d'erreurs `ruff` ou `mypy`
4. ✅ Couverture de tests maintenue ou améliorée
5. ✅ Documentation mise à jour si nécessaire
6. ✅ CHANGELOG.md mis à jour (section [Unreleased])

### Créer la PR

1. **Fork** le repo
2. **Créer une branche** depuis `main` :
   ```bash
   git checkout -b feat/my-feature
   ```
3. **Commit** vos changements
4. **Push** vers votre fork
5. **Ouvrir une PR** sur `main`

### Description de la PR

Template :
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG updated
```

### Review Process

1. **CI checks** doivent passer (tests, linting)
2. **Review** par au moins 1 maintainer
3. **Feedback** : Répondre aux commentaires
4. **Merge** : Par un maintainer une fois approuvée

## Questions ?

- 💬 [Discussions](https://github.com/your-org/OpenGristAI/discussions)
- 🐛 [Issues](https://github.com/your-org/OpenGristAI/issues)
- 📧 Email : nicolas.saint78@gmail.com

---

Merci de contribuer à OpenGristAI ! 🚀

