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
        use_api_key: bool = False,
    ):
        """
        Initialize the Grist API client.

        Args:
            document_id: Grist document ID or name
            access_token: API Key or JWT access token from Grist widget
            base_url: Base URL for Grist API (default: https://docs.getgrist.com)
            timeout: Request timeout in seconds
            use_api_key: If True, use API Key authentication (Bearer header).
                        If False, use widget JWT token (query parameter).
        """
        self.document_id = document_id
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.use_api_key = use_api_key

        # Create HTTP client with appropriate auth
        headers = {"Content-Type": "application/json"}

        if use_api_key:
            # API Key: use Authorization Bearer header
            headers["Authorization"] = f"Bearer {access_token}"
            logger.info(f"GristAPIClient initialized with API Key for document: {document_id}")
        else:
            # Widget JWT: will use query parameter ?auth=TOKEN
            logger.info(f"GristAPIClient initialized with widget token for document: {document_id}")

        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=timeout,
        )

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
        Build full URL for API endpoint.

        - For API Keys: URL without query parameter (auth is in header)
        - For widget tokens: URL with ?auth=TOKEN query parameter
        """
        url = urljoin(self.base_url, path)

        if not self.use_api_key:
            # Widget JWT token: add as query parameter
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}auth={self.access_token}"

        return url

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


    # ========================================================================
    # Table Management via REST API
    # ========================================================================

    async def add_table(
        self, table_id: str, columns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
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
            "tables": [
                {
                    "id": table_id,
                    "columns": columns
                }
            ]
        }

        logger.info(f"Creating table '{table_id}' with {len(columns)} column(s)")
        return await self._request("POST", path, json=payload)

    # ========================================================================
    # Column Management via REST API
    # ========================================================================

    async def add_column(
        self, table_id: str, column_id: str, fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add a column to a table.

        Args:
            table_id: Table ID
            column_id: Column ID
            fields: Column fields (label, type, formula, widgetOptions, etc.)

        Returns:
            Response with created column info

        API: POST /api/docs/{docId}/tables/{tableId}/columns
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/columns"
        payload = {
            "columns": [
                {
                    "id": column_id,
                    "fields": fields
                }
            ]
        }

        logger.info(f"Adding column '{column_id}' to table '{table_id}'")
        return await self._request("POST", path, json=payload)

    async def update_column(
        self, table_id: str, column_id: str, fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a column's properties.

        Args:
            table_id: Table ID
            column_id: Column ID
            fields: Fields to update

        Returns:
            Response confirming update

        API: PATCH /api/docs/{docId}/tables/{tableId}/columns
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/columns"
        payload = {
            "columns": [
                {
                    "id": column_id,
                    "fields": fields
                }
            ]
        }

        logger.info(f"Updating column '{column_id}' in table '{table_id}'")
        return await self._request("PATCH", path, json=payload)

    async def delete_column(self, table_id: str, column_id: str) -> Dict[str, Any]:
        """
        Delete a column from a table.

        Args:
            table_id: Table ID
            column_id: Column ID

        Returns:
            Response confirming deletion

        API: DELETE /api/docs/{docId}/tables/{tableId}/columns/{colId}
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/columns/{column_id}"

        logger.warning(f"Deleting column '{column_id}' from table '{table_id}'")
        return await self._request("DELETE", path)

    # ========================================================================
    # Record Operations
    # ========================================================================

    async def get_records(
        self, table_id: str, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get records from a table.

        Args:
            table_id: Table ID
            filters: Optional filters
            limit: Optional limit on number of records to return

        Returns:
            List of records

        API: GET /api/docs/{docId}/tables/{tableId}/records
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/records"
        params = {}
        if limit is not None:
            params["limit"] = limit
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

        API: POST /api/docs/{docId}/tables/{tableId}/data/delete
        """
        path = f"/api/docs/{self.document_id}/tables/{table_id}/data/delete"

        logger.warning(f"Deleting {len(record_ids)} record(s) from table '{table_id}'")
        return await self._request("POST", path, json=record_ids)

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
