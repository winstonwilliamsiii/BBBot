"""
Bentley Bot Control Center - Flask API Server
Main application that serves admin endpoints for bot management
"""
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for Streamlit (localhost:8501)
CORS(app, resources={
    r"/admin/*": {
        "origins": ["http://localhost:8501", "http://127.0.0.1:8501"]
    }
})

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
            "admin_monitoring": "/admin/monitoring"
        },
        "note": "Admin endpoints will be available after Week 1-2 implementation"
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

if __name__ == '__main__':
    print("🚀 Starting Bentley Bot Control Center API...")
    print("📡 API will be available at: http://localhost:5000")
    print("📊 Health check: http://localhost:5000/health")
    print("🔧 Admin test: http://localhost:5000/admin/test")
    print("\n⚠️  Note: Admin endpoints will be added in Week 1-2")
    print("📖 See: docs/CONTROL_CENTER_QUICK_START.md\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Disabled to prevent .venv file change detection loop
    )
