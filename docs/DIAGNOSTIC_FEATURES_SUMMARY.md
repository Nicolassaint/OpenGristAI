# Résumé des Fonctionnalités de Diagnostic

## 🎯 Problème Résolu

**Avant** : Lorsqu'un modèle LLM ne supportait pas correctement le function calling, l'application échouait silencieusement sans indication claire du problème.

**Maintenant** : Le système détecte automatiquement les problèmes de compatibilité et fournit des diagnostics détaillés avec des recommandations.

## 📦 Nouveautés

### 1. Logging Détaillé dans `agent.py`

#### Ce qui est loggé maintenant :

```python
# Pour chaque itération
- Type de réponse LLM (AIMessage, etc.)
- Présence de l'attribut tool_calls
- Valeur et type de tool_calls
- Nombre de tool calls demandés

# Pour chaque tool call
- Nom du tool
- Arguments
- ID du call
- Résultat (tronqué si long)
- Succès/échec avec émojis visuels

# Détection automatique de problèmes
- Pas de tool calls pendant 3+ itérations
- Liste tool_calls vide
- Taux d'échec élevé (>50%)
- Max iterations atteint
```

#### Métriques Retournées

Chaque appel à `agent.run()` retourne maintenant :

```python
{
    "output": "...",
    "success": True,
    "intermediate_steps": [...],
    "metrics": {
        "iterations": 2,
        "tool_calls": 5,
        "failed_tool_calls": 0,
        "iterations_without_tools": 0  # Si max iterations atteint
    }
}
```

### 2. Validation de Function Calling dans `llm.py`

#### Nouvelle fonction : `validate_function_calling()`

Test automatique avec un tool simple pour vérifier :
- Le modèle supporte-t-il `bind_tools()` ?
- La réponse contient-elle un attribut `tool_calls` ?
- Le modèle génère-t-il réellement des tool calls ?

```python
result = await validate_function_calling(llm, "gpt-4")
# Returns:
# {
#     "supported": True,
#     "has_tool_calls_attr": True,
#     "test_passed": True,
#     "response_type": "AIMessage",
#     "num_tool_calls": 1
# }
```

### 3. Méthode de Validation dans `GristAgent`

#### Usage manuel

```python
agent = GristAgent(...)
result = await agent.validate_function_calling()

if result["test_passed"]:
    print("✅ Modèle compatible")
else:
    print("❌ Problème détecté")
```

#### Usage automatique

```python
agent = GristAgent(
    ...,
    validate_function_calling_on_init=True  # Valide au premier run()
)
```

### 4. Détection de Patterns de Problèmes

Le système détecte automatiquement :

| Pattern | Symptôme | Action |
|---------|----------|--------|
| **Pas de support** | 0 tool calls, pas d'attribut tool_calls | ERROR avec recommandations de modèles |
| **Support partiel** | tool_calls parfois vide | WARNING de vigilance |
| **Haute défaillance** | >50% d'échecs | ERROR avec diagnostic |
| **Boucle infinie** | Max iterations atteint | WARNING avec métriques |

## 📁 Fichiers Modifiés

### Core
- ✅ `app/core/agent.py` - Logging détaillé + métriques + détection de problèmes
- ✅ `app/core/llm.py` - Fonction de validation

### Documentation
- ✅ `docs/FUNCTION_CALLING_DIAGNOSTICS.md` - Guide complet
- ✅ `docs/README.md` - Index de la documentation
- ✅ `docs/DIAGNOSTIC_FEATURES_SUMMARY.md` - Ce fichier
- ✅ `CHANGELOG.md` - Mis à jour

### Tests & Exemples
- ✅ `tests/test_function_calling_validation.py` - Script de test
- ✅ `examples/test_diagnostics.py` - Exemples d'utilisation

## 🚀 Comment Utiliser

### Scénario 1 : Tester un nouveau modèle

```bash
# 1. Configurer le modèle
export OPENAI_MODEL=mistral-large-latest
export OPENAI_BASE_URL=https://api.mistral.ai/v1
export OPENAI_API_KEY=your_key

# 2. Tester
python tests/test_function_calling_validation.py

# 3. Interpréter les résultats
# ✅ PASSED = Compatible
# ⚠️  UNCERTAIN = À tester en profondeur
# ❌ FAILED = Non compatible
```

### Scénario 2 : Debugging d'un problème

```bash
# 1. Activer les logs détaillés
export AGENT_VERBOSE=true

# 2. Logger niveau DEBUG
export LOG_LEVEL=DEBUG

# 3. Lancer l'application
python -m app.api.main

# 4. Faire une requête et examiner les logs
# Regarder pour :
# - "tool_calls attribute type"
# - "Number of tool calls"
# - "⚠️" et "🔴" warnings/errors
```

