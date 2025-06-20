from database import db, Database

# List of websites you're collecting traces for (must match what you use in collect.py)
websites = ["youtube", "wikipedia", "prothomalo"]

# Initialize and assign db instance
db = Database(websites)

# Create tables and initial stats
db.init_database()
