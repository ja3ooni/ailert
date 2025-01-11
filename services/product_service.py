from db_handler import Products, sites
from services.apps import HuggingFaceScanner, ProductHuntScanner

class ProductService:
    def __init__(self):
        self.hf_scanner = HuggingFaceScanner(sites["hf_base_url"],1)
        self.ph_scanner = ProductHuntScanner(sites["ph_site_url"], sites["ph_url"],1)
        self.products = []

    async def get_latest_products(self):
        hf_products = self.hf_scanner.weekly_scanner()
        ph_products = None #self.ph_scanner.get_last_week_top_products()
        final_dict = hf_products #+ ph_products
        for key, items in final_dict.items():
            for item in items:
                self.products.append(Products(
                    name = item["title"],
                    link = item["link"],
                    summary = item["summary"],
                    source = item["source"],
                    engagement = item["engagement"]
                    ))
        return self.products
