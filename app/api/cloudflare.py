import requests

class CloudflareAPI:
    def __init__(self, api_key, api_id):
        self.api_key = api_key
        self.api_id = api_id
        self.base_url = "https://api.cloudflare.com/client/v4"

    def _make_request(self, method, endpoint, params=None, json=None):
        url = f"{self.base_url}{endpoint}"
        headers = {
            "X-Auth-Email": self.api_id,
            "X-Auth-Key": self.api_key,
            "Content-Type": "application/json"
        }
        response = requests.request(method, url, headers=headers, params=params, json=json)
        return response.json()

    def get_domains(self):
        response = self._make_request("GET", "/zones")
        if response.get("success"):
            return [{"id": zone["id"], "name": zone["name"]} for zone in response["result"]]
        return []

    def get_zone_id(self, domain_name):
        domains = self.get_domains()
        for domain in domains:
            if domain["name"] == domain_name:
                return domain["id"]
        return None

    def add_dns_record(self, domain_name, name, content, type="A", ttl=600, proxied=False):
        zone_id = self.get_zone_id(domain_name)
        if not zone_id:
            print(f"Error: Zone ID for {domain_name} not found.")
            return False

        data = {
            "type": type,
            "name": name,
            "content": content,
            "ttl": ttl,
            "proxied": proxied
        }
        response = self._make_request("POST", f"/zones/{zone_id}/dns_records", json=data)
        return response.get("result", {}).get("id", None)

    def modify_record(self, domain_name, record_id, name, content, type="A", ttl=600, proxied=False):
        zone_id = self.get_zone_id(domain_name)
        if not zone_id:
            print(f"Error: Zone ID for {domain_name} not found.")
            return False

        data = {
            "type": type,
            "name": name,
            "content": content,
            "ttl": ttl,
            "proxied": proxied
        }
        response = self._make_request("PATCH", f"/zones/{zone_id}/dns_records/{record_id}", json=data)
        return response.get("success", False)

    def delete_record(self, domain_name, record_id):
        zone_id = self.get_zone_id(domain_name)
        if not zone_id:
            print(f"Error: Zone ID for {domain_name} not found.")
            return False

        response = self._make_request("DELETE", f"/zones/{zone_id}/dns_records/{record_id}")
        return response.get("success", False)

    def get_record_id(self, domain_name, name, type="A"):
        zone_id = self.get_zone_id(domain_name)
        if not zone_id:
            print(f"Error: Zone ID for {domain_name} not found.")
            return None

        params = {
            "name": name,
            "type": type
        }
        response = self._make_request("GET", f"/zones/{zone_id}/dns_records", params=params)
        if response.get("success"):
            for record in response["result"]:
                if record["name"] == name and record["type"] == type:
                    return record["id"]
        return None

    def create_subdomain(self, subdomain_name, domain_name, record_type, record_value):
        return self.add_dns_record(domain_name, f"{subdomain_name}.{domain_name}", record_value, record_type)