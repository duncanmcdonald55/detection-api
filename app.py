from flask import request, jsonify, Flask
from datetime import datetime

app = Flask(__name__)

detections = []

def verify_date(date):
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        return parsed_date
    except ValueError:
        return None

def find_detection_by_id(det_id):
    for detection in detections:
        if detection["id"] == det_id:
            return detection
    return None

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "very healthy"}), 200

@app.route("/detections", methods=["GET","POST"])
def detection_analysis():

    if request.method == 'GET':
        return jsonify(detections), 200
    
    if not request.is_json:
        return jsonify({"error": "must be in json format"}), 415
    
    data = request.get_json()

    required = ["date","confidence","status"]

    missing = [field for field in required if field not in data]

    if missing:
        return jsonify({"error": f"missing required fields {missing}"}), 400
    
    try:
        conf = float(data["confidence"])

        if not (0.0 <= conf <= 1.0):
            return jsonify({"error": "must be between 0 and 1"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "confidence must be a float"}), 400
    
    valid_status = ["candidate","confirmed","rejected"]

    if data["status"] not in valid_status:
        status = data["status"]
        return jsonify({"error": f"{status} is not a valid status"}), 400
    
    date = verify_date(data["date"])
    if not date:
        return jsonify({"error": "not a valid date, must be in format of YYYY-mm-dd"}), 400
    
    det_id = max((d["id"] for d in detections), default=0) + 1
    
    new_detection = {"id": det_id, "date": date, "confidence": conf, "status": data["status"], "notes": data.get("notes", "")}

    detections.append(new_detection)
    return jsonify(new_detection), 201

@app.route("/detections/<int:det_id>", methods=["GET"])
def get_detection(det_id):
    detection = find_detection_by_id(det_id)

    if not detection:
        return jsonify({"error":f"detection with id of {det_id} not found"}), 404
    return jsonify(detection), 200

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)