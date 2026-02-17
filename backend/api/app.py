"""
Bentley Bot Control Center - Flask API Server
Main application that serves admin endpoints for bot management
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)

# Enable CORS for Streamlit (localhost:8501)
CORS(app, resources={
    r"/admin/*": {
        "origins": ["http://localhost:8501", "http://127.0.0.1:8501"]
    }
})

# Import liquidity manager
from api.admin.liquidity_manager import LiquidityManager

# Initialize liquidity manager with defaults
liquidity_manager = LiquidityManager(
    liquidity_buffer_pct=25.0,
    profit_benchmark_pct=15.0,
    auto_rebalance=True
)

# Import blueprints (will be created in Week 1)
# from backend.api.admin.bots import bots_bp
# from backend.api.admin.brokers import brokers_bp
# from backend.api.admin.risk import risk_bp
# from backend.api.admin.monitoring import monitoring_bp

# Register blueprints
# app.register_blueprint(bots_bp)
# app.register_blueprint(brokers_bp)
# app.register_blueprint(risk_bp)
# app.register_blueprint(monitoring_bp)

@app.route('/')
def root():
    """API root endpoint"""
    return jsonify({
        "message": "Bentley Bot Control Center API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "admin_bots": "/admin/bots",
            "admin_brokers": "/admin/brokers",
            "admin_risk": "/admin/risk",
            "admin_monitoring": "/admin/monitoring",
            "admin_liquidity": "/admin/liquidity",
            "admin_liquidity_check": "/admin/liquidity/check-profit"
        },
        "note": "Liquidity management endpoints are now available!"
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Bentley Bot Control Center API",
        "version": "1.0.0"
    })

@app.route('/admin/test')
def test_admin():
    """Test endpoint to verify API is working"""
    return jsonify({
        "message": "Admin API is accessible!",
        "note": "Create blueprints in backend/api/admin/ to add functionality"
    })

@app.route('/admin/liquidity', methods=['GET', 'POST'])
def liquidity_metrics():
    """
    Get liquidity metrics and manage dry powder for automatic trades.
    
    GET: Returns current liquidity metrics based on default or query params
    POST: Updates liquidity settings (buffer_pct, profit_benchmark_pct, auto_rebalance)
    """
    if request.method == 'POST':
        # Update liquidity manager settings
        data = request.json
        
        if 'liquidity_buffer_pct' in data:
            liquidity_manager.liquidity_buffer_pct = float(data['liquidity_buffer_pct'])
        
        if 'profit_benchmark_pct' in data:
            liquidity_manager.profit_benchmark_pct = float(data['profit_benchmark_pct'])
        
        if 'auto_rebalance' in data:
            liquidity_manager.auto_rebalance = bool(data['auto_rebalance'])
        
        return jsonify({
            "status": "success",
            "message": "Liquidity settings updated",
            "settings": {
                "liquidity_buffer_pct": liquidity_manager.liquidity_buffer_pct,
                "profit_benchmark_pct": liquidity_manager.profit_benchmark_pct,
                "auto_rebalance": liquidity_manager.auto_rebalance
            }
        })
    
    # GET request - calculate and return metrics
    # These would normally come from your portfolio database
    # For now, use query params or defaults
    total_value = float(request.args.get('total_value', 100000))
    current_cash = float(request.args.get('current_cash', 26500))
    positions_value = float(request.args.get('positions_value', 73500))
    
    # Calculate metrics
    metrics = liquidity_manager.calculate_liquidity_metrics(
        total_value, current_cash, positions_value
    )
    
    # Get rebalancing recommendation
    recommendation = liquidity_manager.get_rebalance_recommendation(metrics)
    
    # Calculate max position size
    max_position = liquidity_manager.calculate_max_position_size(metrics)
    
    return jsonify({
        "status": "success",
        "metrics": metrics,
        "recommendation": recommendation,
        "max_position_size": max_position,
        "settings": {
            "liquidity_buffer_pct": liquidity_manager.liquidity_buffer_pct,
            "profit_benchmark_pct": liquidity_manager.profit_benchmark_pct,
            "auto_rebalance": liquidity_manager.auto_rebalance
        }
    })

@app.route('/admin/liquidity/check-profit', methods=['POST'])
def check_profit_benchmark():
    """
    Check if a position's profit has reached the benchmark for liquidity release.
    
    POST body: {"position_profit_pct": 18.5}
    """
    data = request.json
    position_profit_pct = float(data.get('position_profit_pct', 0))
    
    should_release, message = liquidity_manager.check_profit_benchmark(position_profit_pct)
    
    return jsonify({
        "status": "success",
        "should_release": should_release,
        "message": message,
        "current_profit": position_profit_pct,
        "benchmark": liquidity_manager.profit_benchmark_pct
    })

if __name__ == '__main__':
    print("🚀 Starting Bentley Bot Control Center API...")
    print("📡 API will be available at: http://localhost:5001")
    print("📊 Health check: http://localhost:5001/health")
    print("🔧 Admin test: http://localhost:5001/admin/test")
    print("\n⚠️  Note: Admin endpoints will be added in Week 1-2")
    print("📖 See: docs/CONTROL_CENTER_QUICK_START.md\n")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=False  # Disabled to prevent .venv file change detection loop
    )
