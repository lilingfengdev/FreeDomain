from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models.domain import Domain, Subdomain
from app.models.card import Card
from app.models.dns_platform import DNSPlatform
from app import db
from app.api.cloudflare import CloudflareAPI
from app.api.dnspod import DNSPodAPI
from app.models.user import User
from app.models.system_settings import SystemSettings

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('您没有权限访问此页面')
            return redirect(url_for('frontend.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def dashboard():
    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('admin/dashboard.html', settings=settings)

@bp.route('/manage_domains')
@login_required
@admin_required
def manage_domains():
    domains = Domain.query.all()
    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('admin/manage_domains.html', domains=domains, settings=settings)

@bp.route('/add_domain', methods=['GET', 'POST'])
@login_required
@admin_required
def add_domain():
    if request.method == 'POST':
        domain_name = request.form['domain_name']  # 从前端获取域名名称
        points_required = request.form['points_required']
        description = request.form['description']
        tags = request.form['tags']
        dns_platform_id = request.form['dns_platform']  # 从前端获取 DNS 平台 ID
        
        # 检查是否已经存在相同名称的域名
        existing_domain = Domain.query.filter_by(name=domain_name).first()
        if existing_domain:
            flash('该域名已存在，请选择其他域名。', 'error')
            return redirect(url_for('admin.add_domain'))

        # 查找对应的 DNS 平台配置
        dns_platform = DNSPlatform.query.get(dns_platform_id)
        if not dns_platform:
            flash('无效的 DNS 平台，请重试。', 'error')
            return redirect(url_for('admin.add_domain'))

        # 添加新域名
        new_domain = Domain(name=domain_name, points_required=points_required, description=description, tags=tags, dns_platform_id=dns_platform_id)
        db.session.add(new_domain)
        db.session.commit()
        flash('域名添加成功')
        return redirect(url_for('admin.manage_domains'))
    
    platforms = DNSPlatform.query.all()
    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('admin/add_domain.html', platforms=platforms, settings=settings)

@bp.route('/edit_domain/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_domain(id):
    domain = Domain.query.get_or_404(id)
    if request.method == 'POST':
        domain.name = request.form['domain_name']  # 从前端获取域名名称
        domain.points_required = request.form['points_required']
        domain.description = request.form['description']
        domain.tags = request.form['tags']
        
        db.session.commit()
        flash('域名更新成功')
        return redirect(url_for('admin.manage_domains'))

    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('admin/edit_domain.html', domain=domain, settings=settings)

@bp.route('/delete_domain/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_domain(id):
    domain = Domain.query.get_or_404(id)
    db.session.delete(domain)
    db.session.commit()
    flash('域名删除成功')
    return redirect(url_for('admin.manage_domains'))

@bp.route('/dns_platforms')
@login_required
@admin_required
def dns_platforms():
    platforms = DNSPlatform.query.all()
    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('admin/dns_platforms.html', platforms=platforms, settings=settings)

@bp.route('/add_dns_platform', methods=['GET', 'POST'])
@login_required
@admin_required
def add_dns_platform():
    if request.method == 'POST':
        name = request.form['name']
        platform_type = request.form['platform_type']
        note = request.form['note']

        if platform_type == 'cloudflare':
            api_key = request.form['cf_api_key']
            api_id = request.form['cf_email']  # 这里存放的是电子邮件
        elif platform_type == 'dnspod':
            api_key = request.form['dp_api_token']
            api_id = request.form['dp_api_id']
        else:
            flash('不支持的平台类型')
            return redirect(url_for('admin.add_dns_platform'))

        new_platform = DNSPlatform(name=name, platform_type=platform_type, api_key=api_key, api_id=api_id, note=note)
        db.session.add(new_platform)
        db.session.commit()
        flash('DNS平台添加成功')
        return redirect(url_for('admin.dns_platforms'))

    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('admin/add_dns_platform.html', settings=settings)

@bp.route('/edit_dns_platform/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_dns_platform(id):
    platform = DNSPlatform.query.get_or_404(id)
    if request.method == 'POST':
        platform.name = request.form['name']
        platform.platform_type = request.form['platform_type']
        platform.note = request.form['note']

        if platform.platform_type == 'cloudflare':
            platform.api_key = request.form['cf_api_key']
            platform.api_id = request.form['cf_email']  # 这里存放的是电子邮件
        elif platform.platform_type == 'dnspod':
            platform.api_key = request.form['dp_api_token']
            platform.api_id = request.form['dp_api_id']
        else:
            flash('不支持的平台类型')
            return redirect(url_for('admin.edit_dns_platform', id=id))

        db.session.commit()
        flash('DNS平台更新成功')
        return redirect(url_for('admin.dns_platforms'))

    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('admin/edit_dns_platform.html', platform=platform, settings=settings)

@bp.route('/delete_dns_platform/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_dns_platform(id):
    platform = DNSPlatform.query.get_or_404(id)
    db.session.delete(platform)
    db.session.commit()
    flash('DNS平台删除成功')
    return redirect(url_for('admin.dns_platforms'))

@bp.route('/get_platform_domains/<int:platform_id>')
@login_required
@admin_required
def get_platform_domains(platform_id):
    platform = DNSPlatform.query.get_or_404(platform_id)
    existing_domains = [domain.name for domain in Domain.query.filter_by(dns_platform_id=platform_id).all()]
    
    if platform.platform_type == 'cloudflare':
        api = CloudflareAPI(platform.api_key, platform.api_id)
        domains = api.get_domains()
    elif platform.platform_type == 'dnspod':
        api = DNSPodAPI(platform.api_id, platform.api_key)
        domains = api.get_domains()
    else:
        domains = []
    print(domains)
    domain_names = []
    for domain in domains:
        domain_names.append(domain['name'])
    available_domains = [domain for domain in domain_names if domain not in existing_domains]
    return jsonify(available_domains)

@bp.route('/manage_records')
@login_required
@admin_required
def manage_records():
    subdomains = Subdomain.query.all()
    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('admin/manage_records.html', subdomains=subdomains, settings=settings)

@bp.route('/delete_record/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    if not current_user.is_admin:
        flash('您没有权限执行此操作')
        return redirect(url_for('frontend.index'))
    
    subdomain = Subdomain.query.get_or_404(record_id)
    db.session.delete(subdomain)
    db.session.commit()
    flash('解析记录已删除')
    return redirect(url_for('admin.manage_records'))

@bp.route('/manage_users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('admin/manage_users.html', users=users, settings=settings)

@bp.route('/toggle_user_ban/<int:user_id>', methods=['POST'])
@login_required
def toggle_user_ban(user_id):
    if not current_user.is_admin:
        flash('您没有权限执行此操作')
        return redirect(url_for('frontend.index'))
    
    user = User.query.get_or_404(user_id)
    user.is_banned = not user.is_banned
    db.session.commit()
    flash(f'用户 {user.username} 已{"封禁" if user.is_banned else "解封"}')
    return redirect(url_for('admin.manage_users'))

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('您没有权限执行此操作')
        return redirect(url_for('frontend.index'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'用户 {user.username} 已删除')
    return redirect(url_for('admin.manage_users'))

@bp.route('/adjust_user_points/<int:user_id>', methods=['POST'])
@login_required
def adjust_user_points(user_id):
    if not current_user.is_admin:
        flash('您没有权限执行此操作')
        return redirect(url_for('frontend.index'))
    
    user = User.query.get_or_404(user_id)
    points_change = int(request.form['points_change'])
    user.points += points_change
    db.session.commit()
    flash(f'用户 {user.username} 积分已{"增加" if points_change > 0 else "减少"} {abs(points_change)}')
    return redirect(url_for('admin.manage_users'))

@bp.route('/system_settings', methods=['GET', 'POST'])
@login_required
@admin_required
def system_settings():
    settings = SystemSettings.query.first() or SystemSettings()
    
    if request.method == 'POST':
        settings.system_name = request.form['system_name']
        settings.forbidden_prefixes = request.form['forbidden_prefixes']
        db.session.add(settings)
        db.session.commit()
        flash('系统设置已更新', 'success')
        return redirect(url_for('admin.system_settings'))

    return render_template('admin/system_settings.html', settings=settings)

@bp.route('/add_card', methods=['GET', 'POST'])
@login_required
@admin_required
def add_card():
    if request.method == 'POST':
        generated_code = request.form['generated_code']
        usable_count = request.form['usable_count']
        point = request.form['points']

        new_card = Card(code=generated_code, points=point, can_used=usable_count) 
        db.session.add(new_card)
        db.session.commit()
        flash(f'卡密添加成功: {generated_code}', 'success')  # 使用 flash 显示生成的卡密
        return redirect(url_for('admin.dashboard'))
    
    settings = SystemSettings.query.first()  # 获取系统设置
    return render_template('admin/add_card.html', settings=settings)











