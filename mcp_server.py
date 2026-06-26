from fastmcp import FastMCP
from core.drift_checker import driftChecker
from core.anomaly_detector import detectAnomaly
from core.health_report import generateHealthReport

mcp = FastMCP('ETL Validator')

@mcp.tool
def schemaDrift(base_path : str, curr_path:str) -> str:
    drift = driftChecker(base_path, curr_path)
    return drift.llmText()

@mcp.tool
def anomalies(curr_path: str) -> str:
    anomaly = detectAnomaly(curr_path)
    return anomaly.llmText()

@mcp.tool
def healthReport(base_path: str, curr_path: str) -> str:
    drift = driftChecker(base_path, curr_path)
    anomaly = detectAnomaly(curr_path)
    report = generateHealthReport(drift.llmText(), anomaly.llmText())
    return report

if __name__ == '__main__':
    mcp.run()