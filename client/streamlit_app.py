import streamlit as st
import asyncio
import nest_asyncio
from client import run_agent

# Apply nest_asyncio to handle Streamlit's event loop
nest_asyncio.apply()

st.title("GitHub Issue Manager")

# Initialize session state for chat history and repo URL
if "messages" not in st.session_state:
    st.session_state.messages = []
if "repo_url" not in st.session_state:
    st.session_state.repo_url = ""

# Input form
with st.form("issue_form"):
    repo_url = st.text_input("GitHub Repository URL (e.g., https://github.com/octocat/hello-world)", value=st.session_state.repo_url)
    user_input = st.text_input("Enter your GitHub issue command (e.g., 'Create an issue: Fix login bug', 'List all issues', 'Close issue number 1')")
    submitted = st.form_submit_button("Submit")
    
    if submitted and user_input and repo_url:
        # Update repo URL in session state
        st.session_state.repo_url = repo_url
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": f"Repo: {repo_url}\n{user_input}"})
        
        # Run agent and get response
        response = asyncio.run(run_agent(user_input, repo_url))
        
        # Add agent response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to update the UI
        st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])