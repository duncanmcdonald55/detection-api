from flask import request, jsonify, Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL","postgresql://postgres:postgres@db:5432/fertility_db")
app.config["SQL_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Detections(db.Model):
    __tablename__ = "detections"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(30), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, default="")

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "confidence": self.confidence,
            "status": self.status,
            "notes": self.notes
        }

with app.app_context():
    db.create_all()

def verify_date(date):
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        return parsed_date
    except ValueError:
        return None

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "very healthy"}), 200

@app.route("/detections", methods=["GET","POST"])
def detection_analysis():

    if request.method == 'GET':
        dets = Detections.query.all()
        return jsonify([d.to_dict() for d in dets]), 200
    
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
    
    notes = data.get("notes","")
    
    
    new_detection = Detections(date=date, confidence=conf, status = data["status"], notes=notes)
    db.session.add(new_detection)
    db.session.commit()
    return jsonify(new_detection.to_dict()), 201

@app.route("/detections/<int:det_id>", methods=["GET"])
def get_detection(det_id):
    detection = db.get_or_404(Detections, det_id)
    return jsonify(detection.to_dict()), 200
    

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)