================================================================================
🌟 **GitHub Issue Manager Architecture** 🌟
================================================================================

<img width="578" height="770" alt="image" src="https://github.com/user-attachments/assets/47853d21-1bd1-4912-a88a-a53f0b8bde88" />




🔥 *Data Flow* 🔥
1. 💻 User types command in Streamlit UI.
2. 🌐 Streamlit sends command to client.py.
3. 🧠 LangGraph Agent (with Llama 3.2) fetches tools from /tools, decides action.
4. 🛠️ Tools call GitHub API to create/list/close issues.
5. 🤖 Ollama llama3.2 provides AI reasoning for LangGraph.
6. 🌐 Response displayed in Streamlit UI, stored in chat history.
================================================================================



