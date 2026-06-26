# GenAI ETL Validator

An agentic ETL validation tool that detects schema drift, flags data anomalies, and generates natural-language pipeline health reports using LLaMA 3 via Groq. Exposes validation tools as an MCP server for integration with MCP-compatible clients.

---

## What it does

- **Schema drift detection**: compares two CSV datasets and identifies added/removed columns and data type changes
- **Anomaly detection**: flags null spikes (>5% missing) and extreme outliers using the IQR method (3x boundary)
- **Health report generation**: sends findings to an LLM that writes a plain-English summary with risk level and recommended actions
- **LangChain agent**: autonomously decides which tools to run based on a natural language query
- **MCP server**: exposes all three validation tools over the Model Context Protocol
- **Streamlit UI**: file upload interface with tabbed results and report download

---

## Tech stack

| Component | Tool |
|-----------|------|
| LLM | LLaMA 3.1 8B Instant via Groq (free) |
| Agent framework | LangChain Classic |
| MCP server | FastMCP |
| UI | Streamlit |
| Data | Pandas, NumPy |

---

## Project structure

```
GenAI-ETL-Validator/
├── .env                      # GROQ API key (not committed)
├── gen_data.py               # Generates synthetic baseline + anomalous datasets for testing
├── agent.py                  # LangChain agent with three tools (CLI interface)
├── app.py                    # Streamlit UI
├── mcp_server.py             # FastMCP server exposing tools over MCP
├── data/
│   ├── baseline.csv          # "Yesterday's" clean dataset
│   └── current.csv           # "Today's" dataset with drift + anomalies injected
└── core/
    ├── drift_checker.py      # Schema comparison logic
    ├── anomaly_detector.py   # Null + outlier detection
    └── health_report.py      # LLM health report generation
```

---

## Setup

### 1. Install dependencies

```bash
pip install langchain langchain-groq langchain-classic langchain-core pandas numpy streamlit fastmcp python-dotenv
```

### 2. Get a free Groq API key

Sign up at [console.groq.com](https://console.groq.com), create an API key, and add it to a `.env` file:

```
vGroqAPIKey=your_key_here
```

### 3. Generate sample data

```bash
python gen_data.py
```

This creates `data/baseline.csv` (clean) and `data/current.csv` with the following issues injected:
- `date` column renamed to `transaction_date`
- `loyalty_score` column added
- `region` column dropped
- 50 null values in `age`
- 10 extreme outliers in `amount` (values in the millions)
- `age` data type changed from int to string

---

## Running the project

### Option A: Streamlit UI

```bash
streamlit run app.py
```

- Upload two CSVs (baseline and current), or check "Use sample data"
- Click **Run Validation**
- Results appear across three tabs: Schema Drift, Anomalies, LLM Report
- Download the health report as a `.md` file

> Note: Streamlit reruns the entire script on every UI interaction: this is expected behaviour.

### Option B: LangChain Agent (CLI)

```bash
python agent.py
```

The agent has three tools available. The docstring on each tool tells the LLM when to use it: this is how the agent autonomously decides which checks to run without being explicitly told.

```
You: Run a full health check on data/baseline.csv vs data/current.csv
You: Just check for schema drift between data/baseline.csv and data/current.csv
You: Are there any anomalies in data/current.csv?
```

> Note: `AgentExecutor` from `langchain_classic` is used here. Newer LangChain versions combine `create_tool_calling_agent` and `AgentExecutor` into a single `create_agent` call, but classic is used here for explicitness.

### Option C: MCP server

```bash
python mcp_server.py
```

Exposes three MCP tools: `schemaDrift`, `anomalies`, `healthReport`.

To test programmatically:

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("mcp_server.py") as client:
        result = await client.call_tool("healthReport", {
            "base_path": "data/baseline.csv",
            "curr_path": "data/current.csv"
        })
        print(result.content[0].text)

asyncio.run(main())
```

---

## How each module works

### `core/drift_checker.py`

Extracts the schema (column to dtype mapping) from both CSVs and compares them. Returns a `SchemaDrift` dataclass with added columns, removed columns, and type changes. The `llmText()` method formats findings as plain text for the LLM: `', '.join(list)` is used to expand lists into comma-separated strings.

### `core/anomaly_detector.py`

**Null detection:** flags any column where null percentage exceeds 5%.

**Outlier detection:** uses the IQR method on all numeric columns. Uses a 3x IQR boundary (instead of the standard 1.5x) to catch only *extreme* outliers, skipping columns with fewer than 10 values as statistically too small. Returns an `anomalyList` dataclass with full outlier details including the actual outlier values, min/max, and fence values.

### `core/health_report.py`

Uses a `ChatPromptTemplate` with two roles: system (senior data engineer persona) and human (the findings). The `|` operator chains the prompt and LLM into a LangChain runnable: `chain = REPORT_PROMPT | llm` is equivalent to passing the prompt directly to the LLM. `temperature=0.3` adds a small amount of creativity to the report writing without making it unpredictable.

### `agent.py`

The `MessagesPlaceholder` in the prompt stores all tool outputs and intermediate steps and passes them back to the LLM so it can reason across multiple tool calls. `create_tool_calling_agent` gives the LLM awareness of available tools; `AgentExecutor` gives it the runtime ability to actually call them: these are two separate concerns.