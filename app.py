from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from pyngrok import ngrok
from threading import Thread
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',"sqlite:///site.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config['secret_key'] = 'niggaballs'

class IOT(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thing_id = db.Column(db.Integer, nullable=False)
    property_name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


@app.route("/")
def home():
    return render_template_string("""
    <h1>Welcome to Arduino Logs Dashboard</h1>
    <p>Click below to view the logs:</p>
    <a href="/logs">View Logs</a>
    """)

@app.route('/arduino-webhook', methods=['POST'])
def arduino_webhook():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON received"}), 400
    try:
        new_log = IOT(
            thing_id=int(data.get('thing_id', 0)),
            property_name=data.get('property_name', 'ultrasonic'),
            value=int(data.get('value', 0))
        )
        db.session.add(new_log)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/deletelogs/<int:thing_id>")
def deletelogs(thing_id):
    IOT.query.filter_by(thing_id=thing_id).delete()
    db.session.commit()

@app.route('/logs')
def logs():
    all_logs = IOT.query.order_by(IOT.id.desc()).all()
    return render_template_string("""
    <h1>Arduino Logs</h1>
    <table border="1" cellpadding="5">
        <tr>
            <th>ID</th>
            <th>Thing ID</th>
            <th>Property</th>
            <th>Distance (cm)</th>
            <th>Updated At</th>
        </tr>
        {% for log in logs %}
        <tr>
            <td>{{ log.id }}</td>
            <td>{{ log.thing_id }}</td>
            <td>{{ log.property_name }}</td>
            <td>{{ log.value }}</td>
            <td>{{ log.updated_at }}</td>
        </tr>
        {% endfor %}
    </table>
    <p><a href="/">Back to Home</a></p>
    """, logs=all_logs)


def start_ngrok():
    public_url = ngrok.connect(5000)
    print(f"\n\nPublic URL (give this to your friend): {public_url}/arduino-webhook\n\n")

if __name__ == "__main__":
    Thread(target=start_ngrok, daemon=True).start()
    app.run(port=5000)
