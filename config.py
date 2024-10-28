import os

class Config:
    # 应用秘钥
    SECRET_KEY = 'your_secret_key'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 邮件配置
    MAIL_SERVER = 'smtp.office365.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'test@example.com'
    MAIL_PASSWORD = '123456'
    MAIL_DEFAULT_SENDER = "test@example.com"

    # 极验配置
    GEETEST_ID = 'id'
    GEETEST_KEY = 'key'
