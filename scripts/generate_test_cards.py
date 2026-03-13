#!/usr/bin/env python
"""
End-to-end test script for species registration and card generation.

Usage:
    python scripts/generate_test_cards.py
    python scripts/generate_test_cards.py --count 5 --user-id qa_user
    python scripts/generate_test_cards.py --clean --count 3
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_servers.species_card_generator import generate_species_card
from mcp_servers.species_encyclopedia_mcp import get_my_stats, register_species


CARDS_DIR = PROJECT_ROOT / "cards"
INDEX_FILE = CARDS_DIR / "index.json"
SCORES_FILE = CARDS_DIR / "user_scores.json"
IMAGES_DIR = CARDS_DIR / "images"
METADATA_DIR = CARDS_DIR / "metadata"


BASE_SPECIES = [
    {
        "chinese_name": "银杏",
        "latin_name": "Ginkgo biloba",
        "features": ["扇形叶片", "秋季金黄", "种子有特殊气味"],
        "category": "plant",
        "habitat": "城市公园、山区",
        "observation_season": "秋季",
        "protection_level": "国家二级保护植物",
        "fun_fact": "银杏是古老孑遗植物，被称为活化石",
        "rarity": 4,
    },
    {
        "chinese_name": "红腹锦鸡",
        "latin_name": "Chrysolophus pictus",
        "features": ["羽色鲜艳", "尾羽较长", "雄鸟头部金黄"],
        "category": "animal",
        "habitat": "山地林区",
        "observation_season": "春季",
        "protection_level": "国家二级保护动物",
        "fun_fact": "雄鸟在求偶时会展开颈羽",
        "rarity": 5,
    },
    {
        "chinese_name": "萤石",
        "latin_name": "Fluorite",
        "features": ["常见紫绿条带", "硬度较低", "部分样品具荧光"],
        "category": "mineral",
        "habitat": "热液矿脉",
        "observation_season": "全年",
        "protection_level": "",
        "fun_fact": "萤石在紫外光下常出现明显荧光",
        "rarity": 3,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test species registration + card generation flow")
    parser.add_argument("--count", type=int, default=3, help="How many test species to process (default: 3)")
    parser.add_argument("--user-id", default="default", help="User id used for score and discovery stats")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for stable rarity/name generation")
    parser.add_argument("--clean", action="store_true", help="Remove existing cards directory before test")
    return parser.parse_args()


def bootstrap_storage(clean: bool) -> None:
    if clean and CARDS_DIR.exists():
        shutil.rmtree(CARDS_DIR)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    if not INDEX_FILE.exists():
        INDEX_FILE.write_text("[]", encoding="utf-8")
    if not SCORES_FILE.exists():
        SCORES_FILE.write_text("{}", encoding="utf-8")


def load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def build_species_payloads(count: int, seed: int) -> list[dict[str, Any]]:
    random.seed(seed)
    payloads: list[dict[str, Any]] = []

    for idx in range(count):
        base = BASE_SPECIES[idx % len(BASE_SPECIES)].copy()
        serial = idx + 1
        base["chinese_name"] = f"{base['chinese_name']}_S{seed}_T{serial:03d}"
        base["latin_name"] = f"{base['latin_name']} var.test{seed}.{serial:03d}"
        base["rarity"] = min(5, max(1, base["rarity"] + random.choice([-1, 0, 1])))
        payloads.append(base)

    return payloads


def verify_card_outputs(chinese_name: str, image_path: str) -> tuple[bool, str]:
    image_ok = bool(image_path) and Path(image_path).exists()
    metadata_candidates = list(METADATA_DIR.glob(f"{chinese_name}_*.json"))
    metadata_ok = len(metadata_candidates) > 0

    if image_ok and metadata_ok:
        return True, ""

    reasons = []
    if not image_ok:
        reasons.append("image file missing")
    if not metadata_ok:
        reasons.append("metadata file missing")
    return False, ", ".join(reasons)


def run_test_flow(payloads: list[dict[str, Any]], user_id: str) -> int:
    print(f"[INFO] Start test flow for user_id={user_id}, species_count={len(payloads)}")

    success = 0
    failed = 0

    for i, payload in enumerate(payloads, start=1):
        print(f"\n[STEP {i}] Register: {payload['chinese_name']}")
        register_result = register_species(user_id=user_id, **payload)
        if register_result.get("error"):
            failed += 1
            print(f"[FAIL] register_species error: {register_result['error']}")
            continue

        if not register_result.get("is_new"):
            failed += 1
            print(f"[FAIL] expected new species but got: {register_result}")
            continue

        print(
            "[OK] register_species -> "
            f"card_id={register_result.get('card_id')} "
            f"points={register_result.get('points_earned')} "
            f"total_score={register_result.get('total_score')}"
        )

        generate_result = generate_species_card(card_id=register_result.get("card_id"), **payload)
        if generate_result.get("error") or not generate_result.get("success"):
            failed += 1
            print(f"[FAIL] generate_species_card failed: {generate_result}")
            continue

        if generate_result.get("card_id") != register_result.get("card_id"):
            failed += 1
            print(
                "[FAIL] generated card_id does not match reserved card_id: "
                f"register={register_result.get('card_id')} generate={generate_result.get('card_id')}"
            )
            continue

        image_path = generate_result.get("image_path", "")
        valid, reason = verify_card_outputs(payload["chinese_name"], image_path)
        if not valid:
            failed += 1
            print(f"[FAIL] output verify failed: {reason}; result={generate_result}")
            continue

        success += 1
        print(f"[OK] generate_species_card -> card_id={generate_result.get('card_id')} image={image_path}")

    print("\n[STEP DUPLICATE] Register first species again to confirm no duplicate points")
    duplicate_result = register_species(user_id=user_id, **payloads[0])
    if duplicate_result.get("error"):
        failed += 1
        print(f"[FAIL] duplicate register error: {duplicate_result['error']}")
    elif duplicate_result.get("is_new") is True or duplicate_result.get("points_earned") != 0:
        failed += 1
        print(f"[FAIL] duplicate rule check failed: {duplicate_result}")
    else:
        print(
            "[OK] duplicate register -> "
            f"is_new={duplicate_result.get('is_new')} "
            f"points={duplicate_result.get('points_earned')}"
        )

    stats = get_my_stats(user_id=user_id)
    index_data = load_json(INDEX_FILE, [])
    scores_data = load_json(SCORES_FILE, {})
    print("\n[SUMMARY]")
    print(f"success={success}, failed={failed}")
    print(
        f"user_stats: discoveries={stats.get('discoveries')} "
        f"total_score={stats.get('total_score')} total_species={stats.get('total_species')}"
    )
    print(
        f"storage: index_entries={len(index_data)} "
        f"user_score_exists={user_id in scores_data} "
        f"images={len(list(IMAGES_DIR.glob('*.png')))} "
        f"metadata={len(list(METADATA_DIR.glob('*.json')))}"
    )
    if len(index_data) > len(payloads):
        print(
            "[WARN] index entries are more than input species. "
            "Current workflow may create extra placeholder records."
        )

    return 0 if failed == 0 else 1


def main() -> int:
    args = parse_args()
    if args.count <= 0:
        print("[ERROR] --count must be > 0")
        return 2

    bootstrap_storage(clean=args.clean)
    payloads = build_species_payloads(args.count, args.seed)
    return run_test_flow(payloads, args.user_id)


if __name__ == "__main__":
    raise SystemExit(main())
