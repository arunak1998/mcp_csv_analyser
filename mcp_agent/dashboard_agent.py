import asyncio
import os
import json
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from textwrap import dedent
from typing import Optional, Dict, Any
import traceback
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
from langgraph.errors import GraphRecursionError
from langgraph.graph import StateGraph, END
from langchain_core.tools import BaseTool

from langchain_mcp_adapters.tools import load_mcp_tools
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




load_dotenv()
MODEL_ID = os.getenv("MODEL_ID", "openai/gpt-oss-120b")
if not MODEL_ID:
    raise ValueError("MODEL_ID environment variable is not set.")
MODEL_API_KEY = os.getenv("GROQ_API_KEY")
if not MODEL_API_KEY:
    raise ValueError("MODEL_API_KEY environment variable is not set.")


# Visualization types mapping
VISUALIZATION_TYPES = {
    "time_series": "Data that changes over time (sales trends, user growth)",
    "bar_chart": "Comparing categories or groups (sales by region, products by category)",
    "pie_chart": "Showing composition or proportion (market share, budget allocation)",
    "scatter_plot": "Relationship between two variables (price vs. rating, age vs. salary)",
    "heatmap": "Showing patterns or intensity across multiple dimensions (activity by hour/day)",
    "table": "Detailed individual records or aggregates requiring precise values",
    "gauge": "KPIs with target values (sales goals, customer satisfaction)",
    "funnel": "Sequential process steps with drop-offs (sales funnel, user journey)",
}

# --- OPTIMIZED INSTRUCTIONS WITH CLEAR STOPPING CONDITIONS ---

INSTRUCTIONS_CSV_ANALYSIS_AND_SCHEMA = dedent("""
You are an expert data analyst. Your ONLY task is to analyze the provided CSV schema and return a JSON report.

You will be given:
- A JSON array named "schema", where each item has:
  - "name": column name (string)
  - "dtype": data type (string)
- A "question" string describing what the user wants to analyze.

CRITICAL RULES:
- Do NOT call any tools.
- Analyze ONLY the provided schema (and the question if provided).
- IMMEDIATELY return the JSON report and STOP – no extra text.

SQL CONSTRAINTS (must follow exactly):
- Use FROM self as the table source (never FROM players or any other name).
- Quote identifiers (column names) that contain spaces or special characters with double quotes, e.g. "Base Price (Cr)", "Player Name".
- Use single quotes only for string literals (e.g., WHERE "Country" = 'India').
- Do not use backticks.
- Prefer explicit GROUP BY for any aggregation, and explicit ORDER BY when sorting.
- Example pattern:
  SELECT "Age", AVG("Base Price (Cr)") AS avg_base_price
  FROM self
  GROUP BY "Age"
  ORDER BY "Age"

PROCESS (execute in order, then STOP):
1. Read the provided "schema" array and optional "question".
2. Create the JSON report based on the schema (and tailor to the question if present).
3. Return the JSON and STOP.

JSON FORMAT (return ONLY this JSON, no extra text):
{
  "domain": "Identified domain based on column names",
  "key_metrics": [
    {
      "metric": "Metric Name",
      "description": "What this metric shows",
      "visualization_type": "bar_chart",
      "visualization_rationale": "Why this chart fits",
      "sql": "SELECT ... FROM self WHERE ... GROUP BY ..."
    }
  ],
  "dashboard_components": ["filters", "charts", "tables"]
}
""") + "\n\nVisualization types: " + json.dumps(VISUALIZATION_TYPES)
INSTRUCTIONS_CSV_METRIC_DATA_JSON_ONLY = dedent("""\
You are a data analyst. Execute SQL queries and return results in JSON format.

CRITICAL STOPPING RULES:
- Execute each SQL query EXACTLY ONCE using execute_polars_sql
- After getting ALL query results, format into JSON and STOP
- Do NOT re-execute queries or call tools again
- Do NOT analyze results - just return the data

TASK:
1. Parse the input JSON to get SQL queries
2. Execute each SQL query ONCE with execute_polars_sql
3. Collect all results
4. Return final JSON with all metrics data
5. STOP immediately after returning JSON

RETURN FORMAT (JSON only, no extra text):
{{
  "metrics": [
    {{
      "metric": "Metric name",
      "description": "Description",
      "visualization_type": "chart_type",
      "data": [
        {{"column1": value, "column2": value}}
      ]
    }}
  ]
}}
""")


