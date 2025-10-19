# Tests pour les Tools Grist

## Prérequis

1. Un document Grist accessible
2. Une API Key Grist (recommandé pour les tests)

## Obtenir votre API Key

**C'est plus simple qu'un token JWT car elle ne expire jamais !**

1. Allez sur votre instance Grist : `https://grist.numerique.gouv.fr`
2. Cliquez sur votre **profil** (en haut à droite)
3. Allez dans **Account Settings** (Paramètres du compte)
4. Cherchez la section **API**
5. Cliquez sur **Create API Key** (Créer une clé API)
6. Copiez la clé (elle ressemble à : `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

## Configuration

Avant de lancer les tests, vous devez configurer les variables dans `test_all_tools.py` :

```python
# À modifier avec vos valeurs
DOCUMENT_ID = "jrsG9Qhc7domWgz1HBWiVp"  # Votre document ID
API_KEY = os.getenv("GRIST_API_KEY", "")  # Votre API Key
BASE_URL = "https://grist.numerique.gouv.fr"  # Votre instance
```

## Lancer les tests

### Option 1 : Avec variable d'environnement (RECOMMANDÉ)

```bash
# Définir votre API Key
export GRIST_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Lancer les tests
python tests/test_all_tools.py
```

### Option 2 : Modifier directement le fichier

Modifiez la ligne dans `test_all_tools.py` :

```python
API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Votre API Key
```

Puis lancez :

```bash
python tests/test_all_tools.py
```

## Ce que fait le script

Le script teste **tous les 12 tools disponibles** :

### 1. Tools de lecture (non-destructifs)
- ✅ `get_tables` - Liste toutes les tables
- ✅ `get_table_columns` - Liste les colonnes d'une table
- ✅ `query_document` - Exécute une requête SQL
- ✅ `get_grist_access_rules_reference` - Documentation des règles d'accès
- ✅ `get_available_custom_widgets` - Liste des widgets disponibles

### 2. Tools de création
- ✅ `add_table` - Crée une table de test nommée `TestToolsTable`
- ✅ `add_table_column` - Ajoute une colonne à la table de test
- ✅ `add_records` - Ajoute 2 records de test

### 3. Tools de modification
- ✅ `update_records` - Modifie un record de test
- ✅ `update_table_column` - Modifie une colonne de test

### 4. Tools de suppression
- ✅ `remove_records` - Supprime un record de test
- ✅ `remove_table_column` - Supprime une colonne de test

## ⚠️ IMPORTANT : Nettoyage

**L'API Grist ne permet PAS de supprimer des tables via REST API.**

Après le test, une table nommée `TestToolsTable` restera dans votre document.

Vous devez la **supprimer manuellement** via l'interface Grist :
1. Ouvrir votre document Grist
2. Aller dans "Raw Data"
3. Trouver la table `TestToolsTable`
4. Clic droit → Delete table

## Résultats attendus

Le script affiche :
- ✅ Un indicateur PASS/FAIL pour chaque tool
- 📊 Un résumé final avec le nombre de tests réussis/échoués
- 📝 Les détails des données retournées par chaque tool

Exemple de sortie :

```
================================================================================
TEST DE TOUS LES TOOLS GRIST
================================================================================
Document ID: jrsG9Qhc7domWgz1HBWiVp
Base URL: https://grist.numerique.gouv.fr
================================================================================

✅ PASS - get_tables
   Found 1 table(s)
   Data: ['Data_Data']

✅ PASS - get_table_columns
   Table 'Data_Data' has 13 column(s)
   Data: ['A', 'B', 'C', ...]

...

================================================================================
RÉSUMÉ DES TESTS
================================================================================
Total: 12 | Passed: 12 | Failed: 0
================================================================================

✅ TOUS LES TESTS SONT PASSÉS!
```

## Dépannage

### Erreur: "GRIST_API_KEY non défini"
→ Définissez la variable d'environnement ou modifiez directement le fichier
→ Obtenez votre API Key depuis Account Settings → API

### Erreur: "401 Unauthorized"
→ Votre API Key est invalide ou a été révoquée
→ Générez une nouvelle API Key depuis Account Settings

### Erreur: "404 Not Found"
→ Vérifiez que le DOCUMENT_ID et BASE_URL sont corrects
→ Vérifiez que vous avez accès au document avec cette API Key

### Erreur: "Table already exists"
→ La table `TestToolsTable` existe déjà
→ Supprimez-la manuellement ou changez `TEST_TABLE_NAME` dans le script

### Erreur: "403 Forbidden"
→ Votre API Key n'a pas les permissions nécessaires sur ce document
→ Vérifiez que vous êtes propriétaire ou éditeur du document

## Structure des tests

Chaque test suit ce pattern :

```python
try:
    result = await service.tool_function(...)
    results.add("tool_name", True, "Success message", result_data)
except Exception as e:
    results.add("tool_name", False, str(e))
```

Les résultats sont collectés et affichés à la fin.
