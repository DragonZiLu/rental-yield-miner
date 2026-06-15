"""
城市分析报告生成器
格式: 需求 → 成果（每城市一份 Markdown 报告）
"""

import os
from datetime import datetime
from typing import List, Dict, Any


def format_pct(v: float, signed: bool = False) -> str:
    if signed:
        return f"{v:+.1f}%"
    return f"{v:.1f}%"


def format_wan(v: float) -> str:
    if v >= 10000:
        return f"{v/10000:.1f}万"
    return f"{v:.0f}"


def _make_header(city: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""# {city} · 房产租售比分析报告

> 生成时间: {now} | 数据来源: LLM 训练知识库 | 范围: 核心城区

---

"""


def _make_demand_section(sentiment, population) -> str:
    """需求分析：为什么要关注这个城市"""

    lines = ["## 一、需求分析", ""]

    # --- 人口 ---
    lines.append("### 1. 人口基本面")
    lines.append("")
    lines.append(f"| 指标 | 数据 |")
    lines.append(f"|------|------|")
    lines.append(f"| 流入趋势 | **{_pop_label(population.population_trend)}**（年净流入 {population.net_migration_annual_wan} 万） |")
    lines.append(f"| 常住人口 | {population.total_population_wan} 万 |")
    lines.append(f"| 近3年增速 | {population.population_growth_3y_pct}% |")
    lines.append(f"| 高校在校生 | {population.student_population_wan} 万 |")
    lines.append(f"| 主导产业 | {'、'.join(population.key_industries)} |")
    lines.append(f"| 产业质量 | {population.industry_quality} |")
    lines.append(f"| 人口风险 | **{_risk_label(population.population_risk)}** |")
    lines.append(f"| 房价收入比 | {population.income_to_price_ratio} |")
    lines.append("")
    lines.append(f"> {population.population_note}")
    lines.append("")

    # --- 市场情绪 ---
    lines.append("### 2. 市场情绪与价格水位")
    lines.append("")
    lines.append(f"| 指标 | 数据 |")
    lines.append(f"|------|------|")
    lines.append(f"| 情绪阶段 | **{_phase_label(sentiment.sentiment_phase)}** |")
    lines.append(f"| 悲观指数 | {sentiment.sentiment_score}/100 |")
    lines.append(f"| 12月价格趋势 | {sentiment.price_trend_12m}（约 {format_pct(sentiment.price_change_est_pct, True)}） |")
    lines.append(f"| 距历史高点 | **↓{abs(sentiment.price_vs_peak_pct):.0f}%**（{sentiment.peak_year}年见顶）|")
    lines.append(f"| 成交量 | {sentiment.volume_trend} |")
    lines.append(f"| 租赁市场 | {sentiment.rental_market} |")
    lines.append(f"| 库存压力 | {sentiment.inventory_pressure}（去化约 {sentiment.months_to_clear} 个月）|")
    lines.append(f"| 政策方向 | {sentiment.policy_stance} |")
    lines.append(f"| 综合风险 | **{_risk_label(sentiment.risk_level)}** |")
    lines.append("")

    lines.append(f"- 🟢 **利多**: {'; '.join(sentiment.bullish_factors)}")
    lines.append(f"- 🔴 **利空**: {'; '.join(sentiment.bearish_factors)}")
    lines.append("")

    lines.append(f"### 3. 策略判断")
    lines.append("")
    lines.append(f"> **入场信号**: `{sentiment.entry_signal}`")
    lines.append(f"> {sentiment.entry_advice}")
    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def _make_results_section(candidates: List, tier1_count: int, tier2_count: int) -> str:
    """成果输出：候选排名"""

    lines = ["## 二、成果输出", ""]

    lines.append(f"**总计**: {len(candidates)} 个核心区候选 | TIER 1: {tier1_count} | TIER 2: {tier2_count}")
    lines.append("")

    lines.append("### 候选小区排名（三维综合评分）")
    lines.append("")
    lines.append("| # | 小区 | 区域 | 租售比 | 月租 | 总价(万) | 质量 | 情绪 | 人口 | 综合 | 评级 |")
    lines.append("|---|------|------|--------|------|----------|------|------|------|------|------|")

    for rank, (c, s) in enumerate(candidates, 1):
        lines.append(
            f"| {rank} | {c.community} | {c.district} | "
            f"{format_pct(c.annual_yield_pct)} | ¥{c.monthly_rent:,} | {c.total_price_wan:.0f} | "
            f"{s['quality']:.2f} | ×{s['sentiment_factor']:.2f} | ×{s['population_factor']:.2f} | "
            f"**{s['composite_score']:.2f}** | {s['tier']} |"
        )

    lines.append("")

    # 每个候选的详细说明
    lines.append("### 候选详情")
    lines.append("")
    for rank, (c, s) in enumerate(candidates, 1):
        lines.append(f"#### {rank}. {c.community}（{c.district}）")
        lines.append(f"- **租售比**: {format_pct(c.annual_yield_pct)} | **月租**: ¥{c.monthly_rent:,} | **参考总价**: {c.total_price_wan:.0f}万（{c.ref_area_sqm}㎡）")
        lines.append(f"- **物业类型**: {c.property_type} | **楼龄**: {c.build_year_range}")
        lines.append(f"- **驱动因素**: {'、'.join(c.key_drivers)}")
        lines.append(f"- **租金韧性**: {s['rental_resilience']:.2f}")
        lines.append(f"- **投资建议**: {s['advice']}")
        if c.notes:
            lines.append(f"- **备注**: {c.notes}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*本报告数据来源于 LLM 训练知识库，未经实时爬虫验证。建议对 TIER 1/2 候选进行贝壳/安居客精准确认。*")
    lines.append("")

    return "\n".join(lines)


def generate_report(
    city: str,
    candidates: List,
    sentiment,
    population,
    output_dir: str = "reports",
) -> str:
    """生成城市分析报告，保存到 reports/{city}.md"""
    os.makedirs(output_dir, exist_ok=True)

    tier1 = sum(1 for _, s in candidates if "TIER 1" in s['tier'])
    tier2 = sum(1 for _, s in candidates if "TIER 2" in s['tier'])

    report = (
        _make_header(city) +
        _make_demand_section(sentiment, population) +
        _make_results_section(candidates, tier1, tier2)
    )

    filepath = os.path.join(output_dir, f"{city}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    return filepath


# ==================== 标签辅助 ====================

def _pop_label(trend: str) -> str:
    labels = {
        "strong_inflow": "🟢 强流入",
        "moderate_inflow": "🟡 温和流入",
        "stable": "⚪ 稳定",
        "outflow": "🔴 净流出",
    }
    return labels.get(trend, trend)


def _phase_label(phase: str) -> str:
    labels = {
        "panic": "🔴 恐慌",
        "bear_market": "🟠 下跌市",
        "bottoming": "🟡 磨底",
        "early_recovery": "🟢 复苏",
        "bull_market": "🔥 牛市",
    }
    return labels.get(phase, phase)


def _risk_label(risk: str) -> str:
    labels = {
        "low": "🟢 低",
        "medium": "🟡 中",
        "high": "🔴 高",
        "extreme": "⛔ 极高",
    }
    return labels.get(risk, risk)
