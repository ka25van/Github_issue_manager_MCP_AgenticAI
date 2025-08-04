import asyncio
import os
import re
import requests
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from langchain_core.tools import Tool
from pydantic.v1 import BaseModel, Field
from typing import List, Dict

load_dotenv()

# Pydantic models for tool inputs (same as server)
class CreateIssueInput(BaseModel):
    repo: str = Field(description="GitHub repository in owner/repo format")
    title: str = Field(description="Title of the issue")
    body: str = Field(default="", description="Body of the issue")

class ListIssuesInput(BaseModel):
    repo: str = Field(description="GitHub repository in owner/repo format")

class CloseIssueInput(BaseModel):
    repo: str = Field(description="GitHub repository in owner/repo format")
    issue_number: int = Field(description="Issue number to close")

def parse_repo_url(repo_url: str) -> str:
    """Extract owner/repo from a GitHub URL."""
    pattern = r"https?://github\.com/([^/]+)/([^/]+)"
    match = re.match(pattern, repo_url)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return ""

async def fetch_tools():
    """Fetch tools from the custom /tools endpoint."""
    tool_server_url = os.getenv("TOOL_SERVER_URL", "http://localhost:8000/tools")
    response = requests.get(tool_server_url)
    if response.status_code == 200:
        tools_data = response.json().get("tools", [])
        tools = []
        for tool_data in tools_data:
            if tool_data["name"] == "create_issue":
                tools.append(Tool.from_function(
                    func=create_issue,
                    name="create_issue",
                    description=tool_data["description"],
                    args_schema=CreateIssueInput
                ))
            elif tool_data["name"] == "list_issues":
                tools.append(Tool.from_function(
                    func=list_issues,
                    name="list_issues",
                    description=tool_data["description"],
                    args_schema=ListIssuesInput
                ))
            elif tool_data["name"] == "close_issue":
                tools.append(Tool.from_function(
                    func=close_issue,
                    name="close_issue",
                    description=tool_data["description"],
                    args_schema=CloseIssueInput
                ))
        return tools
    return []

# Define tool functions (same as server for client-side execution)
def create_issue(repo: str, title: str, body: str = "") -> str:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    url = f"https://api.github.com/repos/{repo}/issues"
    data = {"title": title, "body": body}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        issue_number = response.json()["number"]
        return f"Issue '{title}' created with number {issue_number}."
    return f"Failed to create issue: {response.status_code} - {response.text}"

def list_issues(repo: str) -> List[Dict[str, str]]:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    url = f"https://api.github.com/repos/{repo}/issues?state=open"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        issues = [
            {"number": str(issue["number"]), "title": issue["title"], "body": issue["body"] or ""}
            for issue in response.json()
        ]
        return issues
    return []

def close_issue(repo: str, issue_number: int) -> str:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    data = {"state": "closed"}
    response = requests.patch(url, json=data, headers=headers)
    if response.status_code == 200:
        return f"Issue {issue_number} closed."
    return f"Failed to close issue: {response.status_code} - {response.text}"

async def run_agent(query: str, repo_url: str):
    """Process a user query using the LangGraph agent."""
    repo = parse_repo_url(repo_url)
    if not repo:
        return "Invalid GitHub repository URL."

    # Initialize LLM
    llm = ChatOllama(model=os.getenv("OLLAMA_MODEL"), temperature=0.6)

    # Fetch tools
    tools = await fetch_tools()
    
    # Create ReAct agent
    agent = create_react_agent(llm, tools)
    
    # Process query with repo context
    enhanced_query = f"Repository: {repo}\n{query}"
    response = await agent.ainvoke({"messages": [{"role": "user", "content": enhanced_query}]})
    
    # Extract the final AI message
    for message in response["messages"]:
        if message.__class__.__name__ == "AIMessage" and message.content:
            return message.content
    return "No response generated."

if __name__ == "__main__":
    # Example usage
    query = "Create an issue: Fix login bug"
    repo_url = "https://github.com/octocat/hello-world"
    result = asyncio.run(run_agent(query, repo_url))
    print(result)