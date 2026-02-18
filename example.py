import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class N8nAPI:
    def __init__(self):
        self.base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678/api/v1")
        self.api_key = os.getenv("N8N_API_KEY")
        self.verify_ssl = os.getenv("N8N_SSL_VERIFY", "true").lower() == "true"
        self.headers = {
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

    def get_workflows(self):
        """Fetch all workflows from n8n."""
        url = f"{self.base_url}/workflows"
        try:
            response = requests.get(url, headers=self.headers, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching workflows: {e}")
            return None

    def get_workflow(self, workflow_id):
        """Fetch a specific workflow by ID."""
        url = f"{self.base_url}/workflows/{workflow_id}"
        try:
            response = requests.get(url, headers=self.headers, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching workflow {workflow_id}: {e}")
            return None

    def get_executions(self, limit=10):
        """Fetch latest executions."""
        url = f"{self.base_url}/executions"
        params = {"limit": limit}
        try:
            response = requests.get(url, headers=self.headers, params=params, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching executions: {e}")
            return None

def main():
    # Initialize the API client
    n8n = N8nAPI()
    
    print("--- n8n API Example ---")
    
    if not n8n.api_key:
        print("Error: N8N_API_KEY not found in environment variables.")
        print("Please copy .env.example to .env and fill in your API key.")
        return

    # 1. List Workflows
    print("\nFetching workflows...")
    workflows = n8n.get_workflows()
    if workflows and "data" in workflows:
        print(f"Found {len(workflows['data'])} workflows.")
        for wf in workflows['data'][:5]:  # Show first 5
            print(f"- {wf.get('name')} (ID: {wf.get('id')})")
    
    # 2. List Executions
    print("\nFetching latest executions...")
    executions = n8n.get_executions(limit=5)
    if executions and "data" in executions:
        print(f"Latest {len(executions['data'])} executions:")
        for exe in executions['data']:
            print(f"- ID: {exe.get('id')}, Status: {exe.get('status')}, Workflow: {exe.get('workflowId')}")

if __name__ == "__main__":
    main()
