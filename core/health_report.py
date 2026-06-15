import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

load_dotenv()


def get_llm():
    return ChatGroq(
        model="llama3-8b-8192",    # free, fast
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY"),
    )


REPORT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior data engineer writing a pipeline health summary.
Your job is to translate raw technical findings into a clear, actionable report.
Be concise. Use plain English. Highlight risk level (Low / Medium / High).
End with 2-3 recommended actions."""),
    ("human", """Here are the findings from today's ETL pipeline run:

--- SCHEMA DRIFT ---
{schema_findings}

--- DATA ANOMALIES ---
{anomaly_findings}

Write a pipeline health summary report.""")
])


def generate_health_report(schema_text: str, anomaly_text: str) -> str:
    """Send findings to LLM and return a natural-language health report."""
    llm = get_llm()
    chain = REPORT_PROMPT | llm
    response = chain.invoke({
        "schema_findings": schema_text,
        "anomaly_findings": anomaly_text,
    })
    return response.content


# test
if __name__ == "__main__":
    schema_text = "Schema drift detected:\n  Columns removed: signup_date\n  'purchase_amt' renamed to 'transaction_value'"
    anomaly_text = "Anomalies detected:\n  Null spikes: 'age' 8% nulls\n  Outliers: 'transaction_value' 10 extreme values"
    report = generate_health_report(schema_text, anomaly_text)
    print(report)