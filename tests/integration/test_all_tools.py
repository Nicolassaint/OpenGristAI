"""
Script de test pour tous les tools Grist

Ce script teste tous les 12 tools disponibles sur un document Grist réel.
Il crée des données de test temporaires et les nettoie après.
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.grist_service import GristService
from app.core.tools import set_grist_service
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

# REMPLACER PAR VOS VRAIES VALEURS
DOCUMENT_ID = "jrsG9Qhc7domWgz1HBWiVp"  # Votre document ID
API_KEY = os.getenv("GRIST_API_KEY", "")  # Votre API Key (depuis Account Settings)
BASE_URL = "https://grist.numerique.gouv.fr"  # Votre instance Grist

# Nom de la table de test (sera créée puis supprimée)
TEST_TABLE_NAME = "TestToolsTable"

# NOTE: Pour utiliser un JWT token du widget au lieu d'une API Key,
# changez use_api_key=False et utilisez GRIST_ACCESS_TOKEN


# ============================================================================
# Helper Functions
# ============================================================================

class ToolTestResults:
    """Classe pour tracker les résultats des tests."""

    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.total = 0
        self.passed = 0
        self.failed = 0

    def add(self, tool_name: str, success: bool, message: str = "", data: Any = None):
        """Ajouter un résultat de test."""
        self.total += 1
        if success:
            self.passed += 1
            status = "✅ PASS"
        else:
            self.failed += 1
            status = "❌ FAIL"

        self.results[tool_name] = {
            "status": status,
            "message": message,
            "data": data
        }

        print(f"\n{status} - {tool_name}")
        if message:
            print(f"   {message}")
        if data:
            print(f"   Data: {data}")

    def print_summary(self):
        """Afficher le résumé des tests."""
        print("\n" + "=" * 80)
        print("RÉSUMÉ DES TESTS")
        print("=" * 80)
        print(f"Total: {self.total} | Passed: {self.passed} | Failed: {self.failed}")
        print("=" * 80)

        if self.failed > 0:
            print("\n❌ ÉCHECS:")
            for tool_name, result in self.results.items():
                if "FAIL" in result["status"]:
                    print(f"  - {tool_name}: {result['message']}")


# ============================================================================
# Test Functions
# ============================================================================

async def test_all_tools():
    """Teste tous les tools disponibles."""

    results = ToolTestResults()

    if not API_KEY:
        print("❌ ERREUR: GRIST_API_KEY non défini!")
        print("   Définissez la variable d'environnement GRIST_API_KEY")
        print("   Ou obtenez votre API Key depuis : Account Settings → API")
        return

    print("=" * 80)
    print("TEST DE TOUS LES TOOLS GRIST")
    print("=" * 80)
    print(f"Document ID: {DOCUMENT_ID}")
    print(f"Base URL: {BASE_URL}")
    print(f"Auth: API Key (****{API_KEY[-8:]})")
    print("=" * 80)

    # Créer le service avec API Key
    async with GristService(
        document_id=DOCUMENT_ID,
        access_token=API_KEY,
        base_url=BASE_URL,
        enable_validation=False,  # Désactiver la validation pour les tests
        use_api_key=True,  # Utiliser l'authentification par API Key
    ) as service:

        set_grist_service(service)

        # ====================================================================
        # 1. Test get_tables
        # ====================================================================
        try:
            tables = await service.get_tables()
            results.add(
                "get_tables",
                True,
                f"Found {len(tables)} table(s)",
                [t.get('id') for t in tables]
            )
            existing_table = tables[0]['id'] if tables else None
        except Exception as e:
            results.add("get_tables", False, str(e))
            existing_table = None

        # ====================================================================
        # 2. Test get_table_columns (sur table existante)
        # ====================================================================
        if existing_table:
            try:
                columns = await service.get_table_columns(existing_table)
                results.add(
                    "get_table_columns",
                    True,
                    f"Table '{existing_table}' has {len(columns)} column(s)",
                    [c.get('id') for c in columns]
                )
            except Exception as e:
                results.add("get_table_columns", False, str(e))
        else:
            results.add("get_table_columns", False, "No existing table to test")

        # ====================================================================
        # 3. Test query_document (SQL)
        # ====================================================================
        if existing_table:
            try:
                query_result = await service.query_document(
                    f"SELECT * FROM {existing_table} LIMIT 3"
                )
                results.add(
                    "query_document",
                    True,
                    f"Query returned {len(query_result)} record(s)"
                )
            except Exception as e:
                results.add("query_document", False, str(e))
        else:
            results.add("query_document", False, "No table available for SQL query")

        # ====================================================================
        # 4. Test add_table
        # ====================================================================
        test_table_created = False
        try:
            columns = [
                {
                    "id": "TestName",
                    "fields": {
                        "type": "Text",
                        "label": "Name"
                    }
                },
                {
                    "id": "TestAge",
                    "fields": {
                        "type": "Int",
                        "label": "Age"
                    }
                }
            ]
            result = await service.add_table(TEST_TABLE_NAME, columns)
            results.add(
                "add_table",
                True,
                f"Created table '{TEST_TABLE_NAME}' with {result.get('columns_count', 0)} columns"
            )
            test_table_created = True
        except Exception as e:
            results.add("add_table", False, str(e))

        # ====================================================================
        # 5. Test add_table_column (sur table de test)
        # ====================================================================
        if test_table_created:
            try:
                result = await service.add_table_column(
                    TEST_TABLE_NAME,
                    "TestEmail",
                    "Text",
                    label="Email Address"
                )
                results.add(
                    "add_table_column",
                    True,
                    f"Added column 'TestEmail' to table '{TEST_TABLE_NAME}'"
                )
            except Exception as e:
                results.add("add_table_column", False, str(e))
        else:
            results.add("add_table_column", False, "Test table not created")

        # ====================================================================
        # 6. Test add_records (sur table de test)
        # ====================================================================
        if test_table_created:
            try:
                records = [
                    {"TestName": "Alice", "TestAge": 30},
                    {"TestName": "Bob", "TestAge": 25}
                ]
                result = await service.add_records(TEST_TABLE_NAME, records)
                results.add(
                    "add_records",
                    True,
                    f"Added {result.get('count', 0)} record(s)",
                    result.get('record_ids')
                )
                test_record_ids = result.get('record_ids', [])
            except Exception as e:
                results.add("add_records", False, str(e))
                test_record_ids = []
        else:
            results.add("add_records", False, "Test table not created")
            test_record_ids = []

        # ====================================================================
        # 7. Test update_records (sur table de test)
        # ====================================================================
        if test_table_created and test_record_ids:
            try:
                updates = [{"TestAge": 31}]  # Update first record
                result = await service.update_records(
                    TEST_TABLE_NAME,
                    [test_record_ids[0]],
                    updates
                )
                results.add(
                    "update_records",
                    True,
                    f"Updated {result.get('updated_count', 0)} record(s)"
                )
            except Exception as e:
                results.add("update_records", False, str(e))
        else:
            results.add("update_records", False, "No test records available")

        # ====================================================================
        # 8. Test update_table_column (sur table de test)
        # ====================================================================
        updated_column_id = "TestEmail"  # L'ID peut changer après update
        if test_table_created:
            try:
                result = await service.update_table_column(
                    TEST_TABLE_NAME,
                    "TestEmail",
                    label="Email (Updated)"
                )
                results.add(
                    "update_table_column",
                    True,
                    "Updated column label successfully"
                )

                # Re-fetch les colonnes pour obtenir le nouvel ID (Grist peut l'avoir changé)
                columns = await service.get_table_columns(TEST_TABLE_NAME)
                # Chercher la colonne qui contient "Email" dans son ID
                for col in columns:
                    col_id = col.get('id', '')
                    if 'Email' in col_id and col_id != "TestEmail":
                        updated_column_id = col_id
                        break
            except Exception as e:
                results.add("update_table_column", False, str(e))
        else:
            results.add("update_table_column", False, "Test table not created")

        # ====================================================================
        # 9. Test remove_records (sur table de test)
        # ====================================================================
        if test_table_created and test_record_ids:
            try:
                # Supprimer seulement le premier record pour garder des données pour les autres tests
                result = await service.remove_records(
                    TEST_TABLE_NAME,
                    [test_record_ids[0]]
                )
                results.add(
                    "remove_records",
                    True,
                    f"Removed {result.get('deleted_count', 0)} record(s)"
                )
            except Exception as e:
                results.add("remove_records", False, str(e))
        else:
            results.add("remove_records", False, "No test records available")

        # ====================================================================
        # 10. Test remove_table_column (sur table de test)
        # ====================================================================
        if test_table_created:
            try:
                # Utiliser l'ID mis à jour (Grist peut avoir changé l'ID après update)
                result = await service.remove_table_column(
                    TEST_TABLE_NAME,
                    updated_column_id
                )
                results.add(
                    "remove_table_column",
                    True,
                    f"Removed column '{updated_column_id}' successfully"
                )
            except Exception as e:
                results.add("remove_table_column", False, str(e))
        else:
            results.add("remove_table_column", False, "Test table not created")

        # ====================================================================
        # 11. Test get_grist_access_rules_reference
        # ====================================================================
        try:
            from app.core.tools import get_grist_access_rules_reference
            # Les tools LangChain doivent être invoqués avec .ainvoke({})
            result = await get_grist_access_rules_reference.ainvoke({})
            results.add(
                "get_grist_access_rules_reference",
                True,
                f"Returned documentation ({len(result)} chars)"
            )
        except Exception as e:
            results.add("get_grist_access_rules_reference", False, str(e))

        # ====================================================================
        # 12. Test get_available_custom_widgets
        # ====================================================================
        try:
            from app.core.tools import get_available_custom_widgets
            # Les tools LangChain doivent être invoqués avec .ainvoke({})
            result = await get_available_custom_widgets.ainvoke({})
            results.add(
                "get_available_custom_widgets",
                True,
                f"Found {len(result)} available widget(s)",
                [w.get('name') for w in result]
            )
        except Exception as e:
            results.add("get_available_custom_widgets", False, str(e))

        # ====================================================================
        # CLEANUP: Supprimer la table de test
        # ====================================================================
        # NOTE: Comme remove_table n'existe pas dans l'API, on laisse la table
        # L'utilisateur peut la supprimer manuellement via l'interface Grist
        if test_table_created:
            print(f"\n⚠️  ATTENTION: Table de test '{TEST_TABLE_NAME}' créée mais non supprimée")
            print(f"   (L'API Grist ne permet pas de supprimer des tables)")
            print(f"   Vous pouvez la supprimer manuellement via l'interface Grist")

    # Afficher le résumé
    results.print_summary()

    return results.failed == 0


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n🧪 DÉBUT DES TESTS\n")

    success = asyncio.run(test_all_tools())

    if success:
        print("\n✅ TOUS LES TESTS SONT PASSÉS!\n")
        sys.exit(0)
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ\n")
        sys.exit(1)
