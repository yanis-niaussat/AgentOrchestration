import os
import json
import re
import requests
import time
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Prompt template (mirrors the professor's PromptTemplate approach, but kept
# lightweight so we don't need langchain installed).
# ---------------------------------------------------------------------------

WORKFLOW_TEMPLATE = (
    "Generate a complete, production-ready n8n workflow JSON for the following use case:\n\n"
    "{description}\n\n"
    "Requirements:\n"
    "- Include all necessary nodes (trigger, logic, integrations, response)\n"
    "- Replace every real credential / API key with a clear placeholder "
    "(e.g. YOUR_OPENAI_API_KEY, YOUR_SLACK_BOT_TOKEN)\n"
    "- Output ONLY the raw JSON — no markdown, no explanation"
)


def build_prompt(description: str) -> str:
    """Fill the prompt template with the user's workflow description."""
    return WORKFLOW_TEMPLATE.format(description=description.strip())


# ---------------------------------------------------------------------------
# n8n client
# ---------------------------------------------------------------------------

class N8nWorkflowGenerator:
    """Sends a workflow description to n8n and returns the generated JSON."""

    WEBHOOK_PATH = "workflow-generator"

    def __init__(self):
        base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678").rstrip("/")
        self.webhook_url = f"{base_url}/webhook/{self.WEBHOOK_PATH}"
        api_base = base_url + "/api/v1"
        self.api_key = os.getenv("N8N_API_KEY")
        self.api_headers = {
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        self.api_base = api_base

    # ------------------------------------------------------------------
    # Webhook execution
    # ------------------------------------------------------------------

    def trigger(self, description: str) -> Optional[str]:
        """
        POST the description to the webhook and return the raw response text.
        The workflow uses responseMode='lastNode', so n8n blocks until the AI
        finishes and sends the result back in this same HTTP response.
        Timeout is set generously (180s) to accommodate slow LLM responses.
        """
        prompt = build_prompt(description)
        try:
            print("  Waiting for AI response (this may take up to a minute) …", end="", flush=True)
            resp = requests.post(
                self.webhook_url,
                json={"description": prompt},
                timeout=180,
            )
            print(" done.")
            resp.raise_for_status()
            # n8n returns the last node output as JSON or plain text
            try:
                body = resp.json()
                # Agent output is usually in body[0]['output'] or body['output']
                if isinstance(body, list) and body:
                    body = body[0]
                for key in ("output", "text", "message", "response"):
                    if isinstance(body, dict) and key in body:
                        return str(body[key])
                # Fall back to the full JSON string
                return json.dumps(body)
            except Exception:
                return resp.text
        except Exception as exc:
            print(f"\n  [trigger error] {exc}")
            return None

    # ------------------------------------------------------------------
    # Poll the execution result
    # ------------------------------------------------------------------

    def _get_workflow_id(self) -> Optional[str]:
        """Return the ID of the first workflow found via the REST API."""
        try:
            resp = requests.get(
                f"{self.api_base}/workflows",
                headers=self.api_headers,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            return data[0]["id"] if data else None
        except Exception as exc:
            print(f"  [api error] {exc}")
            return None

    def _latest_execution(self, workflow_id: str) -> Optional[dict]:
        """Fetch the most recent execution for a workflow."""
        try:
            resp = requests.get(
                f"{self.api_base}/executions",
                headers=self.api_headers,
                params={"workflowId": workflow_id, "limit": 1, "includeData": "true"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            return data[0] if data else None
        except Exception as exc:
            print(f"  [api error] {exc}")
            return None

    def _extract_text(self, execution: dict) -> Optional[str]:
        """Walk the execution run-data tree and return the first text/output value."""
        try:
            run_data = (
                execution.get("data", {})
                .get("resultData", {})
                .get("runData", {})
            )
            for _node, runs in run_data.items():
                for run in runs or []:
                    for main in run.get("data", {}).get("main", []):
                        for item in main or []:
                            j = item.get("json", {})
                            for key in ("output", "text", "message", "response"):
                                if key in j:
                                    return str(j[key])
        except Exception as exc:
            print(f"  [extract error] {exc}")
        return None

    def poll(self, workflow_id: str, retries: int = 30, delay: float = 2.0) -> Optional[str]:
        """Poll until the latest execution finishes, then return raw text output."""
        terminal = {"success", "error", "crashed", "cancelled"}
        for attempt in range(retries):
            time.sleep(delay)
            print(f"  Polling … attempt {attempt + 1}/{retries}", end="\r")
            execution = self._latest_execution(workflow_id)
            if execution and execution.get("status") in terminal:
                print()  # newline after \r
                if execution["status"] != "success":
                    print(f"  [warn] Execution ended with status: {execution['status']}")
                return self._extract_text(execution)
        print()
        return None


# ---------------------------------------------------------------------------
# JSON extraction helper
# ---------------------------------------------------------------------------

def extract_json(raw: str) -> Optional[dict]:
    """
    Try to parse the raw AI response as JSON.
    Handles cases where the model wraps the JSON in markdown fences.
    """
    # 1. Direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown fences: ```json ... ``` or ``` ... ```
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Find the first top-level JSON object in the string
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    gen = N8nWorkflowGenerator()

    if not gen.api_key:
        print("Error: N8N_API_KEY not set in .env")
        return

    print("=" * 60)
    print("  N8N WORKFLOW GENERATOR")
    print("  Describe what you want to automate and get back a")
    print("  complete n8n workflow JSON, ready to import.")
    print("=" * 60)

    description = input("\nDescribe your workflow:\n> ").strip()
    if not description:
        print("No description provided. Exiting.")
        return

    print(f"\nBuilding prompt and triggering the n8n workflow …\n")

    # Trigger the generation — response arrives inline (responseMode: lastNode)
    raw_output = gen.trigger(description)
    if not raw_output:
        print("Failed to reach the n8n webhook. Is n8n running?")
        return

    # Try to parse the output as JSON
    workflow_json = extract_json(raw_output)

    print("=" * 60)
    print("  GENERATED WORKFLOW")
    print("=" * 60)

    if workflow_json:
        pretty = json.dumps(workflow_json, indent=2)
        print(pretty)

        # Offer to save
        save = input("\nSave this workflow to a file? [y/N] ").strip().lower()
        if save == "y":
            # Derive a safe filename from the workflow name or description
            wf_name = workflow_json.get("name", description[:40])
            safe_name = re.sub(r"[^\w\-]", "_", wf_name).strip("_").lower()
            output_path = os.path.join("workflows", f"{safe_name}.json")
            os.makedirs("workflows", exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(workflow_json, f, indent=2)
            print(f"\nSaved to: {output_path}")
    else:
        # The model returned free-form text instead of pure JSON
        print(raw_output)
        print("\n[Note] The response was not valid JSON. Paste the above into n8n manually.")


if __name__ == "__main__":
    main()
