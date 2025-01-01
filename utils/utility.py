import hashlib
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
