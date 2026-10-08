"""backend/services/my_stuff_service.py

Explainable similarity matching between candidate product and user's owned inventory (My Stuff).
Uses category comparison, normalized name matching, and keyword overlap (NO embeddings).
"""

import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models import MyStuff, Product


def normalize_text(text: str) -> set[str]:
    """Cleans text into a set of lowercased alphanumeric tokens, removing stopwords."""
    stopwords = {"a", "an", "the", "and", "or", "for", "with", "in", "on", "at", "by", "from", "of", "to"}
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    tokens = set(cleaned.split())
    return tokens - stopwords


def calculate_item_similarity(candidate_name: str, candidate_category: str, owned_name: str, owned_category: str) -> float:
    """Calculates explainable similarity score (0.0 to 1.0) based on category and word tokens."""
    c_cat = candidate_category.strip().lower()
    o_cat = owned_category.strip().lower()

    cat_match = (c_cat == o_cat) or (c_cat in o_cat) or (o_cat in c_cat)
    category_score = 0.5 if cat_match else 0.0

    c_tokens = normalize_text(candidate_name)
    o_tokens = normalize_text(owned_name)

    if not c_tokens or not o_tokens:
        token_score = 0.0
    else:
        intersection = c_tokens.intersection(o_tokens)
        union = c_tokens.union(o_tokens)
        token_score = len(intersection) / len(union) if union else 0.0

    # If category matches and there is token overlap (e.g., both contain "headphones" or "shoes")
    total_score = category_score + (0.5 * token_score)
    return round(total_score, 2)


def find_similar_owned_items(db: Session, user_id: int, product: Product) -> List[Dict[str, Any]]:
    """Finds all owned items that share category or keyword overlap with the candidate product."""
    owned_items = db.query(MyStuff).filter(MyStuff.user_id == user_id).all()
    matches = []

    for item in owned_items:
        sim = calculate_item_similarity(
            candidate_name=product.name,
            candidate_category=product.category,
            owned_name=item.product_name,
            owned_category=item.category,
        )

        # Consider a match if similarity >= 0.45 or (same category and any common keyword)
        if sim >= 0.40:
            matches.append({
                "id": item.id,
                "product_name": item.product_name,
                "category": item.category,
                "condition": item.condition,
                "usage_frequency": item.usage_frequency,
                "price": item.price,
                "similarity_score": sim,
                "explanation": f"You already own '{item.product_name}' in the '{item.category}' category (condition: {item.condition}).",
            })

    matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    return matches
