from fastmcp import FastMCP
import sys
import logging
import json
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger('SpeciesEncyclopedia')

# 修复 Windows 控制台 UTF-8 编码
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

# 创建 MCP 服务
mcp = FastMCP("SpeciesEncyclopedia")

# 数据文件路径
PROJECT_ROOT = Path(__file__).parent.parent
CARDS_DIR = PROJECT_ROOT / "cards"
INDEX_FILE = CARDS_DIR / "index.json"
METADATA_DIR = CARDS_DIR / "metadata"
SCORES_FILE = CARDS_DIR / "user_scores.json"

# 积分规则
POINTS_BY_RARITY = {
    1: 10,
    2: 10,
    3: 20,
    4: 30,
    5: 50
}


def load_index():
    """加载图鉴索引"""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_index(index_data):
    """保存图鉴索引"""
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)


def load_scores():
    """加载用户积分"""
    if SCORES_FILE.exists():
        with open(SCORES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_scores(scores_data):
    """保存用户积分"""
    SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCORES_FILE, 'w', encoding='utf-8') as f:
        json.dump(scores_data, f, ensure_ascii=False, indent=2)


def load_metadata_by_card_id(card_id: str) -> dict | None:
    """按 card_id 加载物种完整详情"""
    if not METADATA_DIR.exists():
        return None

    for metadata_file in METADATA_DIR.glob(f"*_{card_id}.json"):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("读取物种详情失败 %s: %s", metadata_file, exc)
    return None


def generate_card_id(category, existing_ids):
    """生成新的卡片ID"""
    prefix_map = {"plant": "P", "animal": "A", "mineral": "M"}
    prefix = prefix_map.get(category, "P")

    # 找出该分类下最大的编号
    max_num = 0
    for card in existing_ids:
        if card["card_id"].startswith(prefix):
            num = int(card["card_id"][1:])
            max_num = max(max_num, num)

    return f"{prefix}{max_num + 1:03d}"


@mcp.tool()
def register_species(
        chinese_name: str,
        latin_name: str,
        features: list[str],
        category: str = "plant",
        habitat: str = "",
        observation_season: str = "",
        protection_level: str = "",
        fun_fact: str = "",
        rarity: int = 3,
        user_id: str = "default"
) -> dict:
    """智能注册物种到图鉴

    自动检查物种是否已存在：
    - 如果是新物种：添加到图鉴并奖励积分
    - 如果已存在：返回已有信息，不奖励积分

    Parameters:
    - chinese_name: 物种中文名（必需）
    - latin_name: 物种学名（必需）
    - features: 识别特征列表（必需）
    - category: 分类（plant/animal/mineral，默认 plant）
    - habitat: 分布地区（可选）
    - observation_season: 最佳观察期（可选）
    - protection_level: 保护等级（可选）
    - fun_fact: 趣味知识（可选）
    - rarity: 稀有度 1-5 星（默认 3）
    - user_id: 用户ID（默认 "default"）

    Returns:
    - is_new: 是否为新物种
    - card_id: 卡片编号
    - points_earned: 本次获得积分
    - total_score: 用户总积分
    - discoveries: 用户发现总数
    - message: 提示信息
    """
    try:
        # 加载现有图鉴
        index = load_index()

        # 检查物种是否已存在（按中文名或学名）
        existing = None
        for card in index:
            if card["chinese_name"] == chinese_name or card["latin_name"] == latin_name:
                existing = card
                break

        # 如果已存在
        if existing:
            scores = load_scores()
            user_score = scores.get(user_id, {"total_score": 0, "discoveries": 0})

            return {
                "is_new": False,
                "card_id": existing["card_id"],
                "points_earned": 0,
                "total_score": user_score["total_score"],
                "discoveries": user_score["discoveries"],
                "message": f"这是已知物种：{chinese_name} ({existing['card_id']})"
            }

        # 验证必需字段
        if not chinese_name or not latin_name or not features:
            return {
                "is_new": False,
                "error": "缺少必需字段：chinese_name, latin_name, features"
            }

        # 验证分类和稀有度
        if category not in ["plant", "animal", "mineral"]:
            return {"is_new": False, "error": f"无效的分类: {category}"}
        if not (1 <= rarity <= 5):
            return {"is_new": False, "error": f"无效的稀有度: {rarity}"}

        # 生成新卡片ID并在index中占位
        card_id = generate_card_id(category, index)

        # 在index中占位（防止重复注册）
        index.append({
            "card_id": card_id,
            "chinese_name": chinese_name,
            "latin_name": latin_name,
            "category": category,
            "generated_at": datetime.now().isoformat(),
            "discovered_by": user_id,
            "card_generated": False  # 标记卡片尚未生成
        })
        save_index(index)

        # 计算积分
        points = POINTS_BY_RARITY.get(rarity, 20)

        # 更新用户积分
        scores = load_scores()
        if user_id not in scores:
            scores[user_id] = {
                "total_score": 0,
                "discoveries": 0,
                "last_discovery_at": None
            }

        scores[user_id]["total_score"] += points
        scores[user_id]["discoveries"] += 1
        scores[user_id]["last_discovery_at"] = datetime.now().isoformat()
        save_scores(scores)

        logger.info(f"新物种待注册: {chinese_name} ({card_id}), 用户 {user_id} 将获得 {points} 分")

        return {
            "is_new": True,
            "card_id": card_id,
            "points_earned": points,
            "total_score": scores[user_id]["total_score"],
            "discoveries": scores[user_id]["discoveries"],
            "message": f"🎉 发现新物种：{chinese_name}！请调用 generate_species_card() 生成卡片，卡片ID为 {card_id}"
        }

    except Exception as e:
        logger.error(f"注册物种时发生错误: {e}")
        return {"is_new": False, "error": str(e)}


