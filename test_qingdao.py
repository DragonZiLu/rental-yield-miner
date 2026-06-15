#!/usr/bin/env python3
"""
青岛单城市测试 - 纯 LLM 训练数据抽取（不启动爬虫）
三维分析：租售比 × 市场情绪 × 人口流入
"""

import sys
sys.path.insert(0, ".")

from dataclasses import dataclass, field
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# ==================== 青岛训练数据 ====================

@dataclass
class MarketSentiment:
    city: str
    price_trend_12m: str
    price_change_est_pct: float
    price_vs_peak_pct: float
    peak_year: int
    volume_trend: str
    policy_stance: str
    key_policies: list
    rental_market: str
    rental_note: str
    inventory_pressure: str
    months_to_clear: int
    sentiment_phase: str
    sentiment_score: int
    bearish_factors: list
    bullish_factors: list
    risk_level: str
    entry_signal: str
    entry_advice: str

@dataclass
class Population:
    city: str
    population_trend: str
    net_migration_annual_wan: float
    population_growth_3y_pct: float
    total_population_wan: float
    working_age_pct: float
    student_population_wan: float
    key_industries: list
    industry_quality: str
    income_to_price_ratio: str
    demographic_health: str
    population_risk: str
    migration_sources: list
    youth_attractiveness: str
    population_note: str

@dataclass
class Candidate:
    community: str
    district: str
    reason: str
    avg_price_per_sqm: int
    ref_area_sqm: int = 50
    total_price_wan: float = 0
    monthly_rent: int = 0
    annual_yield_pct: float = 0.0
    property_type: str = ""
    build_year_range: str = ""
    key_drivers: list = field(default_factory=list)
    confidence: float = 0.5
    notes: str = ""

    def __post_init__(self):
        self.total_price_wan = self.avg_price_per_sqm * self.ref_area_sqm / 10000
        self.annual_yield_pct = round(self.monthly_rent * 12 / (self.total_price_wan * 10000) * 100, 2)


# ------ 青岛市场情绪（基于训练数据） ------
qingdao_sentiment = MarketSentiment(
    city="青岛",
    price_trend_12m="declining_moderate",
    price_change_est_pct=-10,
    price_vs_peak_pct=-25,
    peak_year=2018,
    volume_trend="shrinking",
    policy_stance="loosening_moderate",
    key_policies=["取消限购", "降低首付比例", "房贷利率下调"],
    rental_market="stable",
    rental_note="核心区（市南市北）租金韧性较强，旅游短租支撑；远郊租金承压",
    inventory_pressure="high",
    months_to_clear=22,
    sentiment_phase="bear_market",
    sentiment_score=72,
    bearish_factors=[
        "二手房挂牌量持续高位，去化周期超20个月",
        "人口流入放缓，省内向济南分流",
        "经济结构偏传统，新兴产业不足",
        "上合峰会透支后回调"
    ],
    bullish_factors=[
        "市南市北核心区价格已从2018年高点回调25%，泡沫挤出较多",
        "海滨城市稀缺性长期存在",
        "地铁网络扩展提升通勤便利度",
        "旅游旺季短租市场支撑租金底线",
        "政策全面放松，下行空间有限"
    ],
    risk_level="medium",
    entry_signal="cautious",
    entry_advice="核心区（市南、市北）高租售比小区可分批建仓；回避西海岸、城阳等远郊新区"
)

# ------ 青岛人口数据（基于训练数据） ------
qingdao_population = Population(
    city="青岛",
    population_trend="moderate_inflow",
    net_migration_annual_wan=4.5,
    population_growth_3y_pct=1.2,
    total_population_wan=1034,
    working_age_pct=65,
    student_population_wan=45,
    key_industries=["海洋经济", "家电制造", "港口物流", "旅游会展", "轨道交通装备"],
    industry_quality="medium",
    income_to_price_ratio="expensive",
    demographic_health="fair",
    population_risk="medium",
    migration_sources=["省内鲁西南", "东北三省"],
    youth_attractiveness="medium",
    population_note="青岛人口仍在流入但增速放缓，高校毕业生留存率偏低，产业结构偏传统导致高薪岗位不足"
)

