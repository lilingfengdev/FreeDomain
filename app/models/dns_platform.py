from app import db
from app.api.dnspod import DNSPodAPI
from app.api.cloudflare import CloudflareAPI

class DNSPlatform(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    platform_type = db.Column(db.String(20), nullable=False)
    api_key = db.Column(db.String(128), nullable=False)
    api_id = db.Column(db.String(128))  # 新增字段，用于存储 DNSPod 的 API ID
    note = db.Column(db.Text)

    def get_api(self):
        if self.platform_type == 'dnspod':
            return DNSPodAPI(self.api_id, self.api_key)  # 使用 api_id 和 api_key
        elif self.platform_type == 'cloudflare':
            return CloudflareAPI(self.api_key, self.api_id)
        else:
            raise ValueError(f"Unsupported platform type: {self.platform_type}")

    def __repr__(self):
        return f'<DNSPlatform {self.name}>'
