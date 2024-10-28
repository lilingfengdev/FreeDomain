from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.domain import Domain, Subdomain
from app.models.dns_platform import DNSPlatform
from app.models.card import Card
from app import db
import random
from datetime import date
from werkzeug.security import check_password_hash
from app.models.system_settings import SystemSettings
from app.api.cloudflare import CloudflareAPI
from app.api.dnspod import DNSPodAPI

bp = Blueprint('frontend', __name__)

@bp.route('/')
def index():
    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('index.html', settings=settings)

@bp.route('/user_center')
@login_required
def user_center():
    settings = SystemSettings.query.first()  # 获取系统设置
    domains = Domain.query.all()
    subdomains = Subdomain.query.filter_by(user_id=current_user.id).all()
    return render_template('user_center.html', domains=domains, subdomains=subdomains, settings=settings)

@bp.route('/create_subdomain', methods=['POST'])
@login_required
def create_subdomain():
    settings = SystemSettings.query.first()
    domain_id = request.form['domain_id']
    subdomain_name = request.form['subdomain']
    record_type = request.form['record_type']
    record_value = request.form['record_value']
    domain = Domain.query.get(domain_id)
    
    if current_user.points < domain.points_required:
        flash('用户积分不足', 'error')
        return redirect(url_for('frontend.user_center'))
    
    items = settings.forbidden_prefixes.split(',')
    if str(subdomain_name) in items or "*" in str(subdomain_name):
        flash('二级域名前缀不允许', 'error')
        return redirect(url_for('frontend.user_center'))
    
    if not domain:
        flash('无效的域名', 'error')
        return redirect(url_for('frontend.user_center'))

    # 获取 DNS 平台配置
    dns_platform = DNSPlatform.query.get(domain.dns_platform_id)
    if not dns_platform:
        flash('无效的 DNS 平台', 'error')
        return redirect(url_for('frontend.user_center'))

    # 调用相应的 DNS API 创建子域名
    if dns_platform.platform_type == 'cloudflare':
        api = CloudflareAPI(dns_platform.api_key, dns_platform.api_id)  # api_id 是电子邮件
        success = api.create_subdomain(subdomain_name, domain.name, record_type, record_value)
    elif dns_platform.platform_type == 'dnspod':
        api = DNSPodAPI(dns_platform.api_id, dns_platform.api_key)
        success = api.create_subdomain(domain.name, subdomain_name, record_type, record_value)
    
    if not success:
        flash('创建子域名失败，请检查输入信息', 'error')
        return redirect(url_for('frontend.user_center'))

    # 更新用户积分
    current_user.points -= domain.points_required
    new_subdomain = Subdomain(subdomain=subdomain_name, domain_id=domain_id, user_id=current_user.id,
                              record_type=record_type, record_value=record_value, record_id=success)
    db.session.add(new_subdomain)
    db.session.commit()
    
    flash('二级域名创建成功', 'success')
    return redirect(url_for('frontend.user_center'))

@bp.route('/daily_check_in')
@login_required
def daily_check_in():
    if current_user.can_checkin():
        points = random.randint(5, 10)
        current_user.points += points
        current_user.last_checkin = date.today()
        db.session.commit()
        flash(f'签到成功，获得{points}积分')
    else:
        flash('今天已经签到过了，明天再来吧！')
    return redirect(url_for('frontend.user_center'))

@bp.route('/redeem_card', methods=['POST'])
@login_required
def redeem_card():
    code = request.form['code']
    card = Card.query.filter_by(code=code).first()
    if card and card.can_used > card.is_used:
        current_user.points += card.points
        card.is_used += 1
        db.session.commit()
        flash(f'兑换成功，获得{card.points}积分')
    else:
        flash('无效或已使用的卡密')
    return redirect(url_for('frontend.user_center'))

@bp.route('/checkin')
@login_required
def checkin():
    if current_user.do_checkin():
        flash('签到成功！获得10积分。', 'success')
    else:
        flash('今天已经签到过了，明天再来吧！', 'warning')
    return redirect(url_for('frontend.user_center'))

@bp.route('/account_settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if not check_password_hash(current_user.password_hash, current_password):
            flash('当前密码不正确', 'error')
        elif new_password != confirm_password:
            flash('新密码和确认密码不匹配', 'error')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('密码已成功更新', 'success')
            return redirect(url_for('frontend.user_center'))

    return render_template('account_settings.html')

@bp.route('/available_domains')
def available_domains():
    settings = SystemSettings.query.first()  # 获取系统设置
    domains = Domain.query.all()
    return render_template('available_domains.html', domains=domains, settings=settings)

@bp.route('/edit_subdomain/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_subdomain(id):
    subdomain = Subdomain.query.get_or_404(id)
    if subdomain.user_id != current_user.id:
        flash('您没有权限编辑这个二级域名', 'error')
        return redirect(url_for('frontend.user_center'))
    
    if request.method == 'POST':
        subdomain.record_type = request.form['record_type']
        subdomain.record_value = request.form['record_value']
        
        # 获取 DNS 平台配置
        dns_platform = DNSPlatform.query.get(subdomain.domain.dns_platform_id)
        if not dns_platform:
            flash('无效的 DNS 平台', 'error')
            return redirect(url_for('frontend.user_center'))
        domain = Domain.query.get(subdomain.domain_id)
        # 调用相应的 DNS API 更新二级域名
        if dns_platform.platform_type == 'cloudflare':
            api = CloudflareAPI(dns_platform.api_key, dns_platform.api_id) 
            api.modify_record(domain.name, subdomain.record_id, subdomain.subdomain, subdomain.record_value, subdomain.record_type)
        elif dns_platform.platform_type == 'dnspod':
            api = DNSPodAPI(dns_platform.api_id, dns_platform.api_key)
            api.modify_record(domain.name, subdomain.record_id, subdomain.subdomain, subdomain.record_type, subdomain.record_value)

        db.session.commit()
        flash('二级域名更新成功', 'success')
        return redirect(url_for('frontend.user_center'))
    
    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('edit_subdomain.html', subdomain=subdomain, settings=settings)

@bp.route('/delete_subdomain/<int:id>', methods=['POST'])
@login_required
def delete_subdomain(id):
    subdomain = Subdomain.query.get_or_404(id)
    if subdomain.user_id != current_user.id:
        flash('您没有权限删除这个二级域名', 'error')
        return redirect(url_for('frontend.user_center'))
    
    # 获取 DNS 平台配置
    dns_platform = DNSPlatform.query.get(subdomain.domain.dns_platform_id)
    if not dns_platform:
        flash('无效的 DNS 平台', 'error')
        return redirect(url_for('frontend.user_center'))
    domain = Domain.query.get(subdomain.domain_id)
    # 调用相应的 DNS API 删除二级域名
    if dns_platform.platform_type == 'cloudflare':
        api = CloudflareAPI(dns_platform.api_key, dns_platform.api_id)  # api_id 是电子邮件
        success = api.delete_record(domain.name, subdomain.record_id)
    elif dns_platform.platform_type == 'dnspod':
        api = DNSPodAPI(dns_platform.api_id, dns_platform.api_key)
        success = api.delete_record(domain.name, subdomain.record_id)

    if not success:
        flash('删除二级域名失败，请检查输入信息', 'error')
        return redirect(url_for('frontend.user_center'))

    # 从数据库中删除子域名
    db.session.delete(subdomain)
    db.session.commit()
    flash('二级域名删除成功', 'success')
    return redirect(url_for('frontend.user_center'))
