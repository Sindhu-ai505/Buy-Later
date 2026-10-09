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


def infer_category(text: str) -> str:
    """Infers product category from title keywords."""
    t = text.lower()
    if any(k in t for k in ["phone", "laptop", "headphone", "earphone", "tablet", "watch", "camera", "charger", "monitor", "speaker", "bluetooth", "tv", "mouse", "keyboard"]):
        return "Electronics"
    if any(k in t for k in ["shirt", "t-shirt", "jeans", "dress", "jacket", "hoodie", "pants", "kurta", "saree", "sweater", "clothing"]):
        return "Clothing"
    if any(k in t for k in ["shoe", "sneaker", "boot", "sandal", "slipper", "footwear"]):
        return "Footwear"
    if any(k in t for k in ["book", "novel", "textbook", "hardcover", "paperback"]):
        return "Books"
    if any(k in t for k in ["cookware", "pan", "bottle", "knife", "lamp", "curtain", "pillow", "bedsheet", "kitchen", "sofa", "chair", "blender", "kettle"]):
        return "Home & Kitchen"
    if any(k in t for k in ["dumbbell", "yoga", "gym", "treadmill", "cycle", "protein", "fitness"]):
        return "Fitness"
    if any(k in t for k in ["serum", "cream", "shampoo", "perfume", "lipstick", "lotion", "sunscreen", "skincare"]):
        return "Beauty"
    return "General"


def extract_from_url(url: str) -> Dict[str, Any]:
    """
    Extracts product name, price, image, and description from a URL.
    Robust extraction with store selectors, Open Graph, JSON-LD, and URL-slug fallbacks.
    """
    from urllib.parse import urlparse, unquote

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

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

    soup = None
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
        }
        resp = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
    except Exception as fetch_err:
        result["description"] = f"Direct fetch note: {str(fetch_err)}"

    try:

        if soup:
            # 1. Product Name: Check e-commerce specific IDs first
            amz_title = soup.find("span", id="productTitle") or soup.find("h1", id="title")
            fk_title = soup.find("h1", class_=re.compile(r"(_6EBuvT|VU-ZEz|B_NuCI)"))
            og_title = soup.find("meta", property="og:title")
            twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
            meta_title = soup.find("meta", attrs={"name": "title"})
            title_tag = soup.find("title")

            if amz_title and amz_title.get_text(strip=True):
                result["name"] = amz_title.get_text(strip=True)
            elif fk_title and fk_title.get_text(strip=True):
                result["name"] = fk_title.get_text(strip=True)
            elif og_title and og_title.get("content"):
                result["name"] = og_title["content"].strip()
            elif twitter_title and twitter_title.get("content"):
                result["name"] = twitter_title["content"].strip()
            elif meta_title and meta_title.get("content"):
                result["name"] = meta_title["content"].strip()
            elif title_tag and title_tag.string:
                result["name"] = title_tag.string.strip()

            # 2. Image
            amz_img = soup.find("img", id=re.compile(r"(landingImage|imgBlkFront)"))
            fk_img = soup.find("img", class_=re.compile(r"(_396cs4|DByuf4)"))
            og_image = soup.find("meta", property="og:image")
            if amz_img and amz_img.get("src"):
                result["image_path"] = amz_img["src"].strip()
            elif fk_img and fk_img.get("src"):
                result["image_path"] = fk_img["src"].strip()
            elif og_image and og_image.get("content"):
                result["image_path"] = og_image["content"].strip()

            # 3. Description
            og_desc = soup.find("meta", property="og:description")
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if og_desc and og_desc.get("content"):
                result["description"] = og_desc["content"].strip()
            elif meta_desc and meta_desc.get("content"):
                result["description"] = meta_desc["content"].strip()

            # 4. JSON-LD structured data
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    if not script.string:
                        continue
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        data = data[0]
                    if isinstance(data, dict):
                        if data.get("@type") == "Product":
                            if not result["name"] and data.get("name"):
                                result["name"] = str(data["name"]).strip()
                            if data.get("brand"):
                                brand_val = data["brand"]
                                result["brand"] = brand_val.get("name", "") if isinstance(brand_val, dict) else str(brand_val)
                            offers = data.get("offers")
                            if isinstance(offers, dict) and "price" in offers:
                                result["price"] = float(re.sub(r"[^\d.]", "", str(offers["price"])))
                            elif isinstance(offers, list) and offers and "price" in offers[0]:
                                result["price"] = float(re.sub(r"[^\d.]", "", str(offers[0]["price"])))
                except Exception:
                    pass

            # 5. Price from meta tags or classes
            if result["price"] == 0.0:
                price_meta = soup.find("meta", property="product:price:amount") or soup.find("meta", attrs={"name": "twitter:data1"})
                if price_meta and price_meta.get("content"):
                    try:
                        clean_p = re.sub(r"[^\d.]", "", price_meta["content"])
                        if clean_p:
                            result["price"] = float(clean_p)
                    except ValueError:
                        pass

            if result["price"] == 0.0:
                amz_price = soup.find("span", class_="a-price-whole") or soup.find("span", class_="a-offscreen")
                fk_price = soup.find("div", class_=re.compile(r"(_30jeq3|Nx9bqj)"))
                if amz_price and amz_price.get_text(strip=True):
                    clean_p = re.sub(r"[^\d.]", "", amz_price.get_text(strip=True))
                    if clean_p:
                        try:
                            result["price"] = float(clean_p)
                        except ValueError:
                            pass
                elif fk_price and fk_price.get_text(strip=True):
                    clean_p = re.sub(r"[^\d.]", "", fk_price.get_text(strip=True))
                    if clean_p:
                        try:
                            result["price"] = float(clean_p)
                        except ValueError:
                            pass

        # 6. Fallback: If name was not found or is a generic site/bot-block title, extract from URL slug
        generic_titles = [
            "amazon", "amazon.in", "flipkart", "robot check", "just a moment...",
            "blocked", "access denied", "page not found", "404", "security check",
            "online shopping", "myntra", "sign in"
        ]
        is_invalid_name = (
            not result["name"] 
            or any(result["name"].lower().strip().startswith(g) for g in generic_titles)
            or len(result["name"].strip()) < 3
        )

        if is_invalid_name:
            path = unquote(urlparse(url).path)
            parts = [p for p in path.split("/") if p and not re.match(r"^(dp|p|gp|product|item|itm.*|B0[0-9A-Z]+)$", p, re.I)]
            if parts:
                slug = parts[0]
                slug_name = re.sub(r"[-_+]+", " ", slug).strip().title()
                if len(slug_name) >= 3 and not slug_name.isdigit():
                    result["name"] = slug_name

        # Clean site suffixes from name
        if result["name"]:
            cleaned_name = re.split(r"\s*[-|–:]\s*(Amazon|Flipkart|Myntra|eBay|Walmart|Shop)", result["name"], flags=re.I)[0]
            result["name"] = cleaned_name.strip()
            result["category"] = infer_category(result["name"])

        # Infer brand if not found
        if not result["brand"] and result["name"]:
            first_word = result["name"].split()[0]
            if len(first_word) >= 2 and first_word.isalpha():
                result["brand"] = first_word

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
