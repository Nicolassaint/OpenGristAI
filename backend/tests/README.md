# Guide des Tests

Documentation pour exécuter et écrire des tests dans OpenGristAI.

## 🚀 Quick Start

```bash
# Installer les dépendances
cd backend && pip install -r requirements.txt

# Lancer tous les tests
make test-backend

# Tests spécifiques
make test-unit          # Tests unitaires seulement
make test-integration   # Tests d'intégration
```

## 📁 Structure

```
tests/
├── conftest.py          # Fixtures partagées (mock_grist_service, etc.)
├── unit/                # Tests unitaires (rapides, mocked)
└── integration/         # Tests d'intégration (workflows complets)
```

## ⚡ Commandes Principales

```bash
# Via Makefile (recommandé)
make test-backend       # Tous les tests mocked
make test-unit          # Tests unitaires
make test-integration   # Tests d'intégration
make test-coverage      # Avec rapport de couverture

# Directement avec pytest
pytest                              # Tous les tests
pytest -v                           # Verbose
pytest -m unit                      # Tests unitaires seulement
pytest tests/unit/test_tools.py     # Fichier spécifique
pytest --cov=app --cov-report=html  # Coverage
```

## 🏷️ Types de Tests

| Marker | Description | Vitesse | Besoin API |
|--------|-------------|---------|------------|
| `@pytest.mark.unit` | Tests unitaires isolés | ⚡ Très rapide | ❌ Non |
| `@pytest.mark.integration` | Workflows complets (mocked) | 🏃 Rapide | ❌ Non |
| `@pytest.mark.requires_api` | Tests avec vraie API Grist | 🐢 Lent | ✅ Oui |

## 🔌 Tests avec API Réelle (Optionnel)

Pour tester avec une vraie connexion Grist :

```bash
# 1. Configuration
export GRIST_API_KEY="votre_clé"
export GRIST_DOCUMENT_ID="votre_doc_id"

# 2. Lancer les tests
pytest -m requires_api
```

⚠️ **Attention** : Crée des données temporaires dans votre document

## 🛠️ Fixtures Principales

Définies dans `conftest.py`, utilisables directement :

```python
@pytest.mark.unit
async def test_example(mock_grist_service, sample_tables):
    # mock_grist_service : Service Grist mocké
    # sample_tables : Données de test prédéfinies
    tables = await mock_grist_service.get_tables()
    assert len(tables) == 3
```

**Fixtures disponibles** :
- `mock_grist_service` - Service Grist mocké complet
- `sample_tables`, `sample_columns`, `sample_records` - Données de test
- `api_client` - Client FastAPI pour tests d'API

## 📝 Écrire un Nouveau Test

```python
import pytest

@pytest.mark.unit  # ou @pytest.mark.integration
@pytest.mark.asyncio
class TestMyFeature:
    async def test_my_function(self, mock_grist_service):
        """Test de ma fonctionnalité."""
        result = await my_function()
        assert result == expected
```

## 🐛 Debugging

```bash
pytest -x          # Stop au premier échec
pytest --lf        # Relancer seulement les tests qui ont échoué
pytest --pdb       # Debugger interactif
pytest -s          # Voir les prints
```

## 💡 Bonnes Pratiques

- ✅ Utiliser les fixtures existantes du `conftest.py`
- ✅ Ajouter le bon marker (`@pytest.mark.unit` ou `integration`)
- ✅ Tests rapides par défaut (mocks)
- ❌ Ne pas hardcoder de credentials
- ❌ Ne pas créer de mocks custom inutiles