# ------ 青岛候选小区（核心区） ------
qingdao_candidates = [
    Candidate(
        community="麦岛片区", district="市南区",
        reason="海大浮山校区周边，学生+旅游短租双重需求，市南核心地段",
        avg_price_per_sqm=14000, monthly_rent=2600,
        property_type="老小区+次新混搭", build_year_range="1998-2010",
        key_drivers=["大学周边", "海滨地段", "旅游短租需求", "地铁2号线"],
        confidence=0.75,
        notes="麦岛是青岛传统高端居住延伸区，小户型租赁活跃"
    ),
    Candidate(
        community="台东商圈", district="市北区",
        reason="老城区核心商圈，商业繁华，小户型密集，地铁直达",
        avg_price_per_sqm=11000, monthly_rent=2000,
        property_type="老旧小区", build_year_range="1990-2005",
        key_drivers=["核心商圈", "地铁1/2号线", "小户型多", "配套成熟"],
        confidence=0.80,
        notes="台东是青岛老牌商业中心，租客以服务业从业者和年轻白领为主"
    ),
    Candidate(
        community="市北老城区", district="市北区",
        reason="老旧小区集中，价格从2018年高点大幅回调，租客稳定",
        avg_price_per_sqm=10400, monthly_rent=1900,
        property_type="老旧小区", build_year_range="1985-2000",
        key_drivers=["价格深度回调", "老城区配套", "租客稳定", "地铁覆盖"],
        confidence=0.70,
        notes="市北老区价格已回吐较多，租售比进入合理区间"
    ),
    Candidate(
        community="李村商圈", district="李沧区",
        reason="李沧核心商圈+地铁枢纽，配套成熟生活便利",
        avg_price_per_sqm=11600, monthly_rent=2100,
        property_type="次新+老小区", build_year_range="2000-2015",
        key_drivers=["地铁枢纽", "商圈中心", "配套成熟"],
        confidence=0.70,
        notes="李村是青岛北部商业中心，地铁2/3号线交汇"
    ),
    Candidate(
        community="大学路片区", district="市南区",
        reason="海大鱼山校区+老城区核心，历史街区+学生租赁",
        avg_price_per_sqm=15000, monthly_rent=2500,
        property_type="历史街区老房", build_year_range="1930-1990",
        key_drivers=["大学核心区", "历史街区", "市南黄金地段"],
        confidence=0.65,
        notes="大学路周边老洋房和小户型，租金受旅游短租溢价支撑"
    ),
    Candidate(
        community="错埠岭片区", district="市北区",
        reason="市北大型居住区，地铁便利，价格在核心区中偏低",
        avg_price_per_sqm=10000, monthly_rent=1800,
        property_type="老小区", build_year_range="1990-2000",
        key_drivers=["价格洼地", "地铁覆盖", "大型社区配套"],
        confidence=0.65,
        notes="错埠岭片区价格亲民，适合刚需租赁"
    ),
]

# ==================== 分析引擎 ====================

def compute_rental_resilience(c: Candidate) -> float:
    """租金韧性评分 0~1"""
    score = 0.5
    drivers = " ".join(c.key_drivers)
    if "大学" in drivers:
        score += 0.2
    if "地铁" in drivers:
        score += 0.1
    if "商圈" in drivers or "商业" in drivers:
        score += 0.1
    if "老城区" in drivers or "核心" in drivers:
        score += 0.1
    return min(score, 1.0)


