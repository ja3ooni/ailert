import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class ProductHuntScanner:
    def __init__(self, site_url, graph_url, top_n=5):
        self.site_url = site_url
        self.graph_url = graph_url
        self.top_n = top_n
        self.response = []

    def get_last_week_top_products(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(self.site_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            last_week_section = soup.find("section", string="Last Week's Top Products")
            if not last_week_section:
                print("Could not find 'Last Week's Top Products' section.")
                return []

            products = []
            for product in last_week_section.find_all("li"):
                title = product.find("h3").get_text(strip=True) if product.find("h3") else "No Title"
                link = product.find("a", href=True)["href"] if product.find("a", href=True) else "No Link"
                products.append({"title": title, "link": f"{self.site_url}{link}"})

            return products
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []

    def get_last_month_top_products(self, api_key):
        query = """
        query ($dateFrom: DateTime!, $dateTo: DateTime!) {
          posts(first: 10, postedAfter: $dateFrom, postedBefore: $dateTo, order: VOTES_COUNT) {
            edges {
              node {
                id
                name
                tagline
                url
                votesCount
              }
            }
          }
        }
        """
        today = datetime.utcnow()
        first_day_of_this_month = datetime(today.year, today.month, 1)
        last_day_of_last_month = first_day_of_this_month - timedelta(days=1)
        first_day_of_last_month = datetime(last_day_of_last_month.year, last_day_of_last_month.month, 1)

        variables = {
            "dateFrom": first_day_of_last_month.isoformat(),
            "dateTo": last_day_of_last_month.isoformat()
        }

        # Set headers with API key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.graph_url, json={"query": query, "variables": variables}, headers=headers)
            response.raise_for_status()
            data = response.json()

            products = data.get("data", {}).get("posts", {}).get("edges", [])
            if not products:
                print("No products found for last month.")
                return []

            result = []
            for product in products:
                node = product["node"]
                result.append({
                    "title": node["name"],
                    "summary": node["tagline"],
                    "link": node["url"],
                    "engagement": node["votesCount"],
                    "source": "Product Hunt"
                })

            return result
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
