import requests

default_token = ""

class HuggingFaceScanner:
    def __init__(self, base_url, top_n=5, auth_token=default_token):
        self.base_url = base_url
        self.top_n = top_n
        self.auth_token = "Bearer "+auth_token
        self.response = {}

    def __top_models(self, top_n):
        url = self.base_url+"/models"
        response = requests.get(
            url, params={"limit": top_n, "full": "False", "config": "False"},
            headers={"Authorization":self.auth_token}
        )
        return []

    def __top_datasets(self, top_n):
        url = self.base_url+"/datasets"
        response = requests.get(
            url, params={"limit": top_n, "full": "False", "config": "False"},
            headers={"Authorization":self.auth_token}
        )
        return []

    def __top_apps(self, top_n):
        url = self.base_url+"/spaces"
        response = requests.get(
            url, params={"limit": top_n, "full": "False", "config": "False"},
            headers={"Authorization":self.auth_token}
        )
        return []

    def weekly_scanner(self):
        self.response["top_models"] =  self.__top_models(self.top_n)
        self.response["top_datasets"] = self.__top_datasets(self.top_n)
        self.response["top_apps"] = self.__top_apps(self.top_n)
        return self.response