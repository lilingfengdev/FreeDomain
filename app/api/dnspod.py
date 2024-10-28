import requests

class DNSPodAPI:
    def __init__(self, api_id, api_token):
        self.base_url = "https://dnsapi.cn"
        self.common_params = {
            "login_token": f"{api_id},{api_token}",
            "format": "json",
        }

    def _make_request(self, endpoint, params):
        url = f"{self.base_url}/{endpoint}"
        data = {**self.common_params, **params}
        response = requests.post(url, data=data)
        return response.json()

    def get_domains(self):
        response = self._make_request("Domain.List", {})
        if response["status"]["code"] == "1":
            return [{"id": domain["id"], "name": domain["name"]} for domain in response["domains"]]
        return []

    def create_subdomain(self, domain, sub_domain, record_type, value, line="默认", ttl=600):
        params = {
            "domain": domain,
            "sub_domain": sub_domain,
            "record_type": record_type,
            "record_line": line,
            "value": value,
            "ttl": ttl,
        }
        response = self._make_request("Record.Create", params)
        return response.get("record", {}).get("id", None)

    def modify_record(self, domain, record_id, sub_domain, record_type, value, line="默认", ttl=600):
        params = {
            "domain": domain,
            "record_id": record_id,
            "sub_domain": sub_domain,
            "record_type": record_type,
            "record_line": line,
            "value": value,
            "ttl": ttl,
        }
        response = self._make_request("Record.Modify", params)
        return response["status"]["code"] == "1"

    def delete_record(self, domain, record_id):
        params = {
            "domain": domain,
            "record_id": record_id,
        }
        response = self._make_request("Record.Remove", params)
        return response["status"]["code"] == "1"

    def get_record_id(self, domain, sub_domain, record_type):
        params = {
            "domain": domain,
        }
        response = self._make_request("Record.List", params)
        if response["status"]["code"] == "1":
            for record in response["records"]:
                if record["name"] == sub_domain and record["type"] == record_type:
                    return record["id"]
        return None