import numpy as np
import pandas as pd
from dataclass import dataclass, field
from typing import Dict, List

@dataclass
class SchemaDrift:
    added_colums: List[str] = field(default_factory = list)
    removed_columns: List[str] = field(default_factory = list)
    changed_columns: Dict[str, dict] = field(default_factory = dict)