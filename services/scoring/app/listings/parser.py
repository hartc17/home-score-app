from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from app.schemas import ListingFacts

_IMAGE_RE = re.compile(r"\.(?:jpe?g|png|webp)(?:\?|$)", re.IGNORECASE)
_MAX_PHOTOS = 40

_HOME_TYPE = {
    "singlefamilyresidence": "single_family",
    "house": "single_family",
    "residence": "single_family",
    "townhouse": "townhouse",
    "rowhouse": "townhouse",
    "apartment": "condo",
    "apartmentcomplex": "condo",
    "condominium": "condo",
}


def _num(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"[\d,]+(?:\.\d+)?", str(value))
    return float(match.group().replace(",", "")) if match else None


def _iter_jsonld(soup: BeautifulSoup) -> list[dict]:
    objects: list[dict] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                objects.append(node)
                if "@graph" in node:
                    stack.append(node["@graph"])
    return objects


def _offer_price(node: dict) -> float | None:
    offers = node.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if isinstance(offers, dict):
        return _num(offers.get("price") or offers.get("lowPrice"))
    return _num(node.get("price"))


def _address(node: dict) -> str | None:
    address = node.get("address")
    if isinstance(address, list):
        address = address[0] if address else None
    if isinstance(address, dict):
        parts = [
            address.get("streetAddress"),
            address.get("addressLocality"),
            address.get("addressRegion"),
            address.get("postalCode"),
        ]
        joined = ", ".join(p for p in parts if p)
        return joined or None
    if isinstance(address, str):
        return address
    return None


def _home_type(node: dict) -> str | None:
    types = node.get("@type")
    for t in types if isinstance(types, list) else [types]:
        if isinstance(t, str) and t.lower() in _HOME_TYPE:
            return _HOME_TYPE[t.lower()]
    return None


def _images(node: dict) -> list[str]:
    image = node.get("image")
    if isinstance(image, str):
        return [image]
    if isinstance(image, list):
        return [i for i in image if isinstance(i, str)]
    if isinstance(image, dict) and isinstance(image.get("url"), str):
        return [image["url"]]
    return []


def _from_jsonld(objects: list[dict], facts: dict, photos: list[str]) -> None:
    def put(key: str, value: object) -> None:
        if value is not None and facts.get(key) is None:
            facts[key] = value

    for node in objects:
        put("price", _offer_price(node))
        put("beds", _num(node.get("numberOfBedrooms")))
        put("baths", _num(node.get("numberOfBathroomsTotal") or node.get("numberOfBathrooms")))
        put("year_built", _num(node.get("yearBuilt")))
        floor = node.get("floorSize")
        if isinstance(floor, dict):
            put("sqft", _num(floor.get("value")))
        put("address", _address(node))
        put("home_type", _home_type(node))
        photos.extend(_images(node))


def _meta(soup: BeautifulSoup, prop: str) -> str | None:
    tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
    content = tag.get("content") if tag else None
    return content or None


def _from_meta(soup: BeautifulSoup, facts: dict, photos: list[str]) -> None:
    if facts.get("price") is None:
        facts["price"] = _num(_meta(soup, "product:price:amount") or _meta(soup, "og:price:amount"))
    if facts.get("address") is None:
        facts["address"] = _meta(soup, "og:title")
    for tag in soup.find_all("meta", property="og:image"):
        content = tag.get("content")
        if content:
            photos.append(content)


def _from_text(soup: BeautifulSoup, facts: dict) -> None:
    text = soup.get_text(" ", strip=True)
    patterns = {
        "price": r"\$\s?([\d,]{4,})",
        "beds": r"(\d+)\s*(?:beds?|bd|bedrooms?)\b",
        "baths": r"(\d+(?:\.\d)?)\s*(?:baths?|ba|bathrooms?)\b",
        "sqft": r"([\d,]{3,})\s*(?:sq\.?\s?ft|sqft|square\s?feet)",
        "year_built": r"(?:built|year built)[^\d]{0,10}(\d{4})",
    }
    for key, pattern in patterns.items():
        if facts.get(key) is not None:
            continue
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            facts[key] = _num(match.group(1))


def _collect_img_tags(soup: BeautifulSoup, photos: list[str]) -> None:
    for tag in soup.find_all("img"):
        src = tag.get("src") or tag.get("data-src")
        if isinstance(src, str) and src.startswith("http") and _IMAGE_RE.search(src):
            photos.append(src)


def _dedupe(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered[:_MAX_PHOTOS]


def parse_listing_html(url: str, html: str) -> ListingFacts:
    soup = BeautifulSoup(html, "html.parser")
    facts: dict = {}
    photos: list[str] = []

    _from_jsonld(_iter_jsonld(soup), facts, photos)
    _from_meta(soup, facts, photos)
    _from_text(soup, facts)
    _collect_img_tags(soup, photos)

    return ListingFacts(
        url=url,
        price=facts.get("price"),
        beds=facts.get("beds"),
        baths=facts.get("baths"),
        sqft=facts.get("sqft"),
        year_built=int(facts["year_built"]) if facts.get("year_built") else None,
        garage=facts.get("garage"),
        lot_sqft=facts.get("lot_sqft"),
        taxes_annual=facts.get("taxes_annual"),
        address=facts.get("address"),
        home_type=facts.get("home_type"),
        photo_urls=_dedupe(photos),
    )
