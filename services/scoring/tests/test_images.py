import io

import httpx
from PIL import Image

from app.photos.images import LONG_EDGE, prepare_image, resize_to_long_edge


def _jpeg(width: int, height: int) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (width, height), (120, 100, 80)).save(out, format="JPEG")
    return out.getvalue()


def _dimensions(data: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(data)) as img:
        return img.size


def test_resize_to_long_edge_downscales_large_image():
    resized = resize_to_long_edge(_jpeg(3000, 2000))
    assert max(_dimensions(resized)) == LONG_EDGE


def test_resize_to_long_edge_preserves_aspect_ratio():
    w, h = _dimensions(resize_to_long_edge(_jpeg(2600, 1300)))
    assert round(w / h) == 2


def test_resize_to_long_edge_leaves_small_image_unscaled():
    assert _dimensions(resize_to_long_edge(_jpeg(800, 600))) == (800, 600)


def test_prepare_image_returns_base64_block_on_success():
    block = prepare_image("https://x/a.jpg", fetch=lambda _: _jpeg(1000, 800))
    assert block["type"] == "image"
    assert block["source"]["type"] == "base64"
    assert block["source"]["media_type"] == "image/jpeg"
    assert block["source"]["data"]


def test_prepare_image_falls_back_to_url_on_fetch_error():
    def boom(_: str) -> bytes:
        raise httpx.ConnectError("unreachable")

    block = prepare_image("https://x/a.jpg", fetch=boom)
    assert block["source"] == {"type": "url", "url": "https://x/a.jpg"}


def test_prepare_image_falls_back_to_url_on_undecodable_body():
    block = prepare_image("https://x/a.jpg", fetch=lambda _: b"not an image")
    assert block["source"]["type"] == "url"
