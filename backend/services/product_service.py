"""backend/services/product_service.py

Product analysis service supporting:
1. Manual entry
2. Screenshot OCR extraction via EasyOCR
3. Web URL extraction via requests + BeautifulSoup (best-effort)
"""

import os
import re
import json
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from PIL import Image

# Initialize EasyOCR reader lazily to avoid startup overhead
_easyocr_reader = None


def get_ocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        # Use CPU mode for compatibility
        _easyocr_reader = easyocr.Reader(["en"], gpu=False)
    return _easyocr_reader


def extract_from_url(url: str) -> Dict[str, Any]:
    """
    Extracts product name, price, image, and description from a URL.
    Best-effort extraction using Open Graph, standard meta tags, and JSON-LD.
    If fields cannot be found, leaves them clear for user confirmation.
    """
    result = {
        "name": "",
        "brand": "",
        "category": "General",
        "price": 0.0,
        "product_url": url,
        "image_path": "",
        "description": "",
        "discount": 0.0,
        "extraction_source": "url",
        "raw_text": "",
    }

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            result["description"] = f"URL returned status code {resp.status_code}. Please verify and enter details manually."
            return result

        soup = BeautifulSoup(resp.content, "html.parser")

        # 1. Title / Name
        og_title = soup.find("meta", property="og:title")
        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        title_tag = soup.find("title")

        if og_title and og_title.get("content"):
            result["name"] = og_title["content"].strip()
        elif twitter_title and twitter_title.get("content"):
            result["name"] = twitter_title["content"].strip()
        elif title_tag and title_tag.string:
            result["name"] = title_tag.string.strip()

        # 2. Image
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            result["image_path"] = og_image["content"].strip()

        # 3. Description
        og_desc = soup.find("meta", property="og:description")
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if og_desc and og_desc.get("content"):
            result["description"] = og_desc["content"].strip()
        elif meta_desc and meta_desc.get("content"):
            result["description"] = meta_desc["content"].strip()

        # 4. Price & Brand from JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                if not script.string:
                    continue
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]

                if isinstance(data, dict):
                    # Check Product schema
                    if data.get("@type") == "Product":
                        if not result["name"] and data.get("name"):
                            result["name"] = str(data["name"])
                        if data.get("brand"):
                            brand_val = data["brand"]
                            result["brand"] = brand_val.get("name", "") if isinstance(brand_val, dict) else str(brand_val)

                        offers = data.get("offers")
                        if isinstance(offers, dict) and "price" in offers:
                            result["price"] = float(offers["price"])
                        elif isinstance(offers, list) and offers and "price" in offers[0]:
                            result["price"] = float(offers[0]["price"])
            except Exception:
                pass

        # 5. Price from meta tags if not already found
        if result["price"] == 0.0:
            price_meta = soup.find("meta", property="product:price:amount")
            if price_meta and price_meta.get("content"):
                try:
                    result["price"] = float(re.sub(r"[^\d.]", "", price_meta["content"]))
                except ValueError:
                    pass

        # Clean name if it has long site suffixes like " | Amazon.in"
        if result["name"]:
            cleaned_name = re.split(r"\s*[-|–]\s*(Amazon|Flipkart|Myntra|eBay|Walmart)", result["name"])[0]
            result["name"] = cleaned_name.strip()

    except Exception as e:
        result["description"] = f"Extraction note: Could not parse URL fully ({str(e)}). Please review the fields."

    return result


def extract_from_image(image_path: str) -> Dict[str, Any]:
    """
    Extracts text, price, brand, and discounts from a product screenshot using EasyOCR.
    """
    result = {
        "name": "",
        "brand": "",
        "category": "General",
        "price": 0.0,
        "product_url": "",
        "image_path": image_path,
        "description": "",
        "discount": 0.0,
        "extraction_source": "ocr",
        "raw_text": "",
    }

    if not os.path.exists(image_path):
        return result

    try:
        reader = get_ocr_reader()
        ocr_results = reader.readtext(image_path, detail=0)
        full_text = " ".join(ocr_results)
        result["raw_text"] = full_text

        # Extract price using regex: ₹, Rs., $, or plain numbers with currency cues
        price_patterns = [
            r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)",
            r"\$\s*([\d,]+(?:\.\d{1,2})?)",
            r"(?:price|mrp|deal price|now)\s*:?\s*(?:₹|Rs\.?|\$)?\s*([\d,]+(?:\.\d{1,2})?)",
        ]
        for pattern in price_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                clean_num = match.group(1).replace(",", "")
                try:
                    val = float(clean_num)
                    if 10.0 <= val <= 500000.0:
                        result["price"] = val
                        break
                except ValueError:
                    continue

        # Extract discount percentage: e.g. "25% off"
        discount_match = re.search(r"(\d{1,2})\s*%\s*(?:off|discount)", full_text, re.IGNORECASE)
        if discount_match:
            result["discount"] = float(discount_match.group(1))

        # Guess product name from the most prominent non-price, non-header line
        stopwords = {"cart", "buy now", "add to cart", "ratings", "reviews", "free delivery", "order now"}
        candidate_lines = []
        for line in ocr_results:
            clean_line = line.strip()
            if len(clean_line) > 5 and not any(w in clean_line.lower() for w in stopwords):
                if not re.search(r"^(₹|\$|rs\.|\d+%)", clean_line, re.IGNORECASE):
                    candidate_lines.append(clean_line)

        if candidate_lines:
            result["name"] = candidate_lines[0]
            if len(candidate_lines) > 1:
                result["description"] = " ".join(candidate_lines[1:4])

        # Infer category heuristics from keywords
        text_lower = full_text.lower()
        if any(w in text_lower for w in ["headphone", "earphone", "laptop", "phone", "tv", "camera", "tablet", "watch"]):
            result["category"] = "Electronics"
        elif any(w in text_lower for w in ["shirt", "t-shirt", "shoes", "jacket", "dress", "pants", "sneaker"]):
            result["category"] = "Fashion"
        elif any(w in text_lower for w in ["book", "novel", "guide", "textbook"]):
            result["category"] = "Books"
        elif any(w in text_lower for w in ["desk", "chair", "lamp", "bottle", "kitchen", "cooker"]):
            result["category"] = "Home"

    except Exception as e:
        result["description"] = f"OCR Note: {str(e)}"

    return result
