import os
from pathlib import Path
from uuid import uuid4

from pipeline.runtime import retry


class LocalStore:
    def __init__(self, root):
        self.root = Path(root)

    def put(self, key, data):
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
        try:
            temporary.write_bytes(data)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


class AzureStore:
    def __init__(self, container, account_url=None):
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient
        connection = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        if connection:
            service = BlobServiceClient.from_connection_string(connection, retry_total=3)
        elif account_url:
            service = BlobServiceClient(account_url, credential=DefaultAzureCredential(), retry_total=3)
        else:
            raise ValueError("Set AZURE_STORAGE_ACCOUNT_URL or AZURE_STORAGE_CONNECTION_STRING")
        self.container = service.get_container_client(container)

    def put(self, key, data):
        from azure.core.exceptions import HttpResponseError, ServiceRequestError, ServiceResponseError

        def transient(exc):
            return isinstance(exc, (ServiceRequestError, ServiceResponseError)) or (
                isinstance(exc, HttpResponseError) and exc.status_code in (408, 429, 500, 502, 503, 504)
            )

        retry(lambda: self.container.upload_blob(key, data, overwrite=True), transient)
