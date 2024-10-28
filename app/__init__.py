from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from config import Config
from flask.cli import with_appcontext
import click
import sqlalchemy as sa
import os
import logging

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # 配置日志
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    from app.routes import auth, frontend, admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(frontend.bp)
    app.register_blueprint(admin.bp)

    # 添加静态文件路由
    @app.route('/static/js/<path:filename>')
    def serve_static(filename):
        return send_from_directory(os.path.join(app.root_path, 'static', 'js'), filename)

    @app.cli.command("create-admin")
    @with_appcontext
    def create_admin():
        from app.models.user import User  # 在这里导入 User 模型
        username = click.prompt('请输入管理员用户名', type=str)
        email = click.prompt('请输入管理员邮箱', type=str)
        password = click.prompt('请输入管理员密码', type=str, hide_input=True, confirmation_prompt=True)
        user = User(username=username, email=email, is_admin=True, email_confirmed=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo('管理员用户创建成功')

    @app.cli.command("init-db")
    @with_appcontext
    def init_db():
        engine = db.get_engine()
        inspector = sa.inspect(engine)
        table_names = inspector.get_table_names()
        
        from app.models import user, domain, card, dns_platform
        
        if not table_names:
            db.create_all()
            settings = SystemSettings.query.first() or SystemSettings()
            settings.system_name = "AZDNS"
            settings.forbidden_prefixes = "*,www,3w"
            db.session.add(settings)
            db.session.commit()
            click.echo("数据库表已创建")
        else:
            click.echo("数据库表已存在")

    return app

from app.models.system_settings import SystemSettings
