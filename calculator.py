"""
租售比计算模块
- 年租售比 = 月租金 × 12 / (均价 × 参考面积) × 100%
- 按阈值过滤
"""

import logging
from typing import Optional, Tuple

import pandas as pd

import config

logger = logging.getLogger(__name__)


def calc_yield_ratio(monthly_rent: Optional[float],
                     avg_price_per_sqm: Optional[float],
                     area_sqm: Optional[float] = None) -> Optional[float]:
    """
    计算年租售比（百分比）

    参数:
        monthly_rent: 月租金（元）
        avg_price_per_sqm: 均价（元/㎡）
        area_sqm: 面积（㎡），默认使用 config.REFERENCE_AREA_SQM

    返回:
        年租售比百分比，如 4.5 表示 4.5%
    """
    if area_sqm is None:
        area_sqm = config.REFERENCE_AREA_SQM

    if not monthly_rent or not avg_price_per_sqm or monthly_rent <= 0 or avg_price_per_sqm <= 0:
        return None

    annual_rent = monthly_rent * 12
    total_price = avg_price_per_sqm * area_sqm
    return round(annual_rent / total_price * 100, 2)


def calculate(df: pd.DataFrame,
              threshold: Optional[float] = None,
              max_total_price_wan: Optional[float] = None) -> pd.DataFrame:
    """
    在 DataFrame 上计算租售比，增加字段:
        - 总价估算(万元): 均价 × 参考面积 / 10000
        - 年租售比(%): 使用综合月租金和综合均价
        - 是否达标: 租售比 ≥ threshold

    参数:
        df: merger 输出的 DataFrame
        threshold: 最低租售比阈值，默认 config.YIELD_THRESHOLD
        max_total_price_wan: 总价上限（万元），可选
    """
    if threshold is None:
        threshold = config.YIELD_THRESHOLD
    if max_total_price_wan is None:
        max_total_price_wan = config.MAX_TOTAL_PRICE_WAN

    df = df.copy()

    # 计算总价估算（万元）
    df["总价估算(万元)"] = df.apply(
        lambda row: round(row["均价_综合(元/㎡)"] * row["参考面积(㎡)"] / 10000, 2)
        if pd.notna(row["均价_综合(元/㎡)"]) else None,
        axis=1,
    )

    # 计算年租售比
    df["年租售比(%)"] = df.apply(
        lambda row: calc_yield_ratio(
            row.get("月租金_综合(元)"),
            row.get("均价_综合(元/㎡)"),
            row.get("参考面积(㎡)"),
        ),
        axis=1,
    )

    # 达标判断
    df["是否达标"] = df["年租售比(%)"].apply(
        lambda x: x >= threshold if pd.notna(x) else False
    )

    # 总价过滤（可选）
    if max_total_price_wan:
        before = len(df)
        df = df[
            df["总价估算(万元)"].isna() |
            (df["总价估算(万元)"] <= max_total_price_wan)
        ]
        logger.info(f"总价过滤 (≤{max_total_price_wan}万): {before} → {len(df)} 条")

    return df


def get_qualified(df: pd.DataFrame) -> pd.DataFrame:
    """返回达标的记录，按租售比降序"""
    return df[df["是否达标"]].sort_values("年租售比(%)", ascending=False)


def get_summary_stats(df: pd.DataFrame) -> Tuple[int, int, float, float, float]:
    """
    返回汇总统计:
        (总数, 达标数, 达标率%, 平均租售比%, 最高租售比%)
    """
    total = len(df)
    qualified = df["是否达标"].sum()
    avg_yield = df["年租售比(%)"].dropna().mean() if total > 0 else 0
    max_yield = df["年租售比(%)"].dropna().max() if total > 0 else 0
    rate = (qualified / total * 100) if total > 0 else 0
    return total, int(qualified), round(rate, 2), round(avg_yield, 2), round(max_yield, 2)
