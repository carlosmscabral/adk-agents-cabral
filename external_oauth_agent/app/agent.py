from google.adk.agents import Agent
from .tools import fetch_protected_financial_data

# The main agent using the ADK Python SDK
root_agent = Agent(
    name="FinancialDataAssistant",
    model="gemini-3-flash-preview",
    description="An assistant that helps users retrieve their protected financial data.",
    instruction="""
    You are a helpful Financial Assistant. Your job is to fetch and summarize the user's financial data.
    You MUST use the `fetch_protected_financial_data` tool to get the data.
    If the tool returns an error, especially regarding missing tokens or unauthorized access, politely inform the user that there was an issue accessing their secure data.
    """,
    tools=[fetch_protected_financial_data]
)