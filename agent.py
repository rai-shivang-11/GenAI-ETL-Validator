import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from core.schema_checker import compare_schemas
from core.detector import detect_anomalies
from core.health_report import generate_health_report

load_dotenv()

# ── Tool definitions ────────────────────────────────────────────────────────

@tool
def schema_drift_tool(baseline_path: str, current_path: str) -> str:
    """
    Compare two CSV datasets and detect schema drift.
    Use this when the user wants to check for column changes, renames, or type changes.
    Returns a plain-text summary of all schema differences found.
    """
    drift = compare_schemas(baseline_path, current_path)
    return drift.to_text()


@tool
def anomaly_detection_tool(dataset_path: str) -> str:
    """
    Detect statistical anomalies in a CSV dataset.
    Use this to check for null spikes, outliers, or data quality issues.
    Returns a plain-text summary of all anomalies found.
    """
    report = detect_anomalies(dataset_path)
    return report.to_text()


@tool
def full_pipeline_health_tool(baseline_path: str, current_path: str) -> str:
    """
    Run a complete pipeline health check: schema drift + anomaly detection + LLM summary.
    Use this when the user wants a full end-to-end pipeline health report.
    Returns a natural-language health report.
    """
    drift = compare_schemas(baseline_path, current_path)
    anomalies = detect_anomalies(current_path)
    report = generate_health_report(drift.to_text(), anomalies.to_text())
    return report


# ── Agent setup ─────────────────────────────────────────────────────────────

def build_agent() -> AgentExecutor:
    llm = ChatGroq(
        model="llama3-8b-8192",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    tools = [schema_drift_tool, anomaly_detection_tool, full_pipeline_health_tool]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an ETL pipeline validation agent.
You have access to tools to check schema drift, detect anomalies, and generate health reports.
When given file paths, use the appropriate tool(s) to validate the pipeline.
Always explain what you found in clear, non-technical terms."""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


# ── CLI runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    agent_executor = build_agent()

    print("\n=== ETL VALIDATOR AGENT ===")
    print("Type your query or press Ctrl+C to exit\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            result = agent_executor.invoke({"input": user_input})
            print(f"\nAgent: {result['output']}\n")
        except KeyboardInterrupt:
            print("\nExiting.")
            break