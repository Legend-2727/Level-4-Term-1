from flask import Flask
from database import db, Fingerprint, init_db

app = Flask(__name__)
init_db(app)  # <-- this sets up db with app context

with app.app_context():
    for row in db.session.query(Fingerprint).all():
        print(row.website, len(row.trace_data), row.timestamp)
