# app.py
from flask import Flask, render_template, jsonify
from engine import Predictor
from datetime import datetime
import threading
import time

app = Flask(__name__)
predictor = Predictor()

# Cache predictions
cached_predictions = []
last_update = None

def update_predictions():
    global cached_predictions, last_update
    while True:
        try:
            cached_predictions = predictor.predict_all()
            last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Predictions updated at {last_update}")
        except Exception as e:
            print(f"Update failed: {e}")
        time.sleep(3600)  # every hour

@app.route("/")
def index():
    return render_template("index.html", predictions=cached_predictions, updated=last_update)

@app.route("/api/predictions")
def api_predictions():
    return jsonify({
        "updated": last_update,
        "predictions": cached_predictions
    })

@app.route("/refresh")
def refresh():
    global cached_predictions, last_update
    try:
        cached_predictions = predictor.predict_all()
        last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({"status": "ok", "updated": last_update})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    # Start background updater
    t = threading.Thread(target=update_predictions, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=10000)