def composite_score(c: Candidate, sentiment: MarketSentiment, pop: Population) -> dict:
    """三维综合评分"""
    # 质量系数
    quality = (
        0.35 * c.confidence +
        0.30 * compute_rental_resilience(c) +
        0.20 * 0.7 +  # market_position default
        0.15 * 0.7    # location_score default
    )

    # 情绪系数
    sentiment_map = {
        "panic": 0.60, "bear_market": 0.75, "bottoming": 0.85,
        "early_recovery": 1.00, "bull_market": 0.80,
    }
    sent_factor = sentiment_map.get(sentiment.sentiment_phase, 0.85)

    # 人口系数
    pop_map = {
        "strong_inflow": 1.20, "moderate_inflow": 1.05,
        "stable": 1.00, "outflow": 0.55,
    }
    pop_factor = pop_map.get(pop.population_trend, 1.0)

    # 黄金坑加分：人口流入 + 市场悲观
    if pop.population_trend in ("strong_inflow", "moderate_inflow") and \
       sentiment.sentiment_phase in ("panic", "bear_market"):
        pop_factor += 0.10

    # 超跌加分：距高点跌幅 > 20%
    if abs(sentiment.price_vs_peak_pct) >= 20:
        pop_factor += 0.05

    composite = round(c.annual_yield_pct * quality * sent_factor * pop_factor, 2)

    # TIER 分类
    if c.annual_yield_pct >= 5.0 and c.confidence >= 0.7 and pop.population_trend != "outflow":
        tier = "TIER 1 🔥"
    elif c.annual_yield_pct >= 4.5 and c.confidence >= 0.6 and pop.population_trend != "outflow":
        tier = "TIER 2 ⭐"
    elif c.annual_yield_pct >= 4.0 and c.confidence >= 0.5:
        tier = "TIER 3"
    else:
        tier = "TIER 4"

    # 投资建议
    if pop.population_trend in ("strong_inflow", "moderate_inflow") and sentiment.sentiment_phase in ("bear_market", "bottoming"):
        advice = "🐻📈 左侧布局：基本面好+情绪错杀，可分批建仓"
    elif sentiment.sentiment_phase == "bear_market":
        advice = "⏳ 等待企稳信号，关注成交量回暖"
    elif sentiment.sentiment_phase == "bottoming":
        advice = "✅ 磨底阶段，核心区高租售比可入场"
    elif sentiment.sentiment_phase in ("early_recovery", "bull_market"):
        advice = "⚠️ 注意追高风险，租售比可能被涨价压缩"
    else:
        advice = "📊 中性观望"

    return {
        "tier": tier,
        "composite_score": composite,
        "quality": round(quality, 2),
        "sentiment_factor": sent_factor,
        "population_factor": round(pop_factor, 2),
        "rental_resilience": round(compute_rental_resilience(c), 2),
        "advice": advice,
    }


# ==================== 报告输出 ====================

