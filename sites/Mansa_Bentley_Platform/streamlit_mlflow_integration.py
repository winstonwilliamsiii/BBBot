"""
Bentley Budget Bot - Streamlit MLflow Integration
Integration module for logging Streamlit app metrics to MLflow
"""

import streamlit as st
from typing import Dict, Any, Optional
import time
from datetime import datetime
import os

try:
    from mlflow_config import (
        log_portfolio_metrics, 
        log_data_ingestion, 
        mlflow_client
    )
    MLFLOW_INTEGRATION_AVAILABLE = True
except ImportError:
    MLFLOW_INTEGRATION_AVAILABLE = False
    print("⚠️ MLflow config not available - metrics will be logged to console only")


class StreamlitMLflowTracker:
    """Streamlit-specific MLflow tracking integration"""
    
    def __init__(self):
        self.session_start = time.time()
        self.available = MLFLOW_INTEGRATION_AVAILABLE
        
        # Initialize session state for tracking
        if 'mlflow_session_id' not in st.session_state:
            st.session_state.mlflow_session_id = f"streamlit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if 'mlflow_metrics' not in st.session_state:
            st.session_state.mlflow_metrics = {}
    
    def track_page_load(self, page_name: str, load_time: float = None):
        """Track page load performance"""
        if load_time is None:
            load_time = time.time() - self.session_start
        
        metrics = {
            "page_name": page_name,
            "load_time_seconds": load_time,
            "session_id": st.session_state.mlflow_session_id,
            "timestamp": datetime.now().isoformat(),
            "user_agent": "streamlit_app"
        }
        
        if self.available:
            log_data_ingestion(
                metrics, 
                f"page_load_{page_name}_{datetime.now().strftime('%H%M')}"
            )
        else:
            print(f"📊 Page Load: {page_name} - {load_time:.2f}s")
    
    def track_portfolio_update(self, portfolio_data: Dict[str, Any]):
        """Track portfolio data updates"""
        if not portfolio_data:
            return
        
        # Enhance with session info
        enhanced_data = {
            **portfolio_data,
            "session_id": st.session_state.mlflow_session_id,
            "update_timestamp": datetime.now().isoformat(),
            "data_source": portfolio_data.get("source", "unknown")
        }
        
        # Store in session state
        st.session_state.mlflow_metrics['last_portfolio_update'] = enhanced_data
        
        if self.available:
            log_portfolio_metrics(
                enhanced_data,
                f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M')}"
            )
        else:
            print(f"📈 Portfolio Update: {len(portfolio_data)} metrics")
    
    def track_yfinance_call(self, symbols: list, success: bool, response_time: float, rows_returned: int = 0):
        """Track Yahoo Finance API calls"""
        metrics = {
            "source": "yfinance",
            "symbols_requested": len(symbols) if symbols else 0,
            "symbols_list": str(symbols) if len(symbols) <= 10 else f"{len(symbols)} symbols",
            "success": success,
            "response_time_seconds": response_time,
            "rows_returned": rows_returned,
            "session_id": st.session_state.mlflow_session_id,
            "api_call_timestamp": datetime.now().isoformat()
        }
        
        if self.available:
            run_name = f"yfinance_{datetime.now().strftime('%H%M%S')}"
            log_data_ingestion(metrics, run_name)
        else:
            status = "✅" if success else "❌"
            print(f"{status} YFinance: {len(symbols)} symbols, {response_time:.2f}s")
    
    def track_csv_upload(self, filename: str, rows: int, columns: int, file_size: int):
        """Track CSV file uploads"""
        metrics = {
            "source": "csv_upload",
            "filename": filename,
            "rows_processed": rows,
            "columns_count": columns,
            "file_size_bytes": file_size,
            "processing_time": 1.0,  # Would be measured in real implementation
            "session_id": st.session_state.mlflow_session_id,
            "upload_timestamp": datetime.now().isoformat(),
            "status": "success"
        }
        
        if self.available:
            log_data_ingestion(
                metrics,
                f"csv_upload_{datetime.now().strftime('%Y%m%d_%H%M')}"
            )
        else:
            print(f"📄 CSV Upload: {filename} - {rows} rows, {columns} cols")
    
    def track_error(self, error_type: str, error_message: str, component: str = "unknown"):
        """Track application errors"""
        error_metrics = {
            "source": f"streamlit_error_{component}",
            "error_type": error_type,
            "error_message": str(error_message)[:500],  # Limit message length
            "component": component,
            "session_id": st.session_state.mlflow_session_id,
            "error_timestamp": datetime.now().isoformat(),
            "status": "error"
        }
        
        if self.available:
            log_data_ingestion(
                error_metrics,
                f"error_{component}_{datetime.now().strftime('%H%M%S')}"
            )
        else:
            print(f"❌ Error in {component}: {error_type}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session metrics"""
        session_duration = time.time() - self.session_start
        
        summary = {
            "session_id": st.session_state.mlflow_session_id,
            "session_duration_seconds": session_duration,
            "mlflow_available": self.available,
            "metrics_tracked": len(st.session_state.mlflow_metrics),
            "summary_timestamp": datetime.now().isoformat()
        }
        
        return summary
    
    def display_tracking_status(self):
        """Display MLflow tracking status in Streamlit sidebar"""
        with st.sidebar:
            st.markdown("### 📊 MLflow Tracking")
            
            if self.available:
                st.success("✅ MLflow Connected")
                try:
                    # Try to get tracking URI
                    tracking_uri = mlflow_client.tracking_uri
                    st.caption(f"Server: `{tracking_uri}`")
                except:
                    st.caption("Server: Connected")
            else:
                st.warning("⚠️ MLflow Offline")
                st.caption("Metrics logged to console")
            
            # Session info
            st.caption(f"Session: `{st.session_state.mlflow_session_id}`")
            
            session_duration = time.time() - self.session_start
            st.caption(f"Duration: {session_duration:.1f}s")
            
            # Metrics count
            metrics_count = len(st.session_state.mlflow_metrics)
            st.caption(f"Metrics: {metrics_count} logged")


# Global tracker instance
tracker = StreamlitMLflowTracker()

# Convenience functions for easy integration
def track_page_load(page_name: str, load_time: float = None):
    """Track page load time"""
    return tracker.track_page_load(page_name, load_time)

def track_portfolio_update(portfolio_data: Dict[str, Any]):
    """Track portfolio updates"""
    return tracker.track_portfolio_update(portfolio_data)

def track_yfinance_call(symbols: list, success: bool, response_time: float, rows_returned: int = 0):
    """Track Yahoo Finance API calls"""
    return tracker.track_yfinance_call(symbols, success, response_time, rows_returned)

def track_csv_upload(filename: str, rows: int, columns: int, file_size: int):
    """Track CSV uploads"""
    return tracker.track_csv_upload(filename, rows, columns, file_size)

def track_error(error_type: str, error_message: str, component: str = "unknown"):
    """Track errors"""
    return tracker.track_error(error_type, error_message, component)

def display_tracking_status():
    """Display tracking status in sidebar"""
    return tracker.display_tracking_status()

def get_session_summary():
    """Get session summary"""
    return tracker.get_session_summary()

# Example integration for your main Streamlit app
def integrate_with_streamlit_app():
    """
    Example of how to integrate MLflow tracking with your main Streamlit app
    Add these calls to your streamlit_app.py at appropriate locations:
    """
    
    example_code = '''
    # At the top of your streamlit_app.py, after imports:
    from streamlit_mlflow_integration import (
        track_page_load, 
        track_portfolio_update, 
        track_yfinance_call,
        track_csv_upload,
        track_error,
        display_tracking_status
    )
    
    # At the start of your main() function:
    track_page_load("dashboard")
    
    # In your sidebar:
    display_tracking_status()
    
    # When fetching Yahoo Finance data:
    try:
        start_time = time.time()
        data = yf.download(tickers, ...)
        response_time = time.time() - start_time
        track_yfinance_call(tickers, True, response_time, len(data))
    except Exception as e:
        track_yfinance_call(tickers, False, time.time() - start_time, 0)
        track_error("YFinanceError", str(e), "data_fetch")
    
    # When processing CSV uploads:
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        file_size = uploaded_file.size
        track_csv_upload(uploaded_file.name, len(df), len(df.columns), file_size)
    
    # When calculating portfolio metrics:
    portfolio_metrics = {
        "total_value": portfolio_value,
        "daily_return": daily_return,
        "num_positions": len(positions),
        "source": "yahoo_finance"  # or "csv_upload"
    }
    track_portfolio_update(portfolio_metrics)
    '''
    
    return example_code

if __name__ == "__main__":
    # Test the integration
    print("🧪 Testing Streamlit MLflow integration...")
    
    # Test tracking functions
    track_page_load("test_page", 2.5)
    
    test_portfolio = {
        "total_value": 125000,
        "daily_return": 1.5,
        "positions": 12
    }
    track_portfolio_update(test_portfolio)
    
    track_yfinance_call(["AAPL", "GOOGL"], True, 1.2, 500)
    track_csv_upload("test.csv", 100, 5, 2048)
    
    print("✅ Integration test completed")
    print("\nIntegration example:")
    print(integrate_with_streamlit_app())