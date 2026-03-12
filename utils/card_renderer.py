import os
import json
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright


class CardRenderer:
    """物种图鉴卡片渲染引擎"""
    
    def __init__(self, template_dir="templates", output_dir="cards"):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.metadata_dir = self.output_dir / "metadata"
        self.index_file = self.output_dir / "index.json"
        
        # 初始化 Jinja2 环境
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        
        # 分类映射
        self.category_map = {
            "plant": {"prefix": "P", "icon": "🌿", "label": "植物界"},
            "animal": {"prefix": "A", "icon": "🦋", "label": "动物界"},
            "mineral": {"prefix": "M", "icon": "💎", "label": "矿物界"}
        }
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """创建必要的目录结构"""
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化索引文件
        if not self.index_file.exists():
            self.index_file.write_text("[]", encoding="utf-8")
    
    def _get_next_card_id(self, category):
        """生成下一个卡片编号"""
        prefix = self.category_map[category]["prefix"]
        
        # 读取现有索引
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                index = json.load(f)
        except:
            index = []
        
        # 找到该分类的最大编号
        max_num = 0
        for card in index:
            card_id = card.get("card_id", "")
            if card_id.startswith(prefix):
                try:
                    num = int(card_id[1:])
                    max_num = max(max_num, num)
                except:
                    pass
        
        # 返回下一个编号
        return f"{prefix}{max_num + 1:03d}"
    
    def _load_template_data(self, species_data, card_id):
        """准备模板数据"""
        category = species_data.get("category", "plant")
        category_info = self.category_map.get(category, self.category_map["plant"])
        
        template_data = {
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
            "image_path": species_data.get("image_path", None)
        }
        
        return template_data
    
    def _render_html(self, template_data):
        """渲染 HTML"""
        template = self.env.get_template("classic.html")
        
        # 读取 CSS 文件
        css_path = self.template_dir / "classic.css"
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        
        # 将 CSS 添加到模板数据
        template_data["css_content"] = css_content
        
        html_content = template.render(**template_data)
        return html_content
    
    def _render_to_image(self, html_content, output_path):
        """使用 Playwright 将 HTML 渲染为图片"""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 800, "height": 1200})
            
            # 加载 HTML 内容
            page.set_content(html_content)
            
            # 等待渲染完成
            page.wait_for_load_state("networkidle")
            
            # 截图
            page.screenshot(path=str(output_path), full_page=True)
            
            browser.close()
    
    def _save_metadata(self, species_data, card_id, image_path):
        """保存卡片元数据"""
        metadata = {
            **species_data,
            "card_id": card_id,
            "image_path": str(image_path),
            "generated_at": datetime.now().isoformat()
        }
        
        chinese_name = species_data.get("chinese_name", "unknown")
        metadata_file = self.metadata_dir / f"{chinese_name}_{card_id}.json"
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _update_index(self, species_data, card_id, image_path):
        """更新总索引"""
        # 读取现有索引
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                index = json.load(f)
        except:
            index = []
        
        # 添加新记录
        index.append({
            "card_id": card_id,
            "chinese_name": species_data.get("chinese_name", ""),
            "latin_name": species_data.get("latin_name", ""),
            "category": species_data.get("category", "plant"),
            "image_path": str(image_path),
            "generated_at": datetime.now().isoformat()
        })
        
        # 保存索引
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def generate_card(self, species_data):
        """生成物种图鉴卡片
        
        Args:
            species_data: 物种数据字典
            
        Returns:
            dict: 包含 success, card_id, image_path 的结果
        """
        try:
            # 验证必需字段
            if not species_data.get("chinese_name"):
                return {"success": False, "error": "缺少必需字段: chinese_name"}
            if not species_data.get("latin_name"):
                return {"success": False, "error": "缺少必需字段: latin_name"}
            
            # 生成卡片编号
            category = species_data.get("category", "plant")
            card_id = self._get_next_card_id(category)
            
            # 准备模板数据
            template_data = self._load_template_data(species_data, card_id)
            
            # 渲染 HTML
            html_content = self._render_html(template_data)
            
            # 生成图片文件名
            chinese_name = species_data.get("chinese_name", "unknown")
            image_filename = f"{chinese_name}_{card_id}.png"
            image_path = self.images_dir / image_filename
            
            # 渲染为图片
            self._render_to_image(html_content, image_path)
            
            # 保存元数据
            self._save_metadata(species_data, card_id, image_path)
            
            # 更新索引
            self._update_index(species_data, card_id, image_path)
            
            return {
                "success": True,
                "card_id": card_id,
                "image_path": str(image_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
