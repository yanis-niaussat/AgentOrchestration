import requests
import json
from typing import Optional, Dict, Any

class WorkflowClient:
    """
    A client to interact with n8n workflows via Webhook nodes.
    Supports standard HTTP methods (GET, POST, etc.) to trigger workflows.
    """
    
    def __init__(self, webhook_url: str, auth_user: str = None, auth_password: str = None, verify_ssl: bool = True):
        """
        Initialize the client with the n8n webhook URL.
        
        Args:
            webhook_url: The full URL of the n8n webhook node.
            auth_user: Optional username for Basic Auth.
            auth_password: Optional password for Basic Auth.
            verify_ssl: Whether to verify SSL certificates.
        """
        self.webhook_url = webhook_url
        self.verify_ssl = verify_ssl
        self.auth = (auth_user, auth_password) if auth_user and auth_password else None
        self.headers = {
            "Content-Type": "application/json"
        }

    def _request(self, method: str, path: str = "", data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        """Helper to make HTTP requests."""
        url = self.webhook_url if not path else f"{self.webhook_url.rstrip('/')}/{path.lstrip('/')}"
        
        # Merge instance headers with request-specific headers
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)
            
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data if method in ["POST", "PUT", "PATCH"] else None,
                params=params,
                headers=request_headers,
                auth=self.auth,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text
                
        except requests.exceptions.RequestException as e:
            print(f"Error during {method} request to {url}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status Code: {e.response.status_code}")
                print(f"Response Content: {e.response.text}")
            raise

    def get(self, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        """Trigger the workflow using a GET request."""
        return self._request("GET", params=params, headers=headers)

    def post(self, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        """Trigger the workflow using a POST request."""
        return self._request("POST", data=data, headers=headers)

    def put(self, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        """Trigger the workflow using a PUT request."""
        return self._request("PUT", data=data, headers=headers)

    def delete(self, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        """Trigger the workflow using a DELETE request."""
        return self._request("DELETE", params=params, headers=headers)

# Example Usage:
if __name__ == "__main__":
    # Replace with your actual webhook URL from n8n
    WEBHOOK_URL = "http://localhost:5678/webhook/test-workflow"
    
    client = WorkflowClient(WEBHOOK_URL, verify_ssl=False)
    
    # Example POST request
    # print("Sending POST request...")
    # result = client.post({"name": "Yanis", "message": "Hello from Python!"})
    # print(result)
    
    # Example GET request
    # print("Sending GET request...")
    # result = client.get(params={"status": "active"})
    # print(result)
