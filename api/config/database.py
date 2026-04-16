import requests
from typing import Dict, Any, List, Optional

PB_URL = "http://127.0.0.1:8090/api/collections"

class PocketBaseClient:
    def __init__(self):
        self.base_url = PB_URL

    def table(self, table_name: str, token: str = None):
        return PocketBaseTable(self.base_url, table_name, token=token)

class PocketBaseTable:
    def __init__(self, base_url: str, table_name: str, token: str = None):
        self.url = f"{base_url}/{table_name}/records"
        self.filters: List[str] = []
        self.columns = "*"
        self.token = token

    def _auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def select(self, columns: str = "*"):
        self.columns = columns
        return self

    def eq(self, field: str, value: str):
        self.filters.append(f'{field}="{value}"')
        return self

    def execute(self):
        filter_str = " && ".join(self.filters) if self.filters else ""
        params = {"perPage": 1000}
        if filter_str:
            params["filter"] = filter_str
        response = requests.get(self.url, params=params, headers=self._auth_headers())
        data = response.json()
        if "items" not in data:
            data["items"] = []
        return data

    def insert(self, data: Dict[str, Any]):
        response = requests.post(self.url, json=data, headers=self._auth_headers())
        result = response.json()
        if "id" in result:
            return {"items": [result]}
        raise ValueError(result)

    def update(self, data: Dict[str, Any]):
        record_id = data.pop("id", None)
        if not record_id:
            raise ValueError("Update needs 'id' field")
        response = requests.patch(f"{self.url}/{record_id}", json=data, headers=self._auth_headers())
        result = response.json()
        if "id" in result:
            return {"items": [result]}
        return {"items": [], "error": result}

    def delete(self):
        filter_str = " && ".join(self.filters) if self.filters else ""
        if not filter_str:
            raise ValueError("Delete needs filter")
        list_response = requests.get(self.url, params={"filter": filter_str}, headers=self._auth_headers())
        records = list_response.json().get("items", [])
        deleted = []
        for record in records:
            del_response = requests.delete(f"{self.url}/{record['id']}", headers=self._auth_headers())
            if del_response.status_code == 204:
                deleted.append(record)
        return {"items": deleted}

# Global client
pocketbase = PocketBaseClient()
