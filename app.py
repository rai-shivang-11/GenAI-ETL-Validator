import streamlit as st
import pandas as pd
from core.schema_checker import compare_schemas
from core.detector import detect_anomalies
from core.health_report import generate_health_report
import tempfile, os

st.set_page_config(page_title="GenAI ETL Validator", page_icon="🔍", layout="wide")

st.title("🔍 GenAI ETL Validator")
st.caption("Detect schema drift, flag anomalies, and get AI-generated pipeline health reports")

# ── File upload ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.subheader("Baseline dataset")
    baseline_file = st.file_uploader("Upload baseline CSV", type="csv", key="baseline")
with col2:
    st.subheader("Current dataset")
    current_file = st.file_uploader("Upload current CSV", type="csv", key="current")

# Default to sample data if no upload
use_sample = st.checkbox("Use sample data (data/baseline.csv vs data/current.csv)", value=True)

if st.button("▶ Run Validation", type="primary"):
    with st.spinner("Running validation..."):

        # Resolve paths
        if use_sample:
            baseline_path = "data/baseline.csv"
            current_path = "data/current.csv"
        elif baseline_file and current_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
                f.write(baseline_file.read())
                baseline_path = f.name
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
                f.write(current_file.read())
                current_path = f.name
        else:
            st.error("Please upload both files or use sample data.")
            st.stop()

        # Run checks
        drift = compare_schemas(baseline_path, current_path)
        anomalies = detect_anomalies(current_path)
        report = generate_health_report(drift.to_text(), anomalies.to_text())

    # ── Results ──────────────────────────────────────────────────────────────
    st.divider()

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Schema Drift", "⚠️ Detected" if drift.has_drift else "✅ Clean")
    col_b.metric("Anomalies", "⚠️ Detected" if anomalies.has_anomalies else "✅ Clean")
    col_c.metric("Columns Added", len(drift.added_columns))

    tab1, tab2, tab3 = st.tabs(["📋 Schema Drift", "📊 Anomalies", "📝 Health Report"])

    with tab1:
        st.subheader("Schema drift findings")
        if drift.has_drift:
            if drift.added_columns:
                st.success(f"**New columns:** {', '.join(drift.added_columns)}")
            if drift.removed_columns:
                st.error(f"**Removed columns:** {', '.join(drift.removed_columns)}")
            if drift.type_changes:
                st.warning("**Type changes:**")
                for col, change in drift.type_changes.items():
                    st.write(f"  - `{col}`: `{change['from']}` → `{change['to']}`")
        else:
            st.success("No schema drift detected.")

    with tab2:
        st.subheader("Anomaly findings")
        if anomalies.has_anomalies:
            if anomalies.null_spikes:
                st.warning("**Null spikes detected:**")
                null_df = pd.DataFrame([
                    {"Column": col, "Null Count": info["null_count"], "Null %": f"{info['null_pct']:.1f}%"}
                    for col, info in anomalies.null_spikes.items()
                ])
                st.dataframe(null_df, use_container_width=True)
            if anomalies.outlier_columns:
                st.warning("**Outliers detected:**")
                outlier_df = pd.DataFrame([
                    {"Column": col, "Outlier Count": info["outlier_count"],
                     "Max Value": f"{info['max_value']:.2f}", "Expected Upper": f"{info['upper_fence']:.2f}"}
                    for col, info in anomalies.outlier_columns.items()
                ])
                st.dataframe(outlier_df, use_container_width=True)
        else:
            st.success("No anomalies detected.")

    with tab3:
        st.subheader("AI-generated health report")
        st.markdown(report)
        st.download_button(
            "⬇ Download report",
            data=report,
            file_name="pipeline_health_report.md",
            mime="text/markdown"
        )

    # Cleanup temp files
    if not use_sample and baseline_file and current_file:
        os.unlink(baseline_path)
        os.unlink(current_path)