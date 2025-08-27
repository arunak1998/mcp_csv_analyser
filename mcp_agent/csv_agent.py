import asyncio
import os
from textwrap import dedent
from typing import Optional
import time
import asyncio
import traceback
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
load_dotenv()




# Instructions for the CSV analysis agent
from textwrap import dedent

INSTRUCTIONS = dedent(
    """\
    You are a smart CSV data analyst assistant with access to CSV files through MCP tools.

    Your job is to:
    1. Inspect the available CSV files and their structure before answering.
       - Use `get_files_list` to see what files are available.
       - Use `read_file` (or equivalent tool) to preview the data.
    2. Identify the columns and their data types.
       - Confirm the column names before using them.
       - If column names are unclear or missing, ask for clarification and suggest likely matches.
    3. Answer user questions by analyzing the CSV data.
       - Compute summaries such as counts, averages, minimums/maximums, distributions, or trends.
       - Compare values across columns if relevant.
    4. Respond with clear, human-friendly summaries.
       - Highlight key numbers, trends, or insights.
       - Keep the answer concise and easy to understand.
       - Optionally suggest a visualization (e.g., “This could be shown as a line chart.”).

     Constraints:
    - Only analyze and summarize data; do not modify files.
    - Always validate that the requested columns exist in the CSV before using them.
    - If the request references missing columns, say so clearly and suggest alternatives.
    - Keep reasoning compact; do not generate more than 8000 tokens during analysis to avoid token-limit issues.

    Output requirements:
    - Provide a short, helpful, human-readable summary tied directly to the CSV’s verified columns.
    - Do not return raw tables unless the user explicitly asks.
    - Prefer insights over dumps.

    Examples of user queries:
    - "What is the average price in the dataset?"
    - "Which product category has the most rows?"
    - "Show me the trend of sales over time."
    - "What are the top 5 customers by total spend?"

    Begin by checking the files and columns, then proceed to answer.
    """
)


# Configuration
MODEL_ID = os.getenv("MODEL_ID", "openai/gpt-oss-120b")
MODEL_API_KEY = os.getenv("GROQ_API_KEY")
if not MODEL_API_KEY:
    raise ValueError("MODEL_API_KEY environment variable is not set.")

async def run_agent(message: str, csv_path: str,tools) -> str:
    """
    Run the CSV analysis agent against your MCP server, pointing at csv_path.
    """
    REPO_ROOT = "/mnt/c/workspaces/mcpserver"


    try:
        print("Discovering tools...")
        tools_by_server = tools
    except Exception as e:
        print("\nDiscovery failed:")
        print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
        return
    for tool in tools_by_server:
        name = getattr(tool, "name", "<unknown>")
        desc = (getattr(tool, "description", "") or "").strip()
        print(f"- {name} :: {desc}")

    # Create OpenAI client
    llm = ChatGroq(model=MODEL_ID, api_key=MODEL_API_KEY)

    # Create assistant agent with MCP tools
    agent = create_react_agent(model=llm, tools=tools_by_server, prompt=INSTRUCTIONS)

    try:
        start_time = time.perf_counter()  # ⏱ start

        # Run the agent with the user's question
        response = await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": message}
                ]
            }
        )

        end_time = time.perf_counter()  # ⏱ end
        elapsed = end_time - start_time
        print(f"Agent run took {elapsed:.2f} seconds")

        return response["messages"][-1].content

    except Exception as e:
        end_time = time.perf_counter()  # ensure timing even on error
        elapsed = end_time - start_time
        print(f"Agent run failed after {elapsed:.2f} seconds with error: {e!r}")
        # Optionally re-raise or return a fallback
        raise

    finally:
        print("Agent run completed with input:", message)
        if response is not None:
            print("Full agent response:", response)
        else:
            print("No response object was created.")
# async def main():
#     """
#     Example usage of the agent.
#     """
#     csv_path = "/mnt/c/workspaces/mcpserver/predicted_prices.csv"
#     question = "can you give the file you have the access?"

#     try:
#         response = await run_agent(question, csv_path)
#         print(f"Agent Response: {response}")
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     asyncio.run(main())
