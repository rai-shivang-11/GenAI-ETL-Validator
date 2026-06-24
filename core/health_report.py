import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

def get_llm():
    return ChatGroq(
        model = 'llama-3.1-8b-instant',
        temperature = 0.3,                      #Determines the creativity level of LLM response
        api_key = os.getenv('vGroqAPIKey')
    )

REPORT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior data engineer writing a pipeline health summary.
Your job is to translate raw technical findings into a clear, actionable report.
Be concise. Use plain English. Highlight risk level (Low / Medium / High).
End with 2-3 recommended actions."""),                                                          #Tuples, first element indicates the assigned role
    ("human", """Here are the findings from today's ETL pipeline run:

--- SCHEMA DRIFT ---
{schema_findings}

--- DATA ANOMALIES ---
{anomaly_findings}

Write a pipeline health summary report.""")                                                     #Triple quotes is for multi-line strings, preserves line breaks
])

def generateHealthReport(schema_text: str, anomaly_text: str) -> str:
    llm = get_llm()
    chain = REPORT_PROMPT | llm                    # Same as llm(REPORT_PROMPT) --> Passes the prompt to the llm runnable (objects that take input and give an output)
    response = chain.invoke({
        'schema_findings':  schema_text,
        'anomaly_findings': anomaly_text
    })

    return response.content

if __name__ == '__main__':
    schema_text = "Schema drift detected:\n  Columns removed: signup_date\n  'purchase_amt' renamed to 'transaction_value'"
    anomaly_text = "Anomalies detected:\n  Null spikes: 'age' 8% nulls\n  Outliers: 'transaction_value' 10 extreme values"
    report = generateHealthReport(schema_text, anomaly_text)
    print(report)