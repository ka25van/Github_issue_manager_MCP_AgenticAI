import os
import requests
from typing import List, Dict
from fastapi import FastAPI
from mcp import tool
from dotenv import load_dotenv
import uvicorn


load_dotenv()

app=FastAPI()

GITHUB_TOKEN=os.getenv("GITHUB_TOKEN")
headers={
    "Authorization":f"Bearer {GITHUB_TOKEN}",
    "Accept":"application/vnd.github.v3+json",
    "X-GitHub-Api-Version":"2022-11-28"
}

@tool()
def create_issue(repo:str, title:str, body:str)->str:
    """Create a new issue in the specified GitHub repository (format: owner/repo)."""
    url = f"https://api.github.com/repos/{repo}/issues"
    data={"title":title, "body":body}
    response=requests.post(url, json=data, headers=headers)
    if response.status_code==201:
        issue_number=response.json()["number"]
        return f"Issue '{title}' created with number {issue_number}"
    return f"Failed to create issue: {response.status_code} - {response.text}"


@tool()
def list_issue(repo:str)-> List[Dict[str,str]]:
    """List all open issues in the specified GitHub repository (format: owner/repo)."""
    url= f"https://api.github.com/repos/{repo}/issues?state=open"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        issues=[
            {"number": issue["number"], "title": issue["title"], "body": issue["body"] or ""}
            for issue in response.json()
        ]
        return issues
    return []

@tool()
def close_issue(repo:str, issue_number:int)->str:
    """Close an issue by its number in the specified GitHub repository (format: owner/repo)."""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    data = {"state": "closed"}
    response = requests.patch(url, json=data, headers=headers)
    if response.status_code == 200:
        return f"Issue {issue_number} closed."
    return f"Failed to close issue: {response.status_code} - {response.text}"
    
if __name__=="__main__":
    uvicorn.run(app,host="0.0.0.0", port=8000)





