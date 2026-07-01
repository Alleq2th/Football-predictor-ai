# app.py
from flask import Flask, render_template, render_template_string, jsonify
from engine import Predictor
from datetime import datetime
import threading
import time
import traceback
import os

app = Flask(__name__)
predictor = Predictor()

cached_predictions = []
last_update = None
last_error = None

# Embedded HTML fallback – works even without templates/index.html
FALLBACK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Football AI Predictions</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; background: #1a1a2e; color: #eee; max-width: 800px; margin: auto; padding: 20px; }
        .card { background: #16213e; border-radius: 12px; padding: 20px; margin: 15px 0; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; }
        .green { background: #00c853; color: #000; } .yellow { background: #ffd600; color: #000; }
        .home { color: #00e676; } .away { color: #ff5252; }
        h1 { text-align: center; }
    </style>
</head>
<body>
    <h1>⚽ Football AI Predictions</h1>
    <p style="text-align:center">Updated: {{ updated or "Waiting for first run..." }}</p>
    {% if error %}<p style="color:red">Error: {{ error }}</p>{% endif %}
    {% if predictions %}
        {% for p in predictions %}
        <div class="card">
            <h2><span class="home">{{ p.home }}</span> vs <span class="away">{{ p.away }}</span></h2>
            <p>🏟 {{ p.league }} | 🕐 {{ p.kickoff[:16] }}</p>
            <p>
                <span class="badge green">Odd: {{ p.odd }}</span>
                <span class="badge yellow">Confidence: {{ p.confidence }}%</span>
                <span class="badge">{{ p.prediction }}</span>
            </p>
        </div>
        {% endfor %}
    {% else %}
        <p>No high-confidence predictions yet. Check back soon.</p>
    {% endif %}
</body>
</html>
"""

def update_predictions():
    global cached_predictions, last_update, last_error
    while True:
        try:
            cached_predictions = predictor.predict_all()
            last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            last_error = None
            print(f"✅ Predictions updated at {last_update}")
        except Exception as e:
            last_error = f"{datetime.now()}: {str(e)}"
            print(f"❌ Update failed: {traceback.format_exc()}")
        time.sleep(3600)

threading.Thread(target=update_predictions, daemon=True).start()

@app.route("/")
def index():
    # Try to use the template file, but fall back to embedded HTML if missing
    try:
        return render_template("index.html", predictions=cached_predictions, updated=last_update, error=last_error)
    except Exception:
        return render_template_string(FALLBACK_HTML, predictions=cached_predictions, updated=last_update, error=last_error)

@app.route("/api/predictions")
def api_predictions():
    return jsonify({"updated": last_update, "predictions": cached_predictions, "error": last_error})

@app.route("/refresh")
def refresh():
    global cached_predictions, last_update, last_error
    try:
        cached_predictions = predictor.predict_all()
        last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        last_error = None
        return jsonify({"status": "ok", "updated": last_update})
    except Exception as e:
        last_error = f"{datetime.now()}: {str(e)}"
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/debug")
def debug():
    try:
        fixtures = predictor.get_fixtures(datetime.now().strftime("%Y-%m-%d"))
        return jsonify({"fixture_count": len(fixtures), "sample": fixtures[:2], "last_error": last_error})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
