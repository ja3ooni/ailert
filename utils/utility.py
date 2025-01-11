import os
import re
import csv
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List


def load_template(template_path="static/newsletter.html") -> str:
    with open(template_path, 'r') as f:
        return f.read()

def generate_deterministic_id(item: Dict[str, Any], key_fields: List[str], prefix: str = "item") -> str:
    """
    Example:
        item = {
            "product_name": "Widget",
            "color": "blue",
            "timestamp": "2024-01-01"
        }
        id = generate_deterministic_id(
            item,
            key_fields=["product_name", "color"],
            prefix="prod"
        )
        # Result: prod-a1b2c3d4...
    """
    key_fields.sort()
    values = []
    for field in key_fields:
        if field not in item:
            raise KeyError(f"Required field '{field}' not found in item")
        value = item[field]
        values.append(str(value))

    combined_string = "||".join(values)
    hash_object = hashlib.sha256(combined_string.encode())
    hash_hex = hash_object.hexdigest()
    short_hash = hash_hex[:12]
    return f"{prefix}-{short_hash}"

def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to specified length at the nearest word boundary."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return truncated.rstrip('.,!?:;')

def get_formatted_timestamp():
    """Get current timestamp in YYYY-MM-DD format"""
    return datetime.now().strftime("%Y-%m-%d")


def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def save_to_csv(email):
    csv_file = 'db_handler/vault/recipients.csv'
    file_exists = os.path.exists(csv_file)

    try:
        with open(csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['email', 'subscribed_at'])
            writer.writerow([email, get_formatted_timestamp()])
        return True
    except Exception as e:
        logging.error(f"Error saving to CSV: {str(e)}")
        return False


def is_email_subscribed(email):
    """Check if email already exists in CSV"""
    csv_file = 'db_handler/vault/recipients.csv'
    if not os.path.exists(csv_file):
        return False

    try:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            return any(row[0] == email for row in reader)
    except Exception as e:
        logging.error(f"Error checking subscription: {str(e)}")
        return False