from app import db

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    system_name = db.Column(db.String(255), nullable=False, default="AZDNS")
    forbidden_prefixes = db.Column(db.String(255), nullable=True, default="www,*,@")

    def __repr__(self):
        return f'<SystemSettings {self.system_name}>'
