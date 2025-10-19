# Function Calling Diagnostics & Troubleshooting

Ce document explique le système de diagnostics amélioré pour le function calling dans Grist AI API v2.

## 🎯 Objectif

Avec la diversité des modèles LLM disponibles (OpenAI, Mistral, Claude, Groq, etc.), tous ne supportent pas le function calling de la même manière. Ce système de diagnostics permet de :

1. **Détecter** rapidement si un modèle ne supporte pas le function calling
2. **Diagnostiquer** les problèmes de compatibilité avec des logs détaillés
3. **Suivre** la santé du système avec des métriques
4. **Alerter** en cas de comportements suspects

## 🔍 Système de Logging Amélioré

### Niveaux de Logs

Le système utilise plusieurs niveaux de logs :

- **DEBUG** : Détails techniques de chaque itération
- **INFO** : Événements importants (tool calls réussis, métriques)
- **WARNING** : Comportements suspects (pas de tool calls, liste vide)
- **ERROR** : Problèmes critiques (function calling non supporté)

### Ce qui est loggé maintenant

#### Pour chaque itération de l'agent

```
DEBUG: LLM Response Type: AIMessage
DEBUG: Response has 'content': True
DEBUG: Response has 'tool_calls': True
DEBUG: tool_calls attribute type: <class 'list'>
DEBUG: tool_calls value: [...]
DEBUG: tool_calls bool value: True
DEBUG: Number of tool calls: 2
INFO:  ✓ LLM requested 2 tool call(s) - function calling working correctly
```

#### Pour chaque tool call

```
DEBUG: --- Tool Call 1/2 ---
DEBUG: Tool: get_tables
DEBUG: Args: {}
DEBUG: ID: call_abc123
INFO:  ✅ Tool 'get_tables' executed successfully
```

#### En cas d'échec

```
ERROR: 🔴 MALFORMED TOOL CALL: Unable to parse tool call structure
ERROR: ❌ Tool 'get_tables' failed: Connection timeout
```

#### Détection de problèmes

```
WARNING: ⚠️  LLM returned empty tool_calls list. This may indicate the model doesn't understand function calling properly.

ERROR: 🔴 FUNCTION CALLING FAILURE: No tool calls for 3 consecutive iterations. 
This strongly suggests the LLM (mistral-small) doesn't properly support function calling.
Consider using a different model (e.g., gpt-4, gpt-3.5-turbo, claude-3-sonnet, mistral-large-latest).
```

### Métriques de fin d'exécution

À la fin de chaque requête, un résumé est fourni :

```
INFO: ✅ Agent execution completed successfully
INFO: 📊 Execution Summary:
INFO:    - Total iterations: 3/10
INFO:    - Total tool calls: 5
INFO:    - Failed tool calls: 0
INFO:    - Success rate: 100.0%
```

## 🧪 Validation au Démarrage

### Validation manuelle

Vous pouvez valider qu'un modèle supporte le function calling avec :

```python
from app.core.agent import GristAgent

agent = GristAgent(
    document_id="your_doc_id",
    grist_token="your_token"
)

# Valider le function calling
validation_result = await agent.validate_function_calling()

if validation_result["test_passed"]:
    print("✅ Function calling is working correctly")
else:
    print(f"❌ Problem detected: {validation_result}")
```

### Validation automatique

Pour activer la validation automatique au premier `run()` :

```python
agent = GristAgent(
    document_id="your_doc_id",
    grist_token="your_token",
    validate_function_calling_on_init=True  # Active la validation
)

# La validation se fera automatiquement au premier run
result = await agent.run("Liste les tables")
```

⚠️ **Note** : La validation fait un appel API test au LLM, ce qui ajoute :
- Latence (~1-2 secondes)
- Coût minimal (1 appel API simple)

### Résultat de validation

La validation retourne un dictionnaire avec :

```python
{
    "supported": True,           # Si le modèle a l'attribut tool_calls
    "has_tool_calls_attr": True, # Si response.tool_calls existe
    "test_passed": True,         # Si le test complet a réussi
    "response_type": "AIMessage",# Type de la réponse
    "num_tool_calls": 1,        # Nombre de tool calls générés
}
```

