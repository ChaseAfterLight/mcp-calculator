import hashlib
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


logger = logging.getLogger("SpeciesImageProvider")

INATURALIST_API_BASE = "https://api.inaturalist.org/v1"
PIXABAY_API_BASE = "https://pixabay.com/api/"
DEFAULT_TIMEOUT = 15


class SpeciesImageProvider:
    """Find and download a cover image for a species card."""

    def __init__(self, download_dir: str | Path = "cards/source_images"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = "mcp-calculator/1.0"

    def resolve(self, *, chinese_name: str, latin_name: str, category: str) -> dict[str, Any] | None:
        candidates: list[dict[str, Any] | None] = []

        if category in {"plant", "animal"}:
            candidates.append(self._safe_search(self._search_inaturalist, latin_name=latin_name))
            candidates.append(self._safe_search(self._search_pixabay, query=latin_name or chinese_name, category=category))
        else:
            candidates.append(self._safe_search(self._search_pixabay, query=chinese_name or latin_name, category=category))
            candidates.append(self._safe_search(self._search_pixabay, query=latin_name or chinese_name, category=category))

        for item in candidates:
            if not item or not item.get("image_url"):
                continue
            downloaded = self._download_image(item["image_url"], chinese_name=chinese_name, latin_name=latin_name)
            if not downloaded and item.get("fallback_image_url") and item["fallback_image_url"] != item["image_url"]:
                downloaded = self._download_image(
                    item["fallback_image_url"],
                    chinese_name=chinese_name,
                    latin_name=latin_name,
                )
            if downloaded:
                item["source_image_path"] = str(downloaded)
                return item
        return None

    def _safe_search(self, func, **kwargs):
        try:
            return func(**kwargs)
        except Exception as exc:
            logger.warning("搜索物种图片失败 %s: %s", getattr(func, "__name__", "provider"), exc)
            return None

    def _search_inaturalist(self, *, latin_name: str) -> dict[str, Any] | None:
        if not latin_name:
            return None

        payload = self._get_json(
            f"{INATURALIST_API_BASE}/observations",
            {
                "taxon_name": latin_name,
                "photos": "true",
                "photo_licensed": "true",
                "quality_grade": "research",
                "order_by": "votes",
                "order": "desc",
                "per_page": 10,
            },
        )
        for record in payload.get("results", []):
            observation_photos = record.get("observation_photos") or []
            for item in observation_photos:
                photo = item.get("photo") or {}
                image_url = photo.get("url")
                license_code = photo.get("license_code")
                if not image_url or not license_code:
                    continue
                return {
                    "provider": "inaturalist",
                    "image_url": self._upgrade_inaturalist_image_url(image_url),
                    "fallback_image_url": image_url,
                    "source_page_url": record.get("uri") or "",
                    "license": license_code,
                    "author": photo.get("attribution") or "",
                    "title": (record.get("taxon") or {}).get("name") or latin_name,
                    "faves_count": record.get("faves_count") or 0,
                    "votes_count": record.get("cached_votes_total") or 0,
                }
        return None

    def _search_pixabay(self, *, query: str, category: str) -> dict[str, Any] | None:
        api_key = os.getenv("PIXABAY_API_KEY", "").strip()
        if not api_key or not query:
            return None

        pixabay_category = {
            "animal": "animals",
            "plant": "nature",
            "mineral": "science",
        }.get(category, "nature")

        payload = self._get_json(
            PIXABAY_API_BASE,
            {
                "key": api_key,
                "q": query,
                "lang": "zh",
                "image_type": "photo",
                "category": pixabay_category,
                "safesearch": "true",
                "per_page": 3,
            },
        )
        hits = payload.get("hits") or []
        if not hits:
            return None

        hit = hits[0]
        image_url = hit.get("largeImageURL") or hit.get("webformatURL")
        if not image_url:
            return None

        return {
            "provider": "pixabay",
            "image_url": image_url,
            "source_page_url": hit.get("pageURL") or "",
            "license": "Pixabay Content License",
            "author": hit.get("user") or "",
            "title": ",".join((hit.get("tags") or "").split(",")[:3]).strip(),
        }

    def _download_image(self, url: str, *, chinese_name: str, latin_name: str) -> Path | None:
        safe_name = self._sanitize_filename(latin_name or chinese_name or "species")
        suffix = Path(url.split("?")[0]).suffix or ".jpg"
        output_path = self.download_dir / f"{safe_name}_{hashlib.md5(url.encode('utf-8')).hexdigest()[:10]}{suffix}"

        if output_path.exists():
            return output_path

        request = Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urlopen(request, timeout=DEFAULT_TIMEOUT) as response, open(output_path, "wb") as f:
                shutil.copyfileobj(response, f)
            return output_path
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            logger.warning("下载物种图片失败 %s: %s", url, exc)
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            return None

    def _get_json(self, base_url: str, params: dict[str, Any]) -> dict[str, Any]:
        query = urlencode({k: v for k, v in params.items() if v not in (None, "")})
        request = Request(f"{base_url}?{query}", headers={"User-Agent": self.user_agent})
        with urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))

    def _sanitize_filename(self, value: str) -> str:
        safe = "".join(ch if ch.isascii() and (ch.isalnum() or ch in {"_", "-"}) else "_" for ch in value.strip())
        return safe[:80] or "species"

    def _upgrade_inaturalist_image_url(self, image_url: str) -> str:
        if "/square." in image_url:
            return image_url.replace("/square.", "/large.")
        return image_url
