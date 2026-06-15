import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class AnomalyReport:
    null_spikes: Dict[str, dict] = field(default_factory=dict)
    outlier_columns: Dict[str, dict] = field(default_factory=dict)
    has_anomalies: bool = False

    def to_text(self) -> str:
        if not self.has_anomalies:
            return "No anomalies detected."

        lines = ["Anomalies detected:"]
        if self.null_spikes:
            lines.append("  Null spikes (>5% missing):")
            for col, info in self.null_spikes.items():
                lines.append(
                    f"    '{col}': {info['null_pct']:.1f}% nulls ({info['null_count']} rows)"
                )
        if self.outlier_columns:
            lines.append("  Statistical outliers (IQR method):")
            for col, info in self.outlier_columns.items():
                lines.append(
                    f"    '{col}': {info['outlier_count']} outliers "
                    f"(max={info['max_value']:.2f}, expected ≤ {info['upper_fence']:.2f})"
                )
        return "\n".join(lines)


def detect_anomalies(dataset_path: str, null_threshold: float = 0.05) -> AnomalyReport:
    """
    Run anomaly checks on a single CSV file.
    - null_threshold: flag columns where null % exceeds this (default 5%)
    """
    df = pd.read_csv(dataset_path)
    report = AnomalyReport()
    n = len(df)

    # --- Null spike detection ---
    for col in df.columns:
        null_count = df[col].isna().sum()
        null_pct = null_count / n
        if null_pct > null_threshold:
            report.null_spikes[col] = {
                "null_count": int(null_count),
                "null_pct": null_pct * 100,
            }

    # --- Outlier detection (IQR method on numeric columns) ---
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 10:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 3 * iqr   # using 3× IQR for extreme outliers
        upper = q3 + 3 * iqr
        outliers = series[(series < lower) | (series > upper)]
        if len(outliers) > 0:
            report.outlier_columns[col] = {
                "outlier_count": len(outliers),
                "max_value": float(series.max()),
                "upper_fence": float(upper),
            }

    report.has_anomalies = bool(report.null_spikes or report.outlier_columns)
    return report


# test
if __name__ == "__main__":
    report = detect_anomalies("data/current.csv")
    print(report.to_text())