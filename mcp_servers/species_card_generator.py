from fastmcp import FastMCP
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.card_renderer import CardRenderer

logger = logging.getLogger('SpeciesCardGenerator')

# 修复 Windows 控制台 UTF-8 编码
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

# 创建 MCP 服务
mcp = FastMCP("SpeciesCardGenerator")

# 初始化渲染器
renderer = CardRenderer()


@mcp.tool()
def generate_species_card(
        chinese_name: str,
        latin_name: str,
        features: list[str],
        category: str = "plant",
        classification: dict = None,
        habitat: str = "",
        observation_season: str = "",
        protection_level: str = "",
        fun_fact: str = "",
        image_path: str = None,
        rarity: int = 3,
        card_id: str = None
) -> dict:
    """生成物种图鉴卡片

    为识别的动植物生成精美的宝可梦风格图鉴卡片图片。

    Parameters:
    - chinese_name: 物种中文名（必需）
    - latin_name: 物种学名（必需）
    - features: 识别特征列表（必需）
    - category: 分类（plant/animal/mineral，默认 plant）
    - classification: 分类学信息字典（可选）
    - habitat: 分布地区（可选）
    - observation_season: 最佳观察期（可选）
    - protection_level: 保护等级（可选）
    - fun_fact: 趣味知识（可选）
    - image_path: 物种照片路径（可选）
    - rarity: 稀有度 1-5 星（默认 3）

    Returns:
    - success: 是否成功
    - card_id: 卡片编号（如 P001）
    - image_path: 生成的图片路径
    - error: 错误信息（如果失败）
    """
    try:
        # 验证必需字段
        if not chinese_name:
            return {"success": False, "error": "缺少必需字段: chinese_name"}
        if not latin_name:
            return {"success": False, "error": "缺少必需字段: latin_name"}
        if not features or len(features) == 0:
            return {"success": False, "error": "缺少必需字段: features"}

        # 验证分类
        if category not in ["plant", "animal", "mineral"]:
            return {"success": False, "error": f"无效的分类: {category}，必须是 plant/animal/mineral"}

        # 验证稀有度
        if not (1 <= rarity <= 5):
            return {"success": False, "error": f"无效的稀有度: {rarity}，必须是 1-5"}

        # 构建物种数据
        species_data = {
            "card_id": card_id,
            "chinese_name": chinese_name,
            "latin_name": latin_name,
            "features": features,
            "category": category,
            "classification": classification or {},
            "habitat": habitat,
            "observation_season": observation_season,
            "protection_level": protection_level,
            "fun_fact": fun_fact,
            "image_path": image_path,
            "rarity": rarity
        }

        # 生成卡片
        result = renderer.generate_card(species_data)

        if result["success"]:
            logger.info(f"成功生成卡片: {result['card_id']} - {chinese_name}")
        else:
            logger.error(f"生成卡片失败: {result.get('error', 'Unknown error')}")

        return result

    except Exception as e:
        logger.error(f"生成卡片时发生错误: {e}")
        return {"success": False, "error": str(e)}


# 启动服务
if __name__ == "__main__":
    mcp.run(transport="stdio")
