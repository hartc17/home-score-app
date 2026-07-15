from pathlib import Path

from app.listings.parser import parse_listing_html

_FIXTURE = (Path(__file__).parent / "fixtures" / "sample_listing.html").read_text()
_URL = "https://listings.example.com/42-maple-street"


def test_parse_extracts_core_facts_from_jsonld():
    facts = parse_listing_html(_URL, _FIXTURE)
    assert facts.price == 575000
    assert facts.beds == 4
    assert facts.baths == 3
    assert facts.sqft == 2450
    assert facts.year_built == 1998
    assert facts.home_type == "single_family"
    assert facts.address == "42 Maple Street, Saratoga Springs, NY, 12866"


def test_parse_collects_and_dedupes_photo_urls():
    facts = parse_listing_html(_URL, _FIXTURE)
    assert "https://cdn.example.com/photos/living.jpg" in facts.photo_urls
    assert "https://cdn.example.com/photos/hero.jpg" in facts.photo_urls
    assert "https://cdn.example.com/photos/bedroom.webp" in facts.photo_urls
    # living.jpg appears in JSON-LD, og:image is absent for it, and an <img>; only once.
    assert facts.photo_urls.count("https://cdn.example.com/photos/living.jpg") == 1
    # Relative image sources are skipped.
    assert all(u.startswith("http") for u in facts.photo_urls)


def test_parse_preserves_url():
    assert parse_listing_html(_URL, _FIXTURE).url == _URL


def test_parse_falls_back_to_text_when_no_jsonld():
    html = "<html><body><p>3 beds 2 baths 1,800 sqft $450,000 built in 2005</p></body></html>"
    facts = parse_listing_html(_URL, html)
    assert facts.beds == 3
    assert facts.baths == 2
    assert facts.sqft == 1800
    assert facts.price == 450000
    assert facts.year_built == 2005


def test_parse_empty_page_returns_url_only():
    facts = parse_listing_html(_URL, "<html><body></body></html>")
    assert facts.url == _URL
    assert facts.price is None
    assert facts.photo_urls == []
