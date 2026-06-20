import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class SchemaDrift:
    added_colums: List[str] = field(default_factory = list)
    removed_columns: List[str] = field(default_factory = list)
    type_changes: Dict[str, dict] = field(default_factory = dict)
    has_drift: bool = False

    def llmText(self):
        if not self.has_drift: return "No schema drift detected"

        lines = ["Schema drift detected:"]
        
        if self.added_colums:
            lines.append(f" New columns added: {', '.join(self.added_colums)}")  # Expands list as string and adds ', ' as a sparator between the elements
        if self.removed_columns:
            lines.append(f" Columns removed: {', '.join(self.removed_columns)}")
        if self.type_changes:
            lines.append(" Data Type Changes:")
            for col, change in self.type_changes.items():
                lines.append(f"  '{col}' column's data type changed from '{change['from']}' to '{change['to']}'")
        
        return '\n'.join(lines)                         # Each element gets added to a new line
    
def schemaExtract(df: pd.DataFrame) -> Dict[str, str]:
    return {col: str(dtype) for col, dtype in df.dtypes.items()}

def driftChecker(baselinePath: str, currentPath: str) -> SchemaDrift:
    df_baseline = pd.read_csv(baselinePath)
    df_current = pd.read_csv(currentPath)

    baselineSchema = schemaExtract(df_baseline)
    currentSchema = schemaExtract(df_current)

    baselineColumns = set(baselineSchema.keys())
    currentColumns = set(currentSchema.keys())

    drift = SchemaDrift()

    drift.added_colums = list(currentColumns - baselineColumns)
    drift.removed_columns = list(baselineColumns - currentColumns)

    commonColumns = baselineColumns & currentColumns

    for col in commonColumns:
        if baselineSchema[col] != currentSchema[col]:
            drift.type_changes[col] = {
                'from': baselineSchema[col],
                'to': currentSchema[col]
            }
    
    drift.has_drift = bool(
        drift.added_colums or drift.removed_columns or drift.type_changes
    )

    return drift

if __name__ == "__main__":
    driftCheck = driftChecker('data/baseline.csv', 'data/current.csv')
    print(driftCheck.llmText())