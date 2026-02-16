"""
🧠 MLflow Training Dashboard - Bentley Budget Bot

Real-time experiment tracking and model performance monitoring for:
- Financial prediction models
- Portfolio optimization algorithms
- Risk analysis models
- Trading strategy backtests

**Access:** Admin only
"""

import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MLflow config
from bbbot1_pipeline.mlflow_config import (
    get_mlflow_tracking_uri, 
    validate_connection,
    MLFLOW_MYSQL_CONFIG
)

# Page config
st.set_page_config(
    page_title="MLflow Training Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS matching Bentley Bot theme
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .experiment-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .run-success { color: #10b981; font-weight: bold; }
    .run-failed { color: #ef4444; font-weight: bold; }
    .run-running { color: #3b82f6; font-weight: bold; }
    .section-header {
        background: #1f2937;
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0 10px 0;
    }
    .stMetric {
        background: #f3f4f6;
        padding: 10px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


def check_mlflow_available():
    """Check if MLflow is available and properly configured."""
    try:
        import mlflow
        return True
    except ImportError:
        st.error("❌ MLflow is not installed. Install with: `pip install mlflow`")
        return False


def get_run_status_badge(status):
    """Return colored status badge for run status."""
    status = status.upper()
    if status == "FINISHED":
        return f'<span class="run-success">✓ FINISHED</span>'
    elif status == "FAILED":
        return f'<span class="run-failed">✗ FAILED</span>'
    elif status == "RUNNING":
        return f'<span class="run-running">● RUNNING</span>'
    else:
        return f'<span>{status}</span>'


def display_connection_info():
    """Display MLflow connection information."""
    with st.sidebar:
        st.markdown("### 🔌 MLflow Configuration")
        st.info(f"""
**Tracking URI:** `{get_mlflow_tracking_uri()}`

**Database:** {MLFLOW_MYSQL_CONFIG['name']}  
**Host:** {MLFLOW_MYSQL_CONFIG['host']}:{MLFLOW_MYSQL_CONFIG['port']}  
**Database:** {MLFLOW_MYSQL_CONFIG['database']}
        """)
        
        # Connection test
        if st.button("🔍 Test Connection"):
            with st.spinner("Testing MLflow connection..."):
                if validate_connection():
                    st.success("✅ Connection successful!")
                else:
                    st.error("❌ Connection failed")


def display_experiments():
    """Display all MLflow experiments."""
    import mlflow
    from mlflow.tracking import MlflowClient
    
    st.markdown('<div class="section-header"><h2>📊 Active Experiments</h2></div>', unsafe_allow_html=True)
    
    try:
        mlflow.set_tracking_uri(get_mlflow_tracking_uri())
        client = MlflowClient()
        experiments = client.search_experiments()
        
        if not experiments:
            st.info("No experiments found. Create your first experiment!")
            return None
        
        # Create experiment dataframe
        exp_data = []
        for exp in experiments:
            exp_data.append({
                "Experiment Name": exp.name,
                "Experiment ID": exp.experiment_id,
                "Lifecycle Stage": exp.lifecycle_stage,
                "Artifact Location": exp.artifact_location
            })
        
        exp_df = pd.DataFrame(exp_data)
        st.dataframe(exp_df, use_container_width=True)
        
        # Allow user to select experiment
        exp_names = [exp.name for exp in experiments]
        selected_exp_name = st.selectbox("Select Experiment to View Details", exp_names)
        
        # Get selected experiment ID
        selected_exp = next((exp for exp in experiments if exp.name == selected_exp_name), None)
        return selected_exp
        
    except Exception as e:
        st.error(f"❌ Failed to load experiments: {str(e)}")
        st.info("Make sure MLflow server is running and database is accessible.")
        return None


def display_experiment_runs(experiment):
    """Display runs for selected experiment."""
    import mlflow
    
    if not experiment:
        return
    
    st.markdown(f'<div class="section-header"><h2>🏃 Runs for: {experiment.name}</h2></div>', unsafe_allow_html=True)
    
    try:
        mlflow.set_tracking_uri(get_mlflow_tracking_uri())
        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id], max_results=50)
        
        if runs.empty:
            st.info(f"No runs found for experiment '{experiment.name}'")
            return
        
        # Display run metrics summary
        col1, col2, col3, col4 = st.columns(4)
        
        total_runs = len(runs)
        finished_runs = len(runs[runs['status'] == 'FINISHED'])
        failed_runs = len(runs[runs['status'] == 'FAILED'])
        
        with col1:
            st.metric("Total Runs", total_runs)
        with col2:
            st.metric("Finished", finished_runs, delta=None)
        with col3:
            st.metric("Failed", failed_runs, delta=None)
        with col4:
            success_rate = (finished_runs / total_runs * 100) if total_runs > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        st.markdown("---")
        
        # Display runs table with key metrics
        display_cols = ['run_id', 'status', 'start_time']
        
        # Add metric columns if they exist
        metric_cols = [col for col in runs.columns if col.startswith('metrics.')]
        param_cols = [col for col in runs.columns if col.startswith('params.')]
        
        # Select top metrics to display (limit to 5)
        display_cols.extend(metric_cols[:5])
        
        # Filter columns that exist
        available_cols = [col for col in display_cols if col in runs.columns]
        
        runs_display = runs[available_cols].copy()
        runs_display['start_time'] = pd.to_datetime(runs_display['start_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.dataframe(runs_display, use_container_width=True)
        
        # Run detail viewer
        st.markdown("---")
        run_ids = runs['run_id'].tolist()
        selected_run_id = st.selectbox("Select Run for Detailed View", run_ids)
        
        if selected_run_id:
            display_run_details(selected_run_id)
            
    except Exception as e:
        st.error(f"❌ Failed to load runs: {str(e)}")


def display_run_details(run_id):
    """Display detailed information for a specific run."""
    import mlflow
    
    st.markdown(f'<div class="section-header"><h3>📋 Run Details: {run_id[:8]}...</h3></div>', unsafe_allow_html=True)
    
    try:
        mlflow.set_tracking_uri(get_mlflow_tracking_uri())
        run = mlflow.get_run(run_id)
        
        # Run info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Run Information")
            st.markdown(f"**Status:** {get_run_status_badge(run.info.status)}", unsafe_allow_html=True)
            st.markdown(f"**Run ID:** `{run.info.run_id}`")
            st.markdown(f"**Experiment ID:** `{run.info.experiment_id}`")
            st.markdown(f"**Start Time:** {datetime.fromtimestamp(run.info.start_time/1000).strftime('%Y-%m-%d %H:%M:%S')}")
            if run.info.end_time:
                st.markdown(f"**End Time:** {datetime.fromtimestamp(run.info.end_time/1000).strftime('%Y-%m-%d %H:%M:%S')}")
                duration = (run.info.end_time - run.info.start_time) / 1000
                st.markdown(f"**Duration:** {duration:.2f} seconds")
        
        with col2:
            st.markdown("#### Metrics")
            if run.data.metrics:
                metrics_df = pd.DataFrame([run.data.metrics]).T
                metrics_df.columns = ['Value']
                st.dataframe(metrics_df, use_container_width=True)
            else:
                st.info("No metrics logged for this run")
        
        # Parameters
        st.markdown("---")
        st.markdown("#### Parameters")
        if run.data.params:
            params_df = pd.DataFrame([run.data.params]).T
            params_df.columns = ['Value']
            col1, col2 = st.columns(2)
            
            # Split params into two columns
            params_list = list(run.data.params.items())
            mid = len(params_list) // 2
            
            with col1:
                st.dataframe(pd.DataFrame(params_list[:mid], columns=['Parameter', 'Value']), use_container_width=True)
            with col2:
                if len(params_list) > mid:
                    st.dataframe(pd.DataFrame(params_list[mid:], columns=['Parameter', 'Value']), use_container_width=True)
        else:
            st.info("No parameters logged for this run")
        
        # Tags
        if run.data.tags:
            st.markdown("---")
            st.markdown("#### Tags")
            tags_df = pd.DataFrame([run.data.tags]).T
            tags_df.columns = ['Value']
            st.dataframe(tags_df, use_container_width=True)
            
    except Exception as e:
        st.error(f"❌ Failed to load run details: {str(e)}")


def display_metric_comparison():
    """Display metric comparison across runs."""
    st.markdown('<div class="section-header"><h2>📈 Metric Comparison</h2></div>', unsafe_allow_html=True)
    st.info("🚧 Metric comparison visualization coming soon!")
    st.markdown("""
    **Planned Features:**
    - Compare metrics across multiple runs
    - Visualize metric trends over time
    - Identify best performing models
    - Export comparison reports
    """)


def main():
    """Main application."""
    st.title("🧠 MLflow Training Dashboard")
    st.markdown(f"**Real-time Experiment Tracking** | Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check authentication (inherit from Admin Control Center)
    if "admin_authenticated" not in st.session_state:
        st.warning("🔒 Please login through the [Admin Control Center](./99_🔧_Admin_Control_Center)")
        st.stop()
        return
    
    # Check MLflow availability
    if not check_mlflow_available():
        st.stop()
        return
    
    # Display connection info in sidebar
    display_connection_info()
    
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Experiments",
        "🏃 Run Details", 
        "📈 Comparisons",
        "⚙️ Settings"
    ])
    
    with tab1:
        selected_experiment = display_experiments()
        if selected_experiment:
            st.markdown("---")
            display_experiment_runs(selected_experiment)
    
    with tab2:
        st.info("Select an experiment and run from the 'Experiments' tab to view detailed run information.")
    
    with tab3:
        display_metric_comparison()
    
    with tab4:
        st.markdown('<div class="section-header"><h2>⚙️ MLflow Settings</h2></div>', unsafe_allow_html=True)
        
        st.markdown("### Configuration")
        st.code(f"""
# Current MLflow Configuration
TRACKING_URI = "{get_mlflow_tracking_uri()}"
DATABASE = "{MLFLOW_MYSQL_CONFIG['database']}"
HOST = "{MLFLOW_MYSQL_CONFIG['host']}:{MLFLOW_MYSQL_CONFIG['port']}"
ENVIRONMENT = "{MLFLOW_MYSQL_CONFIG['name']}"
        """, language="python")
        
        st.markdown("### Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Connection"):
                st.rerun()
        
        with col2:
            if st.button("📊 View MLflow UI"):
                st.markdown(f"[Open MLflow UI](http://localhost:5000)")
        
        with col3:
            if st.button("📖 Documentation"):
                st.markdown("[MLflow Documentation](https://mlflow.org/docs/latest/index.html)")


if __name__ == "__main__":
    main()
