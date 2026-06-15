"""
双源数据合并模块
- 贝壳 + 安居客数据融合
- 按小区名模糊匹配
- 异常数据标记
"""

import logging
from typing import List, Dict, Optional
from difflib import SequenceMatcher

import pandas as pd

import config

logger = logging.getLogger(__name__)


def _similarity(a: str, b: str) -> float:
    """计算两个字符串的相似度（0~1）"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _match_communities(sales: List[Dict], rentals: List[Dict],
                       threshold: float = 0.8) -> List[Dict]:
    """
    将二手房数据与租金数据按小区名匹配
    - threshold: 相似度阈值，≥此值视为同一小区
    """
    matched = []
    used_rentals = set()

    for s in sales:
        s_name = s.get("community", "")
        if not s_name:
            continue

        best_match = None
        best_score = 0.0

        for i, r in enumerate(rentals):
            if i in used_rentals:
                continue
            r_name = r.get("community", "")
            score = _similarity(s_name, r_name)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = (i, r)

        if best_match:
            i, r = best_match
            used_rentals.add(i)
            matched.append({**s, **r, "_match_score": best_score})
        else:
            # 仅有二手房数据，无租金匹配
            matched.append(s)

    # 加入未匹配的租金数据
    for i, r in enumerate(rentals):
        if i not in used_rentals:
            matched.append(r)

    return matched


def merge(city_name: str, ke_data: Dict[str, List[Dict]],
          anjuke_data: Dict[str, List[Dict]],
          ref_area_sqm: float = None) -> pd.DataFrame:
    """
    双源数据合并主函数

    参数:
        city_name: 城市名
        ke_data: 贝壳数据 {"sales": [...], "rentals": [...]}
        anjuke_data: 安居客数据 {"sales": [...], "rentals": [...]}
        ref_area_sqm: 参考面积（默认使用 config.REFERENCE_AREA_SQM）

    返回:
        DataFrame，字段见 docstring
    """
    if ref_area_sqm is None:
        ref_area_sqm = config.REFERENCE_AREA_SQM

    records = []

    # ---------- 贝壳：二手+租金匹配 ----------
    ke_matched = _match_communities(
        ke_data.get("sales", []),
        ke_data.get("rentals", []),
    )

    # ---------- 安居客：二手+租金匹配 ----------
    anjuke_matched = _match_communities(
        anjuke_data.get("sales", []),
        anjuke_data.get("rentals", []),
    )

    # ---------- 构建双源索引 ----------
    ke_index = {}
    for item in ke_matched:
        name = item.get("community", "")
        if name:
            key = name.lower().strip()
            ke_index[key] = item

    anjuke_index = {}
    for item in anjuke_matched:
        name = item.get("community", "")
        if name:
            key = name.lower().strip()
            anjuke_index[key] = item

    # ---------- 合并 ----------
    all_keys = set(ke_index.keys()) | set(anjuke_index.keys())

    for key in all_keys:
        ke_item = ke_index.get(key, {})
        aj_item = anjuke_index.get(key, {})

        community = ke_item.get("community") or aj_item.get("community") or key

        # 均价/总价
        ke_price = ke_item.get("total_price_wan")
        aj_price = aj_item.get("total_price_wan")
        ke_rent = ke_item.get("monthly_rent")
        aj_rent = aj_item.get("monthly_rent")
        ke_area = ke_item.get("area_sqm") or ref_area_sqm
        aj_area = aj_item.get("area_sqm") or ref_area_sqm

        # 计算均价（万元/㎡）= 总价 / 面积
        ke_avg_price = ke_price / ke_area if ke_price and ke_area else None
        aj_avg_price = aj_price / aj_area if aj_price and aj_area else None

        # 综合均价
        if ke_avg_price and aj_avg_price:
            composite_price = (ke_avg_price + aj_avg_price) / 2
            source = "双源验证"
        elif ke_avg_price:
            composite_price = ke_avg_price
            source = "仅贝壳"
        elif aj_avg_price:
            composite_price = aj_avg_price
            source = "仅安居客"
        else:
            composite_price = None
            source = "无有效数据"

        # 综合月租金
        rents = [v for v in (ke_rent, aj_rent) if v is not None]
        composite_rent = sum(rents) / len(rents) if rents else None

        # 数据质量
        quality = "正常"
        if ke_avg_price and aj_avg_price:
            diff = abs(ke_avg_price - aj_avg_price) / max(ke_avg_price, aj_avg_price)
            if diff > 0.20:
                quality = "数据异常"
        elif source == "无有效数据":
            quality = "无效"

        records.append({
            "城市": city_name,
            "小区名": community,
            "区域": ke_item.get("district") or aj_item.get("district", ""),
            "建筑年代": ke_item.get("build_year") or aj_item.get("build_year"),
            "均价_贝壳(元/㎡)": round(ke_avg_price * 10000) if ke_avg_price else None,
            "均价_安居客(元/㎡)": round(aj_avg_price * 10000) if aj_avg_price else None,
            "均价_综合(元/㎡)": round(composite_price * 10000) if composite_price else None,
            "月租金_贝壳(元)": int(ke_rent) if ke_rent else None,
            "月租金_安居客(元)": int(aj_rent) if aj_rent else None,
            "月租金_综合(元)": round(composite_rent) if composite_rent else None,
            "参考面积(㎡)": ref_area_sqm,
            "数据来源": source,
            "数据质量": quality,
        })

    df = pd.DataFrame(records)
    logger.info(f"[{city_name}] 合并结果: {len(df)} 条记录")
    return df
