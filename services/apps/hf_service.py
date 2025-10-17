import configparser

import requests

config = configparser.ConfigParser()
config.read('db_handler/vault/secrets.ini')

# Handle missing HuggingFace config gracefully
try:
    default_token = config["HuggingFace"]["token"]
except KeyError:
    default_token = "your_huggingface_token_here"

class HuggingFaceScanner:
    def __init__(self, base_url, top_n=5, auth_token=default_token):
        self.base_url = base_url
        self.top_n = top_n
        self.auth_token = "Bearer "+auth_token
        self.response = {}

    def _top_models(self, top_n):
        url = self.base_url+"/api/models"
        response = requests.get(
            url, params={"limit": top_n, "full": "True", "config": "False"},
            headers={"Authorization":self.auth_token}
        )
        return [{"title":model["modelId"],
                 "link":self.base_url+model["id"],
                 "summary": model["author"],
                 "source":"HuggingFace",
                 "engagement": str(model["trendingScore"])}for model in response.json()]

    def _top_datasets(self, top_n):
        url = self.base_url+"/api/datasets"
        response = requests.get(
            url, params={"limit": top_n, "full": "False"},
            headers={"Authorization":self.auth_token}
        )
        return [{"title": dataset["id"],
                 "link": self.base_url + dataset["id"],
                 "summary": dataset["author"],
                 "source": "HuggingFace",
                 "engagement": str(dataset["trendingScore"])} for dataset in response.json()]

    def _top_apps(self, top_n):
        url = self.base_url+"/api/spaces"
        response = requests.get(
            url, params={"limit": top_n, "full": "True"},
            headers={"Authorization":self.auth_token}
        )
        return [{"title": apps["id"],
                 "link": self.base_url + apps["id"],
                 "summary": apps["author"],
                 "source": "HuggingFace",
                 "engagement": str(apps["trendingScore"])} for apps in response.json()]

    def weekly_scanner(self):
        self.response["top_models"] =  self._top_models(self.top_n)
        self.response["top_datasets"] = self._top_datasets(self.top_n)
        self.response["top_apps"] = self._top_apps(self.top_n)
        return self.response