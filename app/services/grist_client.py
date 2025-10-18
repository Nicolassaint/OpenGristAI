"""
Grist API Client

HTTP client for interacting with Grist REST API.
Uses the access token obtained from the Grist plugin API.
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)


class GristAPIClient:
    """
    HTTP client for Grist REST API.

    The Grist REST API documentation:
    https://support.getgrist.com/api/

    The base URL and token are obtained from grist.docApi.getAccessToken()
    in the front-end and passed to the backend via headers.
    """

    def __init__(
        self,
        document_id: str,
        access_token: str,
        base_url: str = "https://docs.getgrist.com",
        timeout: float = 30.0,
    ):
        """
        Initialize the Grist API client.

        Args:
            document_id: Grist document ID or name
            access_token: JWT access token from Grist widget
            base_url: Base URL for Grist API (default: https://docs.getgrist.com)
            timeout: Request timeout in seconds
        """
        self.document_id = document_id
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Create HTTP client WITHOUT auth header
        # Grist widget tokens must be passed as query parameter ?auth=TOKEN
        # NOT as Authorization: Bearer header
        self.client = httpx.AsyncClient(
            headers={
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

        logger.info(f"GristAPIClient initialized for document: {document_id}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _build_url(self, path: str) -> str:
        """
        Build full URL for API endpoint with auth query parameter.

        Grist widget tokens must be passed as ?auth=TOKEN query parameter.
        """
        url = urljoin(self.base_url, path)
        # Add auth query parameter
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}auth={self.access_token}"

    async def _request(
        self, method: str, path: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Grist API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            path: API path
            **kwargs: Additional arguments for httpx

        Returns:
            Response JSON

        Raises:
            httpx.HTTPError: If request fails
        """
        url = self._build_url(path)
        logger.debug(f"{method} {url}")

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Grist API error: {e}")
            raise

    # ========================================================================
    # Table Operations
    # ========================================================================

    async def get_tables(self) -> List[Dict[str, Any]]:
        """
        Get all tables in the document.

        Returns:
            List of table metadata

        API: GET /api/docs/{docId}/tables
        """
        path = f"/api/docs/{self.document_id}/tables"
        data = await self._request("GET", path)
        return data.get("tables", [])

    async def get_table_columns(self, table_id: str) -> List[Dict[str, Any]]:
        """
        Get columns for a specific table.

        Args:
            table_id: Table ID

        Returns:
            List of column metadata

        API: GET /api/docs/{docId}/tables/{tableId}/columns
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/columns"
        data = await self._request("GET", path)
        return data.get("columns", [])

    async def add_table(self, table_id: str, columns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a new table in the document.

        Args:
            table_id: ID for the new table
            columns: List of column definitions

        Returns:
            Response with created table info

        API: POST /api/docs/{docId}/tables
        """
        path = f"/api/docs/{self.document_id}/tables"
        payload = {
            "tables": [{
                "id": table_id,
                "columns": columns
            }]
        }

        logger.info(f"Creating table '{table_id}' with {len(columns)} column(s)")
        return await self._request("POST", path, json=payload)

    async def update_table(self, table_id: str, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Update table metadata (e.g., rename table).

        Args:
            table_id: Table ID to update
            name: New name for the table (optional)

        Returns:
            Response confirming update

        API: PATCH /api/docs/{docId}/tables/{tableId}
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}"
        payload = {}
        if name is not None:
            payload["tableId"] = name

        logger.info(f"Updating table '{table_id}'")
        return await self._request("PATCH", path, json=payload)

    async def delete_table(self, table_id: str) -> Dict[str, Any]:
        """
        Delete a table from the document.

        Args:
            table_id: Table ID to delete

        Returns:
            Response confirming deletion

        API: DELETE /api/docs/{docId}/tables/{tableId}
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}"

        logger.warning(f"Deleting table '{table_id}'")
        return await self._request("DELETE", path)

    # ========================================================================
    # Column Operations
    # ========================================================================

    async def add_column(
        self, table_id: str, column_id: str, label: str, col_type: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Add a new column to a table.

        Args:
            table_id: Table ID
            column_id: Column ID
            label: Column label
            col_type: Column type (Text, Numeric, Int, Bool, Date, Choice, Ref, etc.)
            **kwargs: Additional column properties (formula, widgetOptions, etc.)

        Returns:
            Response with created column info

        API: POST /api/docs/{docId}/tables/{tableId}/columns
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/columns"

        column_def = {
            "id": column_id,
            "label": label,
            "type": col_type,
            **kwargs
        }

        payload = {"columns": [column_def]}

        logger.info(f"Adding column '{column_id}' to table '{table_id}'")
        return await self._request("POST", path, json=payload)

    async def update_column(
        self, table_id: str, column_id: str, **updates
    ) -> Dict[str, Any]:
        """
        Update a column's properties.

        Args:
            table_id: Table ID
            column_id: Column ID to update
            **updates: Properties to update (label, type, formula, widgetOptions, etc.)

        Returns:
            Response confirming update

        API: PATCH /api/docs/{docId}/tables/{tableId}/columns/{columnId}
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/columns/{column_id}"
        payload = updates

        logger.info(f"Updating column '{column_id}' in table '{table_id}'")
        return await self._request("PATCH", path, json=payload)

    async def delete_column(self, table_id: str, column_id: str) -> Dict[str, Any]:
        """
        Delete a column from a table.

        Args:
            table_id: Table ID
            column_id: Column ID to delete

        Returns:
            Response confirming deletion

        API: DELETE /api/docs/{docId}/tables/{tableId}/columns/{columnId}
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/columns/{column_id}"

        logger.warning(f"Deleting column '{column_id}' from table '{table_id}'")
        return await self._request("DELETE", path)

    # ========================================================================
    # Page Operations
    # ========================================================================

    async def get_pages(self) -> List[Dict[str, Any]]:
        """
        Get all pages in the document.

        Returns:
            List of page metadata

        API: GET /api/docs/{docId}/pages
        """
        path = f"/api/docs/{self.document_id}/pages"
        data = await self._request("GET", path)
        return data.get("pages", [])

    async def update_page(self, page_id: int, **updates) -> Dict[str, Any]:
        """
        Update a page's properties.

        Args:
            page_id: Page ID
            **updates: Properties to update (name, etc.)

        Returns:
            Response confirming update

        API: PATCH /api/docs/{docId}/pages/{pageId}
        """
        path = f"/api/docs/{self.document_id}/pages/{page_id}"
        payload = updates

        logger.info(f"Updating page {page_id}")
        return await self._request("PATCH", path, json=payload)

    async def delete_page(self, page_id: int) -> Dict[str, Any]:
        """
        Delete a page from the document.

        Args:
            page_id: Page ID to delete

        Returns:
            Response confirming deletion

        API: DELETE /api/docs/{docId}/pages/{pageId}
        """
        path = f"/api/docs/{self.document_id}/pages/{page_id}"

        logger.warning(f"Deleting page {page_id}")
        return await self._request("DELETE", path)

    # ========================================================================
    # Widget Operations
    # ========================================================================

    async def get_page_widgets(self, page_id: int) -> List[Dict[str, Any]]:
        """
        Get all widgets on a page.

        Args:
            page_id: Page ID

        Returns:
            List of widget metadata

        API: GET /api/docs/{docId}/pages/{pageId}/widgets
        """
        path = f"/api/docs/{self.document_id}/pages/{page_id}/widgets"
        data = await self._request("GET", path)
        return data.get("widgets", [])

    async def add_page_widget(
        self, page_id: int, widget_type: str, table_id: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Add a new widget to a page.

        Args:
            page_id: Page ID
            widget_type: Widget type (e.g., "record", "chart", "custom")
            table_id: Table ID to display
            **kwargs: Additional widget properties

        Returns:
            Response with created widget info

        API: POST /api/docs/{docId}/pages/{pageId}/widgets
        """
        path = f"/api/docs/{self.document_id}/pages/{page_id}/widgets"

        widget_def = {
            "type": widget_type,
            "tableId": table_id,
            **kwargs
        }

        payload = {"widgets": [widget_def]}

        logger.info(f"Adding widget to page {page_id}")
        return await self._request("POST", path, json=payload)

    async def update_page_widget(
        self, page_id: int, widget_id: int, **updates
    ) -> Dict[str, Any]:
        """
        Update a widget's properties.

        Args:
            page_id: Page ID
            widget_id: Widget ID to update
            **updates: Properties to update

        Returns:
            Response confirming update

        API: PATCH /api/docs/{docId}/pages/{pageId}/widgets/{widgetId}
        """
        path = f"/api/docs/{self.document_id}/pages/{page_id}/widgets/{widget_id}"
        payload = updates

        logger.info(f"Updating widget {widget_id} on page {page_id}")
        return await self._request("PATCH", path, json=payload)

    async def delete_page_widget(self, page_id: int, widget_id: int) -> Dict[str, Any]:
        """
        Delete a widget from a page.

        Args:
            page_id: Page ID
            widget_id: Widget ID to delete

        Returns:
            Response confirming deletion

        API: DELETE /api/docs/{docId}/pages/{pageId}/widgets/{widgetId}
        """
        path = f"/api/docs/{self.document_id}/pages/{page_id}/widgets/{widget_id}"

        logger.warning(f"Deleting widget {widget_id} from page {page_id}")
        return await self._request("DELETE", path)

    # ========================================================================
    # Record Operations
    # ========================================================================

    async def get_records(
        self, table_id: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get records from a table.

        Args:
            table_id: Table ID
            filters: Optional filters

        Returns:
            List of records

        API: GET /api/docs/{docId}/tables/{tableId}/records
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/records"
        params = {}
        if filters:
            # TODO: Implement filter parameters
            pass

        data = await self._request("GET", path, params=params)
        return data.get("records", [])

    async def add_records(
        self, table_id: str, records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add records to a table.

        Args:
            table_id: Table ID
            records: List of record data (without IDs)

        Returns:
            Response with created record IDs

        API: POST /api/docs/{docId}/tables/{tableId}/records
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/records"
        payload = {"records": records}

        logger.info(f"Adding {len(records)} record(s) to table '{table_id}'")
        return await self._request("POST", path, json=payload)

    async def update_records(
        self, table_id: str, records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update records in a table.

        Args:
            table_id: Table ID
            records: List of records with 'id' and fields to update

        Returns:
            Response confirming update

        API: PATCH /api/docs/{docId}/tables/{tableId}/records
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/records"
        payload = {"records": records}

        logger.info(f"Updating {len(records)} record(s) in table '{table_id}'")
        return await self._request("PATCH", path, json=payload)

    async def delete_records(
        self, table_id: str, record_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Delete records from a table.

        Args:
            table_id: Table ID
            record_ids: List of record IDs to delete

        Returns:
            Response confirming deletion

        API: DELETE /api/docs/{docId}/tables/{tableId}/records
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/records"
        payload = {"records": record_ids}

        logger.warning(f"Deleting {len(record_ids)} record(s) from table '{table_id}'")
        return await self._request("DELETE", path, json=payload)

    # ========================================================================
    # SQL Query
    # ========================================================================

    async def query_sql(
        self, query: str, args: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query on the document.

        Args:
            query: SQL SELECT query
            args: Optional query parameters

        Returns:
            Query results

        API: POST /api/docs/{docId}/sql
        """
        path = f"/api/docs/{self.document_id}/sql"
        payload = {"sql": query}
        if args:
            payload["args"] = args

        logger.info(f"Executing SQL query: {query[:100]}...")
        data = await self._request("POST", path, json=payload)
        return data.get("records", [])


# TODO: Add page and widget operations
# - GET /api/docs/{docId}/pages
# - PATCH /api/docs/{docId}/pages/{pageId}
# - DELETE /api/docs/{docId}/pages/{pageId}
# - GET /api/docs/{docId}/pages/{pageId}/widgets
# - POST /api/docs/{docId}/pages/{pageId}/widgets
# - PATCH /api/docs/{docId}/pages/{pageId}/widgets/{widgetId}
# - DELETE /api/docs/{docId}/pages/{pageId}/widgets/{widgetId}

# TODO: Add error handling
# - Handle 401 (unauthorized - token expired)
# - Handle 403 (forbidden - insufficient permissions)
# - Handle 404 (document/table not found)
# - Handle 429 (rate limited)

# TODO: Add caching
# - Cache table schemas
# - Cache frequently accessed data
# - Implement cache invalidation
