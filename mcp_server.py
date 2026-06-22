from fastmcp import FastMCP
from core.schema_checker import compare_schemas
from core.detector import detect_anomalies
from core.health_report import generate_health_report

mcp = FastMCP("ETL Validator")


@mcp.tool()
def check_schema_drift(baseline_path: str, current_path: str) -> str:
    """
    Detect schema drift between two CSV dataset versions.
    Returns a plain-text summary of added/removed columns and type changes.
    """
    drift = compare_schemas(baseline_path, current_path)
    return drift.to_text()


@mcp.tool()
def detect_data_anomalies(dataset_path: str) -> str:
    """
    Detect statistical anomalies in a CSV dataset.
    Checks for null spikes (>5% missing) and IQR-based outliers.
    """
    report = detect_anomalies(dataset_path)
    return report.to_text()


@mcp.tool()
def generate_pipeline_health_report(baseline_path: str, current_path: str) -> str:
    """
    Run a complete ETL pipeline health check.
    Combines schema drift detection, anomaly detection, and an AI-generated summary.
    """
    drift = compare_schemas(baseline_path, current_path)
    anomalies = detect_anomalies(current_path)
    return generate_health_report(drift.to_text(), anomalies.to_text())


if __name__ == "__main__":
    mcp.run()