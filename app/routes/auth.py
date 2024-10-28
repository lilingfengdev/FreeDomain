from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required
from app.models.user import User
from app import db, mail
from flask_mail import Message
import random
import string
from datetime import datetime, timedelta
import requests
import time
import hmac
from app.models.system_settings import SystemSettings

bp = Blueprint('auth', __name__)

def generate_confirmation_token():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.email_confirmed:
                flash('请先验证您的邮箱', 'error')
                return redirect(url_for('auth.confirm_email'))
            login_user(user)
            flash('登录成功！', 'success')
            return redirect(url_for('frontend.user_center'))
        else:
            flash('无效的用户名或密码', 'error')
            return redirect(url_for('auth.login'))

    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('login.html', settings=settings)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('frontend.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # 极验参数
        lot_number = data.get('lot_number')
        captcha_output = data.get('captcha_output')
        pass_token = data.get('pass_token')
        gen_time = data.get('gen_time')
        
        if not lot_number or not captcha_output or not pass_token or not gen_time:
            return jsonify({'success': False, 'message': '请完成人机验证'})

        # 二次校验
        captcha_id = current_app.config['GEETEST_ID']
        captcha_key = current_app.config['GEETEST_KEY']
        lotnumber_bytes = lot_number.encode()
        prikey_bytes = captcha_key.encode()
        sign_token = hmac.new(prikey_bytes, lotnumber_bytes, digestmod='SHA256').hexdigest()
        validate_data = {
            "lot_number": lot_number,
            "captcha_output": captcha_output,
            "pass_token": pass_token,
            "gen_time": gen_time,
            "sign_token": sign_token,
            "captcha_id": captcha_id
        }
        response = requests.post("http://gcaptcha4.geetest.com/validate", validate_data)
        result = response.json()
        if result.get('result') != 'success':
            return jsonify({'success': False, 'message': '人机验证失败，请重试'})

        # 检查用户是否已存在
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return jsonify({'success': False, 'message': '用户名或邮箱已被使用，请选择其他'})

        # 生成邮箱验证码
        token = generate_confirmation_token()
        token_expiration = datetime.utcnow() + timedelta(hours=24)

        new_user = User(username=username, email=email, 
                       email_confirm_token=token,
                       email_confirm_token_expiration=token_expiration)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        settings = SystemSettings.query.first()
        # 发送验证邮件
        msg = Message(f'{settings.system_name} - 邮箱验证',
                     sender=current_app.config['MAIL_DEFAULT_SENDER'],
                     recipients=[email])
        msg.body = f'您的验证码是: {token} \n请在24小时内登录完成验证'
        mail.send(msg)

        return jsonify({'success': True, 'message': '注册成功，请查收邮箱并完成验证'})

    settings = SystemSettings.query.first()
    return render_template('register.html', settings=settings)

@bp.route('/confirm_email', methods=['GET', 'POST'])
def confirm_email():
    if request.method == 'POST':
        email = request.form['email']
        token = request.form['token']

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('邮箱不存在', 'error')
            return redirect(url_for('auth.confirm_email'))

        if user.email_confirmed:
            flash('邮箱已经验证过了', 'info')
            return redirect(url_for('auth.login'))

        if (user.email_confirm_token == token and 
            user.email_confirm_token_expiration > datetime.utcnow()):
            user.email_confirmed = True
            user.email_confirm_token = None
            user.email_confirm_token_expiration = None
            db.session.commit()
            flash('邮箱验证成功，请登录', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('验证码无效或已过期', 'error')

    settings = SystemSettings.query.first()
    return render_template('confirm_email.html', settings=settings)

@bp.route('/send_email_verification', methods=['POST'])
def send_email_verification():
    email = request.form['email']
    token = generate_confirmation_token()  # 生成验证码
    msg = Message('邮箱验证码', sender='your_email@example.com', recipients=[email])
    msg.body = f'您的验证码是: {token}'
    mail.send(msg)
    flash('验证码已发送，请检查您的邮箱。', 'success')
    return redirect(url_for('auth.register'))

def validate_geetest(challenge, validate, seccode):
    url = "https://api.geetest.com/validate.php"
    data = {
        "gt": current_app.config['GEETEST_ID'],
        "challenge": challenge,
        "validate": validate,
        "seccode": seccode
    }
    response = requests.post(url, data=data)
    return response.text == seccode