@mcp.tool()
def search_species(keyword: str, limit: int = 10) -> dict:
    """搜索图鉴中的物种

    支持按中文名、学名、分类搜索

    Parameters:
    - keyword: 搜索关键词
    - limit: 返回结果数量限制（默认10）

    Returns:
    - count: 匹配数量
    - results: 物种列表
    """
    try:
        index = load_index()
        keyword_lower = keyword.lower()

        results = []
        for card in index:
            # 搜索中文名、学名、分类
            if (keyword in card["chinese_name"] or
                    keyword_lower in card["latin_name"].lower() or
                    keyword_lower in card["category"]):
                results.append({
                    "card_id": card["card_id"],
                    "chinese_name": card["chinese_name"],
                    "latin_name": card["latin_name"],
                    "category": card["category"],
                    "generated_at": card.get("generated_at", ""),
                    "image_path": card.get("image_path", ""),
                    "card_generated": card.get("card_generated", False),
                    "discovered_by": card.get("discovered_by", "")
                })

                if len(results) >= limit:
                    break

        return {
            "count": len(results),
            "results": results,
            "message": f"找到 {len(results)} 个匹配的物种"
        }

    except Exception as e:
        logger.error(f"搜索物种时发生错误: {e}")
        return {"count": 0, "results": [], "error": str(e)}


@mcp.tool()
def get_species_detail(card_id: str) -> dict:
    """根据 card_id 获取物种详情"""
    try:
        if not card_id:
            return {"error": "缺少必需字段：card_id"}

        detail = load_metadata_by_card_id(card_id)
        if detail:
            return detail

        index = load_index()
        for card in index:
            if card.get("card_id") == card_id:
                return card

        return {"error": f"未找到物种详情: {card_id}"}
    except Exception as e:
        logger.error(f"获取物种详情时发生错误: {e}")
        return {"error": str(e)}


@mcp.tool()
def get_my_stats(user_id: str = "default") -> dict:
    """查询我的图鉴统计

    Parameters:
    - user_id: 用户ID（默认 "default"）

    Returns:
    - total_score: 总积分
    - discoveries: 发现物种数量
    - last_discovery_at: 最近发现时间
    - total_species: 图鉴总物种数
    """
    try:
        scores = load_scores()
        index = load_index()

        user_data = scores.get(user_id, {
            "total_score": 0,
            "discoveries": 0,
            "last_discovery_at": None
        })

        return {
            "user_id": user_id,
            "total_score": user_data["total_score"],
            "discoveries": user_data["discoveries"],
            "last_discovery_at": user_data.get("last_discovery_at"),
            "total_species": len(index),
            "message": f"你已发现 {user_data['discoveries']} 个物种，获得 {user_data['total_score']} 积分"
        }

    except Exception as e:
        logger.error(f"查询统计时发生错误: {e}")
        return {"error": str(e)}


# 启动服务
if __name__ == "__main__":
    mcp.run(transport="stdio")
