import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SchemaDrift:
    added_columns: List[str] = field(default_factory=list)
    removed_columns: List[str] = field(default_factory=list)
    type_changes: Dict[str, dict] = field(default_factory=dict)
    has_drift: bool = False

    def to_text(self) -> str:
        """Convert drift findings to a plain text summary for the LLM."""
        if not self.has_drift:
            return "No schema drift detected."

        lines = ["Schema drift detected:"]
        if self.added_columns:
            lines.append(f"  New columns added: {', '.join(self.added_columns)}")
        if self.removed_columns:
            lines.append(f"  Columns removed: {', '.join(self.removed_columns)}")
        if self.type_changes:
            for col, change in self.type_changes.items():
                lines.append(
                    f"  '{col}' type changed: {change['from']} → {change['to']}"
                )
        return "\n".join(lines)


def extract_schema(df: pd.DataFrame) -> Dict[str, str]:
    """Return column → dtype mapping."""
    return {col: str(dtype) for col, dtype in df.dtypes.items()}


def compare_schemas(baseline_path: str, current_path: str) -> SchemaDrift:
    """Compare two CSV files and return a SchemaDrift object."""
    baseline_df = pd.read_csv(baseline_path)
    current_df = pd.read_csv(current_path)

    baseline_schema = extract_schema(baseline_df)
    current_schema = extract_schema(current_df)

    baseline_cols = set(baseline_schema.keys())
    current_cols = set(current_schema.keys())

    drift = SchemaDrift()

    drift.added_columns = list(current_cols - baseline_cols)
    drift.removed_columns = list(baseline_cols - current_cols)

    # Check type changes on columns present in both
    common_cols = baseline_cols & current_cols
    for col in common_cols:
        if baseline_schema[col] != current_schema[col]:
            drift.type_changes[col] = {
                "from": baseline_schema[col],
                "to": current_schema[col],
            }

    drift.has_drift = bool(
        drift.added_columns or drift.removed_columns or drift.type_changes
    )
    return drift


# test
if __name__ == "__main__":
    drift = compare_schemas("data/baseline.csv", "data/current.csv")
    print(drift.to_text())