INSTRUCTIONS_RENDER_DASHBOARD_FROM_DATA = dedent("""
You are a senior dashboard UI engineer.

Input:
- A JSON object containing an array `metrics`.
- Each metric has:
  - `metric` (string): the title,
  - `description` (string): short explanation,
  - `visualization_type` (string): one of `bar_chart`, `time_series`, `pie_chart`, or `table`,
  - `data` (list of row objects): the data to display.

Task:
Generate a **complete, valid HTML document** that renders a responsive dashboard.

Rules:
1. Use Tailwind CSS (via CDN) for styling.
2. Use Chart.js (via CDN) for `bar_chart`, `time_series`, and `pie_chart`.
3. For `table`, render a styled Tailwind table.
4. Each metric should appear in its own card:
   - Card = rounded corners, shadow, padding, margin.
   - Title and description at top.
   - Visualization below.
5. Layout must be mobile-friendly, clean, and centered (use Tailwind containers, `max-w-5xl mx-auto`).
6. Ensure charts/tables auto-resize responsively and avoid horizontal overflow:
   - Wrap each chart canvas inside a `div` with `w-full h-[400px]` (fixed height, responsive width).
   - Add `max-w-full overflow-x-auto` for tables.
   - Use `maintainAspectRatio: false` in Chart.js configs so charts stretch correctly.
7. Avoid extra whitespace. Content should fit inside Streamlit `st.components.v1.html` without scrolling sideways.

Output:
Return only the HTML document string (no markdown, no explanations).
""")

# ─── MCP INIT ──────────────────────────────────────────────────────────────────

# ─── MCP INIT ──────────────────────────────────────────────────────────────────

# _mcp_client = None
# _mcp_tools = None

# async def init_mcp_tools():
#     global _mcp_client, _mcp_tools
#     if _mcp_client is None:
#         _mcp_client = MultiServerMCPClient({
#             "csv_analyst": {"url": "http://localhost:8050/sse", "transport": "sse"}
#         })
#         _mcp_tools = await _mcp_client.get_tools()
#         logger.info("MCP tools initialized")
#     return _mcp_tools

# ─── STATE GRAPH NODES ─────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    messages: Annotated[list[BaseMessage], "add_messages"]
    csv_file_path: str
    tool:BaseTool


async def node_schema(state: PipelineState)->PipelineState:
    try:
        # 1) Load tools and locate get_schema
        tools = state['tool']
        get_schema = next((t for t in tools if t.name == "get_schema"), None)
        if get_schema is None:
            raise RuntimeError("get_schema tool not found")

        # Optional: inspect the tool's input schema at runtime
        # try:
        #     logger.info(f"get_schema input schema: {getattr(get_schema, 'get_input_schema', None)}")
        # except Exception:
        #     pass  # Non-blocking

        # 2) Invoke tool (expects file_location as a string)
        wrapped = await get_schema.ainvoke({
            "file_location": state['csv_file_path'],
            "file_type": "csv"
        })





        # 4) Call LLM to build the metric spec
        llm = ChatGroq(model=MODEL_ID, api_key=MODEL_API_KEY)
        try:
            schema_list = [
                (json.loads(item) if isinstance(item, str) else item)
                for item in wrapped
            ]
        except Exception as e:
            raise ValueError(f"Failed to parse schema items: {e}")

        # Optional sanity checks (keep if you want defensive code)
        if not schema_list:
            raise ValueError("Empty schema returned")
        if not all(isinstance(x, dict) and "name" in x and "dtype" in x for x in schema_list[:2]):
            raise ValueError("Schema items missing required keys after normalization")

        # Use schema_list directly with your instructions
        user_question = state['messages'][-1].content
        print(user_question)
        llm_payload = {
            "schema": schema_list,
            "question": user_question  # can be empty; the prompt must allow this
        }

        # 5) Call LLM to build the metric spec
        llm = ChatGroq(model=MODEL_ID, api_key=MODEL_API_KEY,max_tokens='10151')
        analysis = await llm.ainvoke([
            {"role": "system", "content": INSTRUCTIONS_CSV_ANALYSIS_AND_SCHEMA},
            {"role": "user", "content": json.dumps(llm_payload, ensure_ascii=False)}
        ])



        if not hasattr(analysis, "content") or not analysis.content:
            raise RuntimeError("LLM returned empty content for schema analysis.")

        # 5) Parse spec JSON
        try:
            spec = json.loads(analysis.content)
        except json.JSONDecodeError as je:
            logger.error(f"LLM response not valid JSON: {analysis.content[:300]}...")
            raise ValueError(f"Failed to parse analysis JSON: {je}") from je

        # 6) Validate required keys
        for k in ("key_metrics", "dashboard_components"):
            if k not in spec:
                raise ValueError(f"Analysis JSON missing required key: {k}")

        minimal_spec = {
        "key_metrics": spec.get("key_metrics", []),
        "dashboard_components": spec.get("dashboard_components")
    }
        return {
        "messages": [
        AIMessage(content=json.dumps(minimal_spec, ensure_ascii=False))
    ]
}

    except Exception as e:
        logger.error(f"node_schema failed: {e}")
        # Return a structured error so the graph can decide how to proceed
        return {
            "error": "node_schema_failed",
            "details": str(e)
        }

