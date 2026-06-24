import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq                                                     # To load model of our agent
from langchain_classic.agents import AgentExecutor,create_tool_calling_agent            # Activates agent | Creates agent (Prompt + LLM + Tools)
from langchain_core.tools import tool                                                   # To define functions as tools for LLM agent                                                    
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder              # To structure prompts | To pass tool outputs or chat history to the agent
from core.drift_checker import driftChecker
from core.anomaly_detector import detectAnomaly
from core.health_report import generateHealthReport

load_dotenv()

# For AgentExecutor classic langchain used, newer version has create_agent that combies create_tool_calling_agent and AgentExecutor

@tool
def schema_drift_tool(baseline_path: str, current_path: str) -> str:                    #The doc string helps LLM decide which tool to use
    """
    Compare two CSV datasets and detect schema drift.
    Use this when the user wants to check for column changes, renames, or type changes.
    Returns a plain-text summary of all schema differences found.
    """
    drift = driftChecker(baseline_path, current_path)
    return drift.llmText()

@tool
def anomaly_detector_tool(dataset_path: str) -> str:
    """
    Detect statistical anomalies in a CSV dataset.
    Use this to check for null spikes, outliers, or data quality issues.
    Returns a plain-text summary of all anomalies found.
    """
    anomaly = detectAnomaly(dataset_path)
    return anomaly.llmText()

@tool
def health_report_tool(baseline_path: str, current_path: str) -> str:
    """
    Run a complete pipeline health check: schema drift + anomaly detection + LLM summary.
    Use this when the user wants a full end-to-end pipeline health report.
    Returns a natural-language health report.
    """
    drift = driftChecker(baseline_path, current_path)
    anomaly = detectAnomaly(dataset_path)
    report = generateHealthReport(drift, anomaly)
    return report

def build_agent() -> AgentExeceutor:
    llm = ChatGroq(
        model = 'llama-3.1-8b-instant',
        temperature = 0,                        # To remove randomness
        api_key = os.getenv('vGroqAPIKey')
    )

    tools = [schema_drift_tool, anomaly_detector_tool, health_report_tool]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an ETL pipeline validation agent.
You have access to tools to check schema drift, detect anomalies, and generate health reports.
When given file paths, use the appropriate tool(s) to validate the pipeline.
Always explain what you found in clear, non-technical terms."""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")                                   # This stores all the tool outputs and passes to the llm
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)                                       # Tools here gives the LLM an idea of the tools present
    return AgentExecutor(agent = agent, tools = tools, verbose = True)                          # Tools here give the agent runtime ability to execute the tools

if __name__ == '__main__':
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