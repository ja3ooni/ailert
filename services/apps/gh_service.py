import jwt
import time
import requests
from bs4 import BeautifulSoup

default_pem = ""
default_clientId = ""

class GitHubScanner:
    def __init__(self, site_url,  top_n=5, pem_path=default_pem, client_id=default_clientId):
        self.site_url = site_url
        self.top_n = top_n
        self.pem_path = pem_path
        self.client_id = client_id
        self.response = []

    def __gh_authenticate(self):
        with open(self.pem_path, 'rb') as pem_file:
            signing_key = pem_file.read()

        payload = {
            'iat': int(time.time()),
            'exp': int(time.time()) + 600,
            'iss': self.client_id
        }

        encoded_jwt = jwt.encode(payload, signing_key, algorithm='RS256')
        return encoded_jwt

    def __extract_from_html(self, link):
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

                self.response.append({
                    'name': name,
                    'description': description,
                    'stars': int(stars) if stars.isdigit() else stars,
                    'forks': int(forks) if forks.isdigit() else forks
                })

            return self.response
        except Exception as e:
            print(f"Error: {str(e)}")

    def get_trending_repos(self):
        pass

    def daily_trending_repos(self):
        repositories = self.__extract_from_html(self.site_url)
        return repositories

    def weekly_trending_repos(self):
        repositories = self.__extract_from_html(self.site_url)
        return  repositories
