from flask import Flask, jsonify, render_template
from router.routes import bp, limiter
import os

app = Flask(__name__)

limiter.init_app(app)
app.register_blueprint(bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api')
def api_info():
    return jsonify({
        "message": "Newsletter Application API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/internal/v1/health",
            "login": "/internal/v1/login",
            "subscribe": "/internal/v1/subscribe",
            "scheduler_status": "/internal/v1/scheduler-status",
            "generate_newsletter": "/internal/v1/generate-newsletter"
        },
        "documentation": "See SETUP.md for API usage"
    })

@app.route('/health')
def simple_health():
    return jsonify({"status": "ok", "message": "Application is running"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting server on http://localhost:{port}")
    print("Available endpoints:")
    print(f"  - Root: http://localhost:{port}/")
    print(f"  - Health: http://localhost:{port}/health")
    print(f"  - API Health: http://localhost:{port}/internal/v1/health")
    app.run(host="0.0.0.0", port=port, debug=True)
