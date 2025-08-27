import os
import asyncio
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
# Import your compiled graph builder
from dashboard_agent import build_pipeline_graph
CUSTOM_TEMP_DIR = "/mnt/c/workspaces/mcpserver/temp/"
os.makedirs(CUSTOM_TEMP_DIR, exist_ok=True)
# Simple async runner for Streamlit
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

CSV_MCP_SERVER = {"csv_analyst": {"url": "http://localhost:8050/sse", "transport": "sse",}}

def init_mcp_tools():
    client = MultiServerMCPClient(CSV_MCP_SERVER)
    tools_by_server = asyncio.run(client.get_tools())
    return tools_by_server

# Initialize once in session_state
if "mcp_tools" not in st.session_state:
    st.session_state.mcp_tools = init_mcp_tools()

# Usage
tool = st.session_state.mcp_tools


st.set_page_config(page_title="CSV → Dashboard", layout="wide")
st.title("CSV → Dashboard (Simple)")

# 1) Upload CSV
st.subheader("Upload CSV")
csv_file = st.file_uploader("Choose a CSV file", type=["csv"])

csv_path = None
if csv_file is not None:
    # Persist to a temp path

    csv_path = os.path.join(CUSTOM_TEMP_DIR, f"uploaded_{csv_file.name}")
    with open(csv_path, "wb") as f:
        f.write(csv_file.getbuffer())
    st.success(f"Uploaded: {csv_file.name}")

# 2) Enter a question/prompt
st.subheader("Question")
default_q = "Analyze price trends over Age and top players by base price."
query = st.text_input("What should the dashboard show?", value=default_q)

# 3) Generate button
if st.button("Generate Dashboard"):
    if not csv_path:
        st.error("Please upload a CSV first.")
    else:
        with st.spinner("Generating dashboard..."):
            try:
                # Build pipeline
                pipeline = build_pipeline_graph()

                # Initial state: messages + csv_file_path
                init_state = {
                    "messages": [HumanMessage(content=query)],
                    "csv_file_path": csv_path,
                    "tool":tool
                }

                # Run the graph
                result = run_async(pipeline.ainvoke(init_state))

                # Try html from state
                html = result['messages'][-1].content

                # Fallback to last AIMessage content
                if not html:
                    msgs = result.get("messages", [])
                    last_ai = next((m for m in reversed(msgs) if isinstance(m, AIMessage)), None)
                    if last_ai:
                        html = last_ai.content

                if html:



                    st.components.v1.html(html, height=1000, scrolling=True)
                    st.success("Dashboard generated!")
                else:
                    st.error("No HTML returned from pipeline.")
                    st.write("Result keys:", list(result.keys()))
            except Exception as e:
                st.error(f"Failed: {e}")
