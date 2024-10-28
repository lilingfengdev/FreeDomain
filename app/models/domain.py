from app import db
from datetime import datetime, timezone, timedelta

class Domain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    points_required = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    tags = db.Column(db.String(255))
    dns_platform_id = db.Column(db.Integer, db.ForeignKey('dns_platform.id'), nullable=False)
    subdomains = db.relationship('Subdomain', backref='domain', lazy='dynamic')

class Subdomain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subdomain = db.Column(db.String(255), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8))))
    record_type = db.Column(db.String(10), nullable=False)  # 'A', 'AAAA', 'CNAME', 'SRV'
    record_value = db.Column(db.String(255), nullable=False)
    record_id = db.Column(db.String(255), nullable=False)

    user = db.relationship('User', backref=db.backref('subdomains', lazy='dynamic'))
