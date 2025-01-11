import jwt
import time
import requests
import configparser
from db_handler import Repo
from bs4 import BeautifulSoup

config = configparser.ConfigParser()
config.read('db_handler/vault/secrets.ini')

default_pem = config["GitHub"]["pem_path"]
default_clientId = config["GitHub"]["client_id"]

class GitHubScanner:
    def __init__(self, site_url, ftype, top_n=5, pem_path=default_pem, client_id=default_clientId):
        self.site_url = site_url
        self.ftype = ftype
        self.top_n = top_n
        self.pem_path = pem_path
        self.client_id = client_id
        self.response = []

    def _gh_authenticate(self):
        with open(self.pem_path, 'rb') as pem_file:
            signing_key = pem_file.read()

        payload = {
            'iat': int(time.time()),
            'exp': int(time.time()) + 600,
            'iss': self.client_id
        }

        encoded_jwt = jwt.encode(payload, signing_key, algorithm='RS256')
        return encoded_jwt

    def _extract_from_html(self, link):
        repos = []
        try:
            response = requests.get(link)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            repo_list = soup.find_all('article', class_='Box-row')

            for repo in repo_list:
                name = repo.find('h2', class_='h3').text.strip().replace('\n', '').replace(' ', '')

                description = repo.find('p', class_='col-9 color-fg-muted my-1 pr-4')
                description = description.text.strip() if description else "No description provided."

                stars_element = repo.find('a', class_='Link Link--muted d-inline-block mr-3') or \
                                repo.find('a', class_='Link--muted d-inline-block mr-3')
                stars = stars_element.text.strip().replace(',', '') if stars_element else "0"

                fork_elements = repo.find_all('a', class_='Link Link--muted d-inline-block mr-3') or \
                                repo.find_all('a', class_='Link--muted d-inline-block mr-3')
                forks = fork_elements[1].text.strip().replace(',', '') if len(fork_elements) > 1 else "0"

                repos.append({
                    'name': name,
                    'description': description,
                    'stars': str(stars),
                    'forks': str(forks)
                })

            return repos[:self.top_n]
        except Exception as e:
            print(f"Error: {str(e)}")

    def _daily_trending_repos(self):
        repositories = self._extract_from_html(self.site_url)
        return repositories

    def _weekly_trending_repos(self):
        repositories = self._extract_from_html(self.site_url)
        return  repositories

    async def get_trending_repos(self):
        if self.ftype == "daily":
            repositories = self._daily_trending_repos()
        else:
            repositories = self._weekly_trending_repos()
        self.response.extend(Repo(
            name = repo["name"],
            link = "",
            summary = repo["description"],
            source = "GitHub",
            engagement = repo["stars"]) for repo in repositories)
        return self.response