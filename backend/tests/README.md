# OpenGristAI - Guide des Tests

Ce guide explique comment exécuter les tests de l'application OpenGristAI.

## Table des Matières

- [Structure des Tests](#structure-des-tests)
- [Installation](#installation)
- [Exécution des Tests](#exécution-des-tests)
- [Types de Tests](#types-de-tests)
- [Tests avec API Réelle](#tests-avec-api-réelle)
- [Configuration](#configuration)

## Structure des Tests

```
tests/
├── conftest.py              # Fixtures et configuration partagées
├── pytest.ini               # Configuration pytest
├── unit/                    # Tests unitaires (mocked)
│   ├── test_agent.py
│   ├── test_grist_service.py
│   ├── test_tools.py
│   ├── test_models.py
│   ├── test_preview_service.py
│   ├── test_validation.py
│   └── test_confirmation_service.py
└── integration/             # Tests d'intégration
    ├── test_agent_workflows.py
    ├── test_api_endpoints.py
    └── test_all_tools.py
```

## Installation

Installez les dépendances de test :

```bash
cd backend
pip install -r requirements.txt
```

## Exécution des Tests

### Tous les tests (mocked uniquement)

```bash
pytest
```

### Tests unitaires seulement

```bash
pytest -m unit
```

### Tests d'intégration seulement

```bash
pytest -m integration
```

### Tests d'un fichier spécifique

```bash
pytest tests/unit/test_grist_service.py
```

### Tests avec verbosité

```bash
pytest -v
pytest -vv  # Plus de détails
```

### Tests avec coverage

```bash
pytest --cov=app --cov-report=html
# Ouvre htmlcov/index.html pour voir le rapport
```

## Types de Tests

### Tests Unitaires (`@pytest.mark.unit`)

Tests rapides avec des mocks, sans dépendances externes :

```python
@pytest.mark.unit
class TestGristService:
    async def test_get_tables(self, mock_grist_service):
        tables = await mock_grist_service.get_tables()
        assert len(tables) == 3
```

**Avantages :**
- ⚡ Très rapides
- 🔒 Pas besoin de credentials API
- 🧪 Isolés et reproductibles
- 🚀 Peuvent tourner en CI/CD

### Tests d'Intégration (`@pytest.mark.integration`)

Tests avec des composants réels mais toujours mockés :

```python
@pytest.mark.integration
@pytest.mark.asyncio
class TestAgentWorkflows:
    async def test_workflow_list_tables(self, agent_with_mocks):
        result = await agent_with_mocks.run("What tables are in this document?")
        assert result["success"] is True
```

### Tests avec API Réelle (`@pytest.mark.requires_api`)

Tests nécessitant une vraie connexion à Grist :

```python
@pytest.mark.requires_api
@pytest.mark.integration
class TestAllToolsRealAPI:
    async def test_real_get_tables(self, real_grist_service):
        result = await get_tables.ainvoke({})
        assert isinstance(result, list)
```

## Tests avec API Réelle

### Configuration

Pour exécuter les tests avec une vraie API Grist, configurez les variables d'environnement :

```bash
# Créez un fichier .env dans backend/
GRIST_API_KEY=votre_clé_api_ici
GRIST_DOCUMENT_ID=votre_document_id_ici  # Optionnel
GRIST_BASE_URL=https://grist.numerique.gouv.fr  # Optionnel
```

### Obtenir une API Key Grist

1. Connectez-vous à votre instance Grist
2. Allez dans **Account Settings** (Paramètres du compte)
3. Section **API** → Créez une nouvelle clé
4. Copiez la clé dans votre `.env`

### Exécution

```bash
# Exécuter seulement les tests avec API réelle
pytest -m requires_api

# Exécuter un test spécifique avec API réelle
pytest tests/integration/test_all_tools.py::TestAllToolsRealAPI::test_real_get_tables -m requires_api

# Avec verbosité pour voir les détails
pytest -m requires_api -v
```

### ⚠️ Avertissement

Les tests avec API réelle :
- Créent des données temporaires dans votre document Grist
- Une table `TestToolsTable` sera créée
- **Cette table ne peut PAS être supprimée automatiquement** (limitation API Grist)
- Vous devez la supprimer manuellement via l'interface Grist

## Configuration

### Fixtures Disponibles

Toutes définies dans `conftest.py` :

#### Configuration
- `test_settings` - Configuration de test avec valeurs par défaut

#### Données de Test
- `sample_tables` - Exemples de tables Grist
- `sample_columns` - Exemples de colonnes
- `sample_records` - Exemples d'enregistrements

#### Mocks
- `mock_grist_client` - Client API mocké
- `mock_grist_service` - Service Grist mocké
- `mock_llm` - LLM LangChain mocké

#### API Tests
- `api_client` - Client FastAPI pour tests
- `sample_chat_request` - Requête chat exemple
- `sample_headers` - Headers HTTP exemple

### Markers Pytest

Définis dans `pytest.ini` :

- `@pytest.mark.unit` - Tests unitaires
- `@pytest.mark.integration` - Tests d'intégration
- `@pytest.mark.slow` - Tests lents
- `@pytest.mark.requires_api` - Tests nécessitant API réelle

### Utilisation des Fixtures

```python
@pytest.mark.unit
@pytest.mark.asyncio
class TestMyFeature:
    async def test_something(self, mock_grist_service, sample_tables):
        """Test utilisant les fixtures."""
        tables = await mock_grist_service.get_tables()
        assert len(tables) == len(sample_tables)
```

## Bonnes Pratiques

### ✅ À Faire

1. **Utiliser les fixtures** du `conftest.py`
2. **Marquer les tests** avec les bons decorators
3. **Tester avec mocks** par défaut
4. **Nettoyer** après les tests
5. **Documenter** les cas de test complexes

### ❌ À Éviter

1. ❌ Hardcoder des credentials dans les tests
2. ❌ Créer des mocks custom quand une fixture existe
3. ❌ Laisser des données résiduelles
4. ❌ Tests avec side effects non documentés
5. ❌ Tests trop longs ou trop lents sans marker `@pytest.mark.slow`

## Debugging

### Voir les logs complets

```bash
pytest --log-cli-level=DEBUG
```

### Arrêter au premier échec

```bash
pytest -x
```

### Exécuter seulement les tests qui ont échoué

```bash
pytest --lf  # Last failed
```

### Mode debug avec pdb

```bash
pytest --pdb
```

### Voir les prints dans les tests

```bash
pytest -s
```

## CI/CD

Les tests sont automatiquement exécutés dans la CI. Seuls les tests mocked (sans `@pytest.mark.requires_api`) tournent automatiquement.

Pour inclure les tests API réels dans la CI, configurez les secrets :
- `GRIST_API_KEY`
- `GRIST_DOCUMENT_ID`
- `GRIST_BASE_URL`

## Contribuer

Lors de l'ajout de nouveaux tests :

1. Suivez la structure existante
2. Utilisez les fixtures partagées
3. Ajoutez les markers appropriés
4. Documentez les cas complexes
5. Assurez-vous que les tests passent : `pytest`

## Exemples

### Test Unitaire Simple

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_tables(mock_grist_service, sample_tables):
    """Test simple avec mock."""
    tables = await mock_grist_service.get_tables()
    assert len(tables) == 3
    assert tables[0]["id"] == "Students"
```

### Test d'Intégration

```python
@pytest.mark.integration
@pytest.mark.asyncio
class TestWorkflow:
    async def test_complete_workflow(self, agent_with_mocks):
        """Test workflow complet."""
        result = await agent_with_mocks.run("Add a student")
        assert result["success"] is True
```

### Test avec API Réelle

```python
@pytest.mark.requires_api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api(real_grist_service):
    """Test avec vraie API."""
    tables = await real_grist_service.get_tables()
    assert isinstance(tables, list)
```

## Support

Pour toute question sur les tests :
- Consultez la documentation : `docs/`
- Ouvrez une issue sur GitHub
- Contactez l'équipe de développement

