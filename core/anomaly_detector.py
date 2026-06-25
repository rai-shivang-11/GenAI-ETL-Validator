import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class anomalyList:
    outliers: Dict[str, dict] = field(default_factory= dict)
    nulls: Dict[str, dict] = field(default_factory= dict)
    has_anomaly: bool = False

    def llmText(self):
        if not self.has_anomaly:
            return 'No anomalies detected'
        anomalies = ['Anomalies detected:']
        if self.outliers:
            anomalies.append(' Outliers detected:')
            for col, info in self.outliers.items():
                anomalies.append(
                    f'  "{col}" column had {info['outlier_count']} outliers\n'
                    f'  Outliers = {info['outliers']}\n'
                    f'  Maximum value = {info['max_value']:.2f}\n'
                    f'  Minimum value = {info['min_value']:.2f}\n'
                    f'  Upper limit = {info['upper_fence']:.2f}\n'
                    f'  lower limit = {info['lower_fence']:.2f}')
        if self.nulls:
            anomalies.append(f' Null spikes detected (null % > 5)')
            for col, info in self.nulls.items():
                anomalies.append(
                    f'  "{col}" column had {info['null_count']} nulls\n'
                    f'   Null percentage: {info['null_prcnt']}')

        return '\n'.join(anomalies)
    
def detectAnomaly(data_path: str, null_threshold: float = 0.05) -> anomalyList:
    df_dataset = pd.read_csv(data_path)
    n = len(df_dataset)
    anomaly = anomalyList()

    for col in df_dataset.columns:
        null_count = df_dataset[col].isna().sum()
        null_prcnt = float(null_count / n)

        if null_prcnt > null_threshold:
            anomaly.nulls[col] = {
                'null_count': null_count,
                'null_prcnt': null_prcnt
            }
    
    numeric_columns = df_dataset.select_dtypes(include= [np.number]).columns

    for ncol in numeric_columns:
        series = df_dataset[ncol].dropna()
        if len(series) < 10: continue   #dataset staistically small
        
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1                           #Interquartile range
        
        lower_fence = q1 - (iqr * 3)            #'Extreme' outliers lie outside 3x boundary of iqr
        upper_fence = q3 + (iqr * 3)            #'Mild' outliers lie outside 1.5x iqr
        
        outlier = series[(series < lower_fence) | (series > upper_fence)]
        
        if len(outlier) > 0:
            anomaly.outliers[ncol] = {
                'outlier_count': len(outlier),
                'outliers': outlier.to_list(),
                'max_value': float(max(outlier)),
                'min_value': float(min(outlier)),
                'upper_fence': float(upper_fence),
                'lower_fence': float(lower_fence)
            }
    
    anomaly.has_anomaly = bool (
        anomaly.nulls or anomaly.outliers
    )
    return anomaly

if __name__ == '__main__':
    anomalyTest = detectAnomaly('data/current.csv')
    print(anomalyTest.llmText())