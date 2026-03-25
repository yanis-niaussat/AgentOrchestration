import os
import sys
from dotenv import load_dotenv

# Adding root to path to allow importing from triggers package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from triggers.workflow_client import WorkflowClient

load_dotenv()

def trigger_retrieval(query: str = "What stores embeddings?"):
    """
    Triggers the 'Retrieval' n8n workflow.
    """
    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678/api/v1")
    webhook_url = f"{base_url.replace('/api/v1', '')}/webhook/retrieval"
    verify_ssl = os.getenv("N8N_SSL_VERIFY", "true").lower() == "true"
    
    client = WorkflowClient(webhook_url, verify_ssl=verify_ssl)
    
    print(f"Goal: Retrieve relevant documents for query: '{query}'")
    
    try:
        result = client.post(data={"query": query})
        
        docs = []
        if isinstance(result, list) and len(result) > 0:
            docs = result[0].get("docs", [])
        elif isinstance(result, dict):
            docs = result.get("docs", [])
            
        if docs:
            print("--- Top Retrieved Document ---")
            print(docs[0].get("page_content", docs[0]))
        else:
            print("No documents found or unsupported response format.")
            print("Response:", result)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    user_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What stores embeddings?"
    trigger_retrieval(user_query)
