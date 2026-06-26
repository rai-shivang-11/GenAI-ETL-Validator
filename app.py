import streamlit as st
import pandas as pd
import os, tempfile
from core.drift_checker import driftChecker
from core.anomaly_detector import detectAnomaly
from core.health_report import generateHealthReport

# Note stremlit runs this whole code again if anything is changed on the page (click, button, etc)
 
st.set_page_config(page_title = 'ETL Validator', page_icon = '🔍', layout = 'wide')     #Always the first line in a streamlit application

st.title('Gen-AI ETL Validator')
st.caption('Detect schema drift, flag anomalies, and get AI-generated pipeline health reports')

col1, col2 = st.columns(2)                                  #Initializes two columns

with col1:                                                  #Everything in this with block belongs to col1
    st.subheader('Baseline dataset')
    baseline_file = st.file_uploader('Upload baseline csv', type= 'csv', key= 'baseline')
with col2:
    st.subheader('Current dataset')
    current_file = st.file_uploader('Upload current csv', type= 'csv', key= 'current')

use_sample = st.checkbox('Use sample data (data/baseline.csv and data/current.csv)', value= True)

if st.button('Run Validation', type= 'primary'):
    with st.spinner('Running validation...'):       # Spinner keeps displaying this until code is out of the block it is in
        # Check which data to use
        if use_sample:
            baseline_path = 'data/baseline.csv'
            current_path = 'data/current.csv'
        elif baseline_file and current_file:
            with tempfile.NamedTemporaryFile(delete= False, suffix= '.csv') as f:   # delete = False tells pythion not to delte the temp file immediately after creation, and to keep it unless removed
                f.write(baseline_file.read)
                baseline_path = f.name
            with tempfile.NamedTemporaryFile(delete= False, suffix= '.csv') as f:
                f.write(current_file.read)
                current_path = f.name
        else:
            st.error('Error - Either or both files missing, use sample data if files are unavailable')
            st.stop()
        
        drift = driftChecker(baseline_path, current_path)
        anomaly = detectAnomaly(current_path)
        report = generateHealthReport(drift.llmText(), anomaly.llmText())
    
    st.divider()

    col_a, col_b = st.columns(2)
    col_a.metric("Schema Drift", "⚠️ Detected" if drift.has_drift else "✅ Clean")
    col_b.metric("Anomalies", "⚠️ Detected" if anomaly.has_anomaly else "✅ Clean")

    tab1, tab2, tab3 = st.tabs(["📋 Schema Drift", "📊 Anomalies", "📝 Health Report"])

    with tab1:
        st.subheader('Schema Drift')
        if drift.has_drift:
            if drift.added_colums:
                st.success(f'**New columns added: {', '.join(drift.added_colums)}**')
            if drift.removed_columns:
                st.error(f'**Columns removed:** {', '.join(drift.removed_columns)}')
            if drift.type_changes:
                c = 1
                head = '**Type changes:**\n'
                for col, change in drift.type_changes.items():
                    st.warning(f"{head if c else ''} - '{col}' column's data type changed from '{change['from']}' to '{change['to']}'")
                    c = 0
        else:
            st.success('No schema drift detected')

    with tab2:
        st.subheader('Anomalies')
        if anomaly.has_anomaly:
            if anomaly.outliers:
                c = 1
                head = '**Outliers detected:**\n'
                for col, info in anomaly.outliers.items():
                    st.error(f'{head if c else ''}'
                    f' - "{col}" column had {info['outlier_count']} outliers\n'
                    f'      - Outliers = {info['outliers']}\n'
                    f'      - Maximum value = {info['max_value']:.2f}\n'
                    f'      - Minimum value = {info['min_value']:.2f}\n'
                    f'      - Upper limit = {info['upper_fence']:.2f}\n'
                    f'      - lower limit = {info['lower_fence']:.2f}'
                    )
                    c = 0
            if anomaly.nulls:
                c = 1
                head = '**Null spike detected (>5 % Nulls):**\n'
                for col, info in anomaly.nulls.items():
                    st.warning(f'{head if c else ''}'
                    f' - "{col}" column had {info['null_count']} nulls\n'
                    f'      - Null percentage: {info['null_prcnt']}'
                    )
        else:
            st.success('No anomalies detected')
    
    with tab3:
        st.subheader('LLM Report')
        st.markdown(report)
        st.download_button(
            'Download Report',
            data=report,                                            #Actual data to be downloaded
            file_name="pipeline_health_report.md",                  #Suggests this name to the browser when downloading
            mime="text/markdown"                                    #Tells browser which type file it is downloading
        )
    
    # Removing temp files
    if not use_sample and baseline_file and current_file:
        os.unlink(baseline_path)
        os.unlink(current_path)

