from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from datetime import date

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    points = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    email_confirmed = db.Column(db.Boolean, default=False)
    email_confirm_token = db.Column(db.String(32))
    email_confirm_token_expiration = db.Column(db.DateTime)
    last_checkin = db.Column(db.Date, nullable=True)
    is_banned = db.Column(db.Boolean, default=False)  # 新增字段：用户是否被封禁

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can_checkin(self):
        return self.last_checkin is None or self.last_checkin < date.today()

    @property
    def is_active(self):
        # 重写 is_active 属性，考虑用户是否被封禁
        return not self.is_banned

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
