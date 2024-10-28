from app import db

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), unique=True, nullable=False)
    points = db.Column(db.Integer)  
    is_used = db.Column(db.Integer, default=0)
    can_used = db.Column(db.Integer)
