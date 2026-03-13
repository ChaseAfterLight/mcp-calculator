import base64
import json
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright


class CardRenderer:
    """Species card renderer."""

    def __init__(self, template_dir="templates", output_dir="cards"):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.metadata_dir = self.output_dir / "metadata"
        self.index_file = self.output_dir / "index.json"

        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        self.category_map = {
            "plant": {"prefix": "P", "icon": "🌿", "label": "植物类"},
            "animal": {"prefix": "A", "icon": "🦊", "label": "动物类"},
            "mineral": {"prefix": "M", "icon": "💎", "label": "矿物类"},
        }

        self._ensure_directories()

    def _ensure_directories(self):
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        if not self.index_file.exists():
            self.index_file.write_text("[]", encoding="utf-8")

    def _load_index(self):
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_index(self, index):
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def _get_next_card_id(self, category):
        prefix = self.category_map[category]["prefix"]
        index = self._load_index()

        max_num = 0
        for card in index:
            card_id = card.get("card_id", "")
            if card_id.startswith(prefix):
                try:
                    num = int(card_id[1:])
                    max_num = max(max_num, num)
                except Exception:
                    pass

        return f"{prefix}{max_num + 1:03d}"

    def _find_existing_card(self, card_id):
        for card in self._load_index():
            if card.get("card_id") == card_id:
                return card
        return None

    def _resolve_template_image_src(self, image_path):
        if not image_path:
            return None
        if str(image_path).startswith(("http://", "https://", "file://")):
            return str(image_path)
        path = Path(image_path)
        if not path.exists():
            return None

        suffix = path.suffix.lower()
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }.get(suffix)
        if not mime_type:
            return path.resolve().as_uri()

        return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

    def _load_template_data(self, species_data, card_id):
        category = species_data.get("category", "plant")
        category_info = self.category_map.get(category, self.category_map["plant"])
        source_image_path = species_data.get("source_image_path") or species_data.get("image_path")

        return {
            "card_id": card_id,
            "category": category,
            "category_icon": category_info["icon"],
            "category_label": category_info["label"],
            "chinese_name": species_data.get("chinese_name", ""),
            "latin_name": species_data.get("latin_name", ""),
            "features": species_data.get("features", []),
            "habitat": species_data.get("habitat", ""),
            "observation_season": species_data.get("observation_season", ""),
            "protection_level": species_data.get("protection_level", ""),
            "fun_fact": species_data.get("fun_fact", ""),
            "rarity": species_data.get("rarity", 3),
            "image_path": self._resolve_template_image_src(source_image_path),
        }

    def _render_html(self, template_data):
        template = self.env.get_template("classic.html")
        css_path = self.template_dir / "classic.css"
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()

        template_data["css_content"] = css_content
        return template.render(**template_data)

    def _render_to_image(self, html_content, output_path):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 800, "height": 1200})
            page.set_content(html_content)
            page.wait_for_load_state("networkidle")
            page.screenshot(path=str(output_path), full_page=True)
            browser.close()

    def _save_metadata(self, species_data, card_id, image_path):
        metadata = {
            **species_data,
            "card_id": card_id,
            "image_path": str(image_path),
            "card_image_path": str(image_path),
            "generated_at": datetime.now().isoformat(),
        }

        chinese_name = species_data.get("chinese_name", "unknown")
        metadata_file = self.metadata_dir / f"{chinese_name}_{card_id}.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _update_index(self, species_data, card_id, image_path):
        index = self._load_index()
        updated = False

        for card in index:
            if card.get("card_id") == card_id:
                card.update(
                    {
                        "chinese_name": species_data.get("chinese_name", ""),
                        "latin_name": species_data.get("latin_name", ""),
                        "category": species_data.get("category", "plant"),
                        "image_path": str(image_path),
                        "generated_at": datetime.now().isoformat(),
                        "card_generated": True,
                    }
                )
                updated = True
                break

        if not updated:
            index.append(
                {
                    "card_id": card_id,
                    "chinese_name": species_data.get("chinese_name", ""),
                    "latin_name": species_data.get("latin_name", ""),
                    "category": species_data.get("category", "plant"),
                    "image_path": str(image_path),
                    "generated_at": datetime.now().isoformat(),
                    "card_generated": True,
                }
            )

        self._save_index(index)

    def generate_card(self, species_data):
        try:
            if not species_data.get("chinese_name"):
                return {"success": False, "error": "缺少必需字段: chinese_name"}
            if not species_data.get("latin_name"):
                return {"success": False, "error": "缺少必需字段: latin_name"}

            category = species_data.get("category", "plant")
            card_id = species_data.get("card_id")
            if card_id:
                existing_card = self._find_existing_card(card_id)
                if existing_card is None:
                    return {"success": False, "error": f"card_id not found: {card_id}"}
            else:
                card_id = self._get_next_card_id(category)

            template_data = self._load_template_data(species_data, card_id)
            html_content = self._render_html(template_data)

            chinese_name = species_data.get("chinese_name", "unknown")
            image_filename = f"{chinese_name}_{card_id}.png"
            image_path = self.images_dir / image_filename

            self._render_to_image(html_content, image_path)
            self._save_metadata(species_data, card_id, image_path)
            self._update_index(species_data, card_id, image_path)

            return {
                "success": True,
                "card_id": card_id,
                "image_path": str(image_path),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
