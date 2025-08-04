import os
import requests
from typing import List, Dict
from fastapi import FastAPI
from langchain_core.tools import tool
from dotenv import load_dotenv
import uvicorn
from pydantic.v1 import BaseModel, Field

load_dotenv()

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Tool server is running"}

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# Pydantic models for tool inputs
class CreateIssueInput(BaseModel):
    repo: str = Field(description="GitHub repository in owner/repo format")
    title: str = Field(description="Title of the issue")
    body: str = Field(default="", description="Body of the issue")

class ListIssuesInput(BaseModel):
    repo: str = Field(description="GitHub repository in owner/repo format")

class CloseIssueInput(BaseModel):
    repo: str = Field(description="GitHub repository in owner/repo format")
    issue_number: int = Field(description="Issue number to close")

@tool(args_schema=CreateIssueInput)
def create_issue(repo: str, title: str, body: str = "") -> str:
    """Create a new issue in the specified GitHub repository (format: owner/repo)."""
    url = f"https://api.github.com/repos/{repo}/issues"
    data = {"title": title, "body": body}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        issue_number = response.json()["number"]
        return f"Issue '{title}' created with number {issue_number}."
    return f"Failed to create issue: {response.status_code} - {response.text}"

@tool(args_schema=ListIssuesInput)
def list_issues(repo: str) -> List[Dict[str, str]]:
    """List all open issues in the specified GitHub repository (format: owner/repo)."""
    url = f"https://api.github.com/repos/{repo}/issues?state=open"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        issues = [
            {"number": str(issue["number"]), "title": issue["title"], "body": issue["body"] or ""}
            for issue in response.json()
        ]
        return issues
    return []

@tool(args_schema=CloseIssueInput)
def close_issue(repo: str, issue_number: int) -> str:
    """Close an issue by its number in the specified GitHub repository (format: owner/repo)."""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    data = {"state": "closed"}
    response = requests.patch(url, json=data, headers=headers)
    if response.status_code == 200:
        return f"Issue {issue_number} closed."
    return f"Failed to close issue: {response.status_code} - {response.text}"

# Expose tools via a custom endpoint
@app.get("/tools")
async def get_tools():
    tools = [create_issue, list_issues, close_issue]
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "args_schema": tool.args_schema.schema() if tool.args_schema else {}
            }
            for tool in tools
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)