def print_report(candidates, sentiment, population):
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🏠 房产租售比挖掘系统 v2[/bold cyan]\n"
        "[dim]数据来源: LLM 训练数据（无爬虫）[/dim]",
        border_style="cyan",
    ))

    # --- 城市基本面 ---
    console.print()
    console.print("[bold]📍 青岛 · 城市基本面[/bold]")
    console.print()

    # 人口
    pop_table = Table(title="👥 人口流入", box=box.SIMPLE)
    pop_table.add_column("指标", style="cyan")
    pop_table.add_column("数据", style="white")
    pop_table.add_row("流入趋势", f"{population.population_trend}（年净流入 {population.net_migration_annual_wan} 万）")
    pop_table.add_row("常住人口", f"{population.total_population_wan} 万（近3年增速 {population.population_growth_3y_pct}%）")
    pop_table.add_row("高校在校生", f"{population.student_population_wan} 万")
    pop_table.add_row("主导产业", "、".join(population.key_industries))
    pop_table.add_row("产业质量", population.industry_quality)
    pop_table.add_row("人口结构", population.demographic_health)
    pop_table.add_row("人口风险", population.population_risk)
    pop_table.add_row("备注", population.population_note)
    console.print(pop_table)

    # 市场情绪
    sent_table = Table(title="📉 市场情绪", box=box.SIMPLE)
    sent_table.add_column("指标", style="cyan")
    sent_table.add_column("数据", style="white")
    sent_table.add_row("12月价格趋势", f"{sentiment.price_trend_12m}（约 {sentiment.price_change_est_pct:+.0f}%）")
    sent_table.add_row("距历史高点", f"↓{abs(sentiment.price_vs_peak_pct):.0f}%（{sentiment.peak_year}年见顶）")
    sent_table.add_row("成交量", sentiment.volume_trend)
    sent_table.add_row("租赁市场", f"{sentiment.rental_market} — {sentiment.rental_note}")
    sent_table.add_row("库存压力", f"{sentiment.inventory_pressure}（去化约 {sentiment.months_to_clear} 个月）")
    sent_table.add_row("情绪阶段", f"[bold yellow]{sentiment.sentiment_phase}[/bold yellow]（悲观指数 {sentiment.sentiment_score}/100）")
    sent_table.add_row("政策方向", f"{sentiment.policy_stance}：{'、'.join(sentiment.key_policies)}")
    sent_table.add_row("综合风险", f"[bold {'red' if sentiment.risk_level == 'high' else 'yellow'}]{sentiment.risk_level}[/bold {'red' if sentiment.risk_level == 'high' else 'yellow'}]")
    sent_table.add_row("入场建议", f"[bold]{sentiment.entry_signal}[/bold] — {sentiment.entry_advice}")
    console.print(sent_table)

    # 利多/利空
    console.print()
    console.print(f"🟢 利多: {'; '.join(sentiment.bullish_factors)}")
    console.print(f"🔴 利空: {'; '.join(sentiment.bearish_factors)}")

    # --- 候选排名 ---
    console.print()
    console.print("[bold]🏆 青岛核心区候选小区（三维评分）[/bold]")
    console.print()

    # 计算评分并排序
    results = []
    for c in candidates:
        scores = composite_score(c, sentiment, population)
        results.append((c, scores))
    results.sort(key=lambda x: x[1]["composite_score"], reverse=True)

    table = Table(title="Top 候选", box=box.SIMPLE_HEAVY, width=100)
    table.add_column("#", style="dim", width=3)
    table.add_column("小区", style="bold white", width=12)
    table.add_column("区", style="cyan", width=8)
    table.add_column("租售比", justify="right", style="bold yellow", width=8)
    table.add_column("月租", justify="right", width=7)
    table.add_column("总价", justify="right", width=6)
    table.add_column("韧性", justify="right", width=5)
    table.add_column("情绪×人口", justify="right", width=12)
    table.add_column("综合", justify="right", style="bold green", width=6)
    table.add_column("评级", width=8)
    table.add_column("建议", style="dim", max_width=28, no_wrap=False)

    for rank, (c, s) in enumerate(results, 1):
        yield_style = "[bold green]" if c.annual_yield_pct >= 4.5 else ""
        yield_end = "[/bold green]" if yield_style else ""
        table.add_row(
            str(rank),
            c.community,
            c.district,
            f"{yield_style}{c.annual_yield_pct}%{yield_end}",
            f"¥{c.monthly_rent:,}",
            f"{c.total_price_wan:.0f}",
            f"{s['rental_resilience']:.2f}",
            f"{s['sentiment_factor']:.2f}×{s['population_factor']:.2f}",
            f"{s['composite_score']:.2f}",
            s['tier'],
            s['advice'][:30],
        )

    console.print(table)

    # --- 总结 ---
    tier1 = [r for r in results if "TIER 1" in r[1]["tier"]]
    tier2 = [r for r in results if "TIER 2" in r[1]["tier"]]
    console.print()
    console.print(f"[bold]📊 总结:[/bold] {len(results)} 个候选 | "
                  f"[bold green]TIER 1: {len(tier1)}[/bold green] | "
                  f"[bold yellow]TIER 2: {len(tier2)}[/bold yellow]")
    console.print(f"[dim]注: 所有数据来源于 LLM 训练知识库，未接入实时爬虫。建议通过爬虫验证 Top 候选。[/dim]")
    console.print()


if __name__ == "__main__":
    print_report(qingdao_candidates, qingdao_sentiment, qingdao_population)