## 📊 Métriques et Diagnostics

### Métriques retournées

Chaque appel à `agent.run()` retourne maintenant des métriques :

```python
result = await agent.run("Ajoute une colonne Age")

print(result["metrics"])
# {
#     "iterations": 2,
#     "tool_calls": 3,
#     "failed_tool_calls": 0
# }
```

### Patterns de problèmes détectés

#### 1. Modèle ne supporte pas function calling

**Symptômes** :
- Pas d'attribut `tool_calls` dans la réponse
- 0 tool calls sur toutes les itérations

**Logs** :
```
WARNING: ⚠️  LLM response has no 'tool_calls' attribute. This model may not support function calling.
ERROR: 🔴 CRITICAL: Agent made 0 tool calls across all iterations.
```

**Solution** : Changer de modèle vers un modèle compatible

#### 2. Modèle supporte partiellement

**Symptômes** :
- Attribut `tool_calls` présent mais souvent vide
- Quelques tool calls mais pas toujours

**Logs** :
```
WARNING: ⚠️  LLM returned empty tool_calls list.
```

**Solution** : Utiliser un modèle plus performant ou ajuster le prompt système

#### 3. Tools échouent fréquemment

**Symptômes** :
- Taux d'échec > 50%
- Erreurs répétées d'exécution

**Logs** :
```
ERROR: ❌ Tool 'query_document' failed: Invalid SQL syntax
ERROR: 🔴 CRITICAL: High failure rate (3/5).
```

**Solution** : Vérifier les arguments passés par le LLM, améliorer les descriptions des tools

#### 4. Max iterations atteint

**Symptômes** :
- Agent atteint la limite d'itérations
- Pas de réponse finale

**Logs** :
```
ERROR: ⚠️  Agent reached max iterations (10)
```

**Solution** : 
- Augmenter `max_iterations` si besoin
- Simplifier la requête
- Vérifier si le modèle boucle (même tools appelés répétitivement)

## 🔧 Configuration

### Variables d'environnement

```bash
# Modèle à utiliser
OPENAI_MODEL=gpt-4-turbo-preview

# URL de base (pour providers compatibles OpenAI)
OPENAI_BASE_URL=https://api.openai.com/v1

# Clé API
OPENAI_API_KEY=your_api_key

# Agent settings
AGENT_MAX_ITERATIONS=10
AGENT_VERBOSE=true
```

### Niveau de logging

Dans votre code Python :

```python
import logging

# Activer tous les logs de debug
logging.basicConfig(level=logging.DEBUG)

# Ou seulement pour le module agent
logging.getLogger("app.core.agent").setLevel(logging.DEBUG)
```

## 🧪 Compatibilité des Modèles

### Modèles Testés

| Provider | Modèle | Function Calling | Qualité | Notes |
|----------|--------|------------------|---------|-------|
| OpenAI | gpt-4, gpt-4-turbo | ✅ Excellent | ⭐⭐⭐⭐⭐ | Référence |
| OpenAI | gpt-3.5-turbo | ✅ Bon | ⭐⭐⭐⭐ | Bon rapport qualité/prix |
| Anthropic | claude-3-opus | ✅ Excellent | ⭐⭐⭐⭐⭐ | Via tool use API |
| Anthropic | claude-3-sonnet | ✅ Excellent | ⭐⭐⭐⭐⭐ | Recommandé |
| Mistral | mistral-large-latest | ✅ Bon | ⭐⭐⭐⭐ | Compatible |
| Mistral | mistral-medium-latest | ⚠️ Moyen | ⭐⭐⭐ | Peut oublier des tools |
| Mistral | mistral-small, 7B, etc. | ❌ Non | - | Pas de support |
| Groq | llama-3.1-70b-versatile | ✅ Bon | ⭐⭐⭐⭐ | Rapide |
| Groq | mixtral-8x7b-32768 | ⚠️ Moyen | ⭐⭐⭐ | Support partiel |