async def node_execute_sql(state: PipelineState)->PipelineState:
    tools = state['tool']
    exec_tool = next(t for t in tools if t.name == "execute_polars_sql")
    exec_tool.get_input_schema
    # Optional: inspect the tool's input schema at runtime
    try:
        logger.info(f"get_schema input schema: {getattr(exec_tool, 'get_input_schema', None)}")
    except Exception:
        pass  # Non-blocking
    results = []
    messages=state['messages'][-1]
    try:
        payload = json.loads(messages.content)
    except Exception as e:
        raise ValueError(f"Failed to parse AIMessage content as JSON: {e}")
    key_metrics = payload.get("key_metrics", [])
    for m in key_metrics:
        print(f"the query is {m['sql']}")
        data = await exec_tool.ainvoke({
            "file_locations": [state['csv_file_path']],
            "query": m["sql"],
            "file_type": "csv"
            })
        results.append({
            "metric": m["metric"],
            "description": m["description"],
            "visualization_type": m["visualization_type"],
            "data": data or []
        })

    return {
        'messages': [AIMessage(content=results)]}

async def node_render_html(state: PipelineState)->PipelineState:

    messages=state['messages'][-1]

    last_messages=messages.content
    llm = ChatGroq(model=MODEL_ID, api_key=MODEL_API_KEY)
    html_resp = await llm.ainvoke([
        {"role": "system", "content": INSTRUCTIONS_RENDER_DASHBOARD_FROM_DATA},
        {"role": "user", "content": json.dumps({"metrics": last_messages})}
    ])
    return {"messages": [AIMessage(content=html_resp.content)]}

# ─── BUILD & RUN GRAPH ────────────────────────────────────────────────────────

def build_pipeline_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("schema", node_schema)
    graph.add_node("execute_sql", node_execute_sql)
    graph.add_node("render_html", node_render_html)
    graph.add_edge("schema", "execute_sql")
    graph.add_edge("execute_sql", "render_html")
    graph.add_edge("render_html", END)
    graph.set_entry_point("schema")
    return graph.compile()

# async def main():
#     pipeline = build_pipeline_graph()
#     user_input="Analyze Base Price trends over Age "
#     messages = [HumanMessage(content=user_input)]
#     result = await pipeline.ainvoke({
#         "messages": messages,"csv_file_path":"/mnt/c/workspaces/mcpserver/temp/uploaded_predicted_prices.csv"
#     })
#     html = result['messages'][-1]
#     if html:
#         logger.info("Dashboard generated successfully!")

#     else:
#         logger.error("Pipeline failed")

# if __name__ == "__main__":
#     asyncio.run(main())