### Scénario 3 : Monitoring en production

```python
# Dans votre code
result = await agent.run(user_message)

# Logger les métriques
logger.info(
    "Request completed",
    extra={
        "tool_calls": result["metrics"]["tool_calls"],
        "failed_calls": result["metrics"]["failed_tool_calls"],
        "iterations": result["metrics"]["iterations"],
    }
)

# Alerter si problème
if result["metrics"]["failed_tool_calls"] > 0:
    alert_team("Agent having issues", result["metrics"])
```

## 🔍 Exemples de Logs

### Cas Normal (Tout fonctionne)

```
INFO: ✓ LLM requested 2 tool call(s) - function calling working correctly
DEBUG: --- Tool Call 1/2 ---
DEBUG: Tool: get_tables
INFO: ✅ Tool 'get_tables' executed successfully
INFO: ✅ Agent execution completed successfully
INFO: 📊 Execution Summary:
INFO:    - Total iterations: 2/10
INFO:    - Total tool calls: 2
INFO:    - Failed tool calls: 0
INFO:    - Success rate: 100.0%
```

### Cas Problématique (Modèle incompatible)

```
DEBUG: LLM Response Type: AIMessage
DEBUG: Response has 'content': True
DEBUG: Response has 'tool_calls': False
WARNING: ⚠️  LLM response has no 'tool_calls' attribute.
WARNING: This model may not support function calling.
ERROR: 🔴 FUNCTION CALLING FAILURE: No tool calls for 3 consecutive iterations.
ERROR: This strongly suggests the LLM (llama-2-7b) doesn't properly support function calling.
ERROR: Consider using a different model (e.g., gpt-4, gpt-3.5-turbo, claude-3-sonnet, mistral-large-latest).
```

## 🎓 Ce que Vous Apprenez

Avec ces logs, vous pouvez maintenant diagnostiquer :

1. **Le modèle ne supporte pas function calling**
   - Symptôme : Pas d'attribut `tool_calls`
   - Log : "LLM response has no 'tool_calls' attribute"

2. **Le modèle supporte mais ne l'utilise pas**
   - Symptôme : Attribut présent mais liste vide
   - Log : "LLM returned empty tool_calls list"

3. **Les tools échouent**
   - Symptôme : Taux d'échec élevé
   - Log : "❌ Tool 'xxx' failed" + stack trace

4. **Le modèle boucle**
   - Symptôme : Max iterations atteint
   - Log : Voir les tool calls répétés

## 📊 Compatibilité Testée

| Provider | Modèle | Status | Notes |
|----------|--------|--------|-------|
| OpenAI | gpt-4 | ✅ | Référence |
| OpenAI | gpt-3.5-turbo | ✅ | Bon |
| Mistral | mistral-large | ✅ | Compatible |
| Mistral | mistral-small | ❌ | Non supporté |
| Anthropic | claude-3-sonnet | ✅ | Excellent |
| Groq | llama-3.1-70b | ✅ | Rapide |

## 🛠️ Configuration

### Variables d'Environnement

```bash
# Modèle et provider
OPENAI_MODEL=gpt-4
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-...

# Agent
AGENT_MAX_ITERATIONS=10
AGENT_VERBOSE=true

# Logging
LOG_LEVEL=INFO  # ou DEBUG pour plus de détails
```

### Dans le Code

```python
# Option 1: Validation automatique (recommandé pour nouveaux modèles)
agent = GristAgent(
    document_id="...",
    grist_token="...",
    validate_function_calling_on_init=True,  # ← Active la validation
    max_iterations=10,
    verbose=True
)

# Option 2: Validation manuelle
agent = GristAgent(...)
validation_result = await agent.validate_function_calling()
if not validation_result["test_passed"]:
    raise ValueError("Model not compatible")
```

## 📚 Documentation Complète

Pour plus de détails :

- **[FUNCTION_CALLING_DIAGNOSTICS.md](./FUNCTION_CALLING_DIAGNOSTICS.md)** - Guide complet avec troubleshooting
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Architecture générale
- **[CHANGELOG.md](../CHANGELOG.md)** - Historique des changements

## 🤝 Contribution

Ces fonctionnalités sont conçues pour être extensibles. Contributions bienvenues pour :

- Tests de nouveaux modèles
- Amélioration des détections de patterns
- Nouveaux diagnostics
- Amélioration de la documentation

Voir [CONTRIBUTING.md](../CONTRIBUTING.md).

---

**Créé le** : 2025-01-19  
**Auteur** : OpenGristAI Team  
**Version** : 0.3.0 (unreleased)

