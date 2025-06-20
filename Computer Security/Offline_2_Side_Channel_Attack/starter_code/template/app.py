from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

import database
from database import Database
# additional imports

app = Flask(__name__)

HEATMAP_DIR = "static/heatmaps"
os.makedirs(HEATMAP_DIR, exist_ok=True)


stored_traces = []
stored_heatmaps = []

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/collect_trace', methods=['POST'])
def collect_trace():
    data = request.get_json()
    trace = data.get("trace")
    if not trace or not isinstance(trace, list):
        return jsonify({"error": "Invalid trace data"}), 400

    try:
        # Generate unique filename
        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(HEATMAP_DIR, filename)

        # Plot and save heatmap
        plt.figure(figsize=(10, 2))
        plt.imshow([trace], cmap='hot', aspect='auto')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(filepath, bbox_inches='tight', pad_inches=0)
        plt.close()  # CRITICAL: Release memory and prevent threading issues

        stored_traces.append(trace)
        stored_heatmaps.append(filename)
        return jsonify({ "image_url": f"/heatmaps/{filename}" })
    except Exception as e:
        return jsonify({ "error": str(e) }), 500

@app.route('/heatmaps/<filename>')
def get_heatmap(filename):
    return send_from_directory(HEATMAP_DIR, filename)


@app.route('/api/clear_results', methods=['POST'])
def clear_results():
    try:
        # Clear stored lists
        stored_traces.clear()
        stored_heatmaps.clear()
        # Delete all heatmap images
        for filename in os.listdir(HEATMAP_DIR):
            filepath = os.path.join(HEATMAP_DIR, filename)
            if os.path.isfile(filepath):
                os.remove(filepath)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route("/download_traces")
def download_traces():
    return jsonify(stored_traces)

@app.route('/api/get_results')
def get_results():
    """Endpoint to retrieve collected traces for automation"""
    return jsonify({
        "traces": stored_traces,
        "count": len(stored_traces),
        "status": "success"
    })


# Additional endpoints can be implemented here as needed.

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)