### Comment tester un nouveau modèle

1. **Configurer le modèle** :
```bash
export OPENAI_MODEL=mistral-large-latest
export OPENAI_BASE_URL=https://api.mistral.ai/v1
export OPENAI_API_KEY=your_mistral_key
```

2. **Tester avec validation** :
```python
agent = GristAgent(
    document_id="test_doc",
    grist_token="test_token",
    validate_function_calling_on_init=True
)

result = await agent.validate_function_calling()
print(f"Validation: {result}")
```

3. **Faire quelques tests** :
```python
# Test simple
result1 = await agent.run("Liste les tables")

# Test avec tool calls multiples
result2 = await agent.run("Ajoute une colonne Age de type Int à la table Users")

# Vérifier les métriques
print(f"Métriques: {result1['metrics']}")
print(f"Métriques: {result2['metrics']}")
```

4. **Analyser les logs** :
- Vérifier qu'il y a des tool calls
- Vérifier le taux de succès
- Regarder s'il y a des warnings

## 🐛 Troubleshooting

### Problème : Aucun tool call généré

**Diagnostic** :
```bash
# Activer les logs détaillés
export AGENT_VERBOSE=true

# Vérifier les logs
tail -f logs/app.log | grep "tool_calls"
```

**Vérifications** :
1. Le modèle supporte-t-il function calling ?
2. La clé API est-elle valide ?
3. Le `base_url` est-il correct ?

### Problème : Tools appelés mais échouent

**Diagnostic** :
```bash
# Regarder les erreurs spécifiques
tail -f logs/app.log | grep "ERROR"
```

**Vérifications** :
1. Les descriptions des tools sont-elles claires ?
2. Le Grist token est-il valide ?
3. Les données respectent-elles le schéma ?

### Problème : Max iterations atteint systématiquement

**Diagnostic** :
```python
# Augmenter les iterations temporairement pour debug
agent = GristAgent(
    ...,
    max_iterations=20,  # Au lieu de 10
    verbose=True
)
```

**Vérifications** :
1. Le modèle boucle-t-il (mêmes tools répétés) ?
2. Les tool results sont-ils utiles pour le LLM ?
3. La requête est-elle trop complexe ?

## 📝 Exemples d'Utilisation

### Exemple 1 : Debug d'un nouveau modèle

```python
import logging
from app.core.agent import GristAgent

# Activer les logs détaillés
logging.basicConfig(level=logging.DEBUG)

# Créer l'agent avec validation
agent = GristAgent(
    document_id="test_doc",
    grist_token="token",
    validate_function_calling_on_init=True,
    max_iterations=5
)

# Tester
result = await agent.run("Liste les tables du document")

# Analyser
if not result["success"]:
    print(f"Échec : {result['error']}")
    print(f"Métriques : {result['metrics']}")
else:
    print(f"Succès ! Métriques : {result['metrics']}")
```

### Exemple 2 : Monitoring en production

```python
from app.core.agent import GristAgent
import logging

logger = logging.getLogger(__name__)

async def handle_user_request(request):
    agent = GristAgent(...)
    
    result = await agent.run(request.message)
    
    # Logger les métriques
    metrics = result.get("metrics", {})
    logger.info(f"Request completed", extra={
        "tool_calls": metrics.get("tool_calls", 0),
        "failed_calls": metrics.get("failed_tool_calls", 0),
        "iterations": metrics.get("iterations", 0),
        "success": result["success"]
    })
    
    # Alerter si problème
    if not result["success"] or metrics.get("failed_tool_calls", 0) > 0:
        logger.warning(f"Request had issues: {result}")
    
    return result
```

## 📚 Références

- [LangChain Function Calling](https://python.langchain.com/docs/modules/model_io/chat/function_calling)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Mistral Function Calling](https://docs.mistral.ai/capabilities/function_calling/)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)

---

**Créé le** : 2025-01-19  
**Dernière mise à jour** : 2025-01-19  
**Version API** : v2

