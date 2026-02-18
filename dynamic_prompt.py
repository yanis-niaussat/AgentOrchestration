import os
import requests
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

class N8nPrompt:
    """Simple n8n prompt executor."""
    
    def __init__(self):
        base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678")
        if not base_url.endswith("/api/v1"):
            base_url = base_url.rstrip("/") + "/api/v1"
        self.base_url = base_url
        self.api_key = os.getenv("N8N_API_KEY")
        self.headers = {
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
    
    def execute(self, webhook_path, data):
        """Execute n8n workflow via webhook."""
        webhook_url = self.base_url.replace("/api/v1", "") + f"/webhook/{webhook_path}"
        try:
            response = requests.get(webhook_url, params=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_first_workflow_id(self):
        """Get the first workflow ID."""
        url = f"{self.base_url}/workflows"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            workflows = response.json()
            if workflows and 'data' in workflows and len(workflows['data']) > 0:
                return workflows['data'][0].get('id')
        except Exception as e:
            print(f"Error: {e}")
        return None
    
    def get_result(self, workflow_id):
        """Get the latest execution result."""
        url = f"{self.base_url}/executions"
        params = {"workflowId": workflow_id, "limit": 1, "includeData": "true"}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            executions = response.json()
            
            if executions and 'data' in executions and len(executions['data']) > 0:
                return executions['data'][0]
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def extract_response(self, execution_result):
        """Extract AI text from execution result."""
        try:
            result_data = execution_result.get('data', {}).get('resultData', {})
            run_data = result_data.get('runData', {})
            
            for node_name, node_runs in run_data.items():
                if node_runs and len(node_runs) > 0:
                    for run in node_runs:
                        main_data = run.get('data', {}).get('main', [])
                        for main in main_data:
                            if main:
                                for item in main:
                                    if 'json' in item:
                                        if 'output' in item['json']:
                                            return item['json']['output']
                                        if 'text' in item['json']:
                                            return item['json']['text']
            return None
        except Exception as e:
            print(f"Error extracting response: {e}")
            return None


def main():
    """Ask for topic and get AI response from n8n."""
    n8n = N8nPrompt()
    
    if not n8n.api_key:
        print("Error: N8N_API_KEY not found in .env file")
        return
    
    print("=" * 60)
    print("DYNAMIC PROMPT WITH N8N")
    print("=" * 60)
    
    # Get workflow ID dynamically
    workflow_id = n8n.get_first_workflow_id()
    if not workflow_id:
        print("Error: No workflows found")
        return
    
    topic = input("\n📝 What topic would you like explained? ")
    if not topic.strip():
        print("❌ No topic provided.")
        return
    
    print(f"\n🚀 Processing: {topic}")
    print("⏳ Waiting for AI...\n")
    
    # Execute workflow
    response = n8n.execute("dynamic-prompt-fixed", {"topic": topic})
    
    if response:
        # Poll for result
        for attempt in range(10):
            time.sleep(1)
            execution_result = n8n.get_result(workflow_id)
            
            if execution_result:
                status = execution_result.get('status')
                if status in ['success', 'error', 'crashed', 'cancelled']:
                    print("=" * 60)
                    print("AI RESPONSE")
                    print("=" * 60)
                    
                    ai_text = n8n.extract_response(execution_result)
                    if ai_text:
                        print(f"\n{ai_text}\n")
                    else:
                        print("Could not extract response.")
                    return
        
        print("❌ Timeout waiting for execution.")
    else:
        print("❌ Failed to execute workflow.")


if __name__ == "__main__":
    main()