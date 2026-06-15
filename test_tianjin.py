#!/usr/bin/env python3
"""
天津单城市测试 - 纯 LLM 训练数据抽取
三维分析：租售比 × 市场情绪 × 人口流入
"""

import sys
sys.path.insert(0, ".")

from dataclasses import dataclass, field
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


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


# ==================== 天津训练数据 ====================

tianjin_sentiment = MarketSentiment(
    city="天津",
    price_trend_12m="declining_moderate",
    price_change_est_pct=-8,
    price_vs_peak_pct=-30,
    peak_year=2017,
    volume_trend="shrinking",
    policy_stance="loosening_aggressive",
    key_policies=["全面取消限购", "首付降至15%", "房贷利率下调", "海河英才落户政策"],
    rental_market="weakening",
    rental_note="核心区（和平/南开）租金受高校和医疗资源支撑相对稳定；"
               "远郊及滨海新区租金持续承压，空置率上升。"
               "北京通勤族支撑武清等个别区域，但整体需求偏弱。",
    inventory_pressure="high",
    months_to_clear=24,
    sentiment_phase="bear_market",
    sentiment_score=75,
    bearish_factors=[
        "距2017年高点已跌30%，长期阴跌挫伤信心",
        "人口增长乏力，高校毕业生大量流向北京",
        "滨海新区大规模开发后供应严重过剩",
        "传统制造业转型缓慢，新兴产业不足",
        "年轻人吸引力弱于北京杭州成都"
    ],
    bullish_factors=[
        "距最高点已跌30%，泡沫挤出充分，安全边际足够",
        "京津双城记：北京人口溢出+高铁通勤（30分钟）",
        "天大/南开双一流高校，核心区学生租赁刚需",
        "医疗资源全国前列（肿瘤/血液/心血管），吸引就医人群",
        "价格已接近2015年水平，继续下行空间有限",
    ],
    risk_level="medium",
    entry_signal="cautious",
    entry_advice="仅关注核心区（和平/南开/河西）高租售比+高校周边标的；"
                 "坚决回避滨海新区、远郊和新区概念板块。"
                 "天津是'跌出来的机会'，但必须精选地段确保租金抗跌。"
)

tianjin_population = Population(
    city="天津",
    population_trend="moderate_inflow",
    net_migration_annual_wan=1.5,
    population_growth_3y_pct=0.4,
    total_population_wan=1363,
    working_age_pct=64,
    student_population_wan=58,
    key_industries=["装备制造", "石油化工", "港口物流", "航空航天", "生物医药"],
    industry_quality="medium",
    income_to_price_ratio="expensive",
    demographic_health="fair",
    population_risk="medium",
    migration_sources=["河北", "东北三省", "山东"],
    youth_attractiveness="medium",
    population_note="天津人口增长乏力，实际流入质量偏低。"
                    "天大/南开毕业生留存率约30%，大量外流至北京。"
                    "海河英才计划有一定效果但未扭转趋势。"
                    "核心区高教+医疗资源是核心区租赁需求的主要支撑。"
)

tianjin_candidates = [
    Candidate(
        community="王顶堤片区", district="南开区",
        reason="天大/南大周边，双一流高校学生租赁刚需，核心区地段",
        avg_price_per_sqm=11000, monthly_rent=2000,
        property_type="老旧小区", build_year_range="1985-2000",
        key_drivers=["天大/南大周边", "双一流高校", "学生租赁刚需", "地铁3/6号线"],
        confidence=0.80,
        notes="王顶堤是南开传统居住区，天大南大留学生+考研族租赁需求稳定"
    ),
    Candidate(
        community="大直沽片区", district="河东区",
        reason="老城区地铁沿线，老旧小区价格低，通勤天津站便利",
        avg_price_per_sqm=9600, monthly_rent=1700,
        property_type="老旧小区", build_year_range="1985-2000",
        key_drivers=["老城区地铁", "天津站通勤", "价格低", "生活便利"],
        confidence=0.75,
        notes="大直沽是河东成熟居住区，价格亲民，适合在津工作人群"
    ),
    Candidate(
        community="小白楼片区", district="和平区",
        reason="市中心CBD核心，白领+商务租赁需求，和平区教育资源加持",
        avg_price_per_sqm=13000, monthly_rent=2400,
        property_type="老小区+次新混搭", build_year_range="1990-2010",
        key_drivers=["市中心CBD", "和平区核心", "商务白领", "教育资源"],
        confidence=0.75,
        notes="小白楼-五大道区域是天津传统核心区，租客质量较高"
    ),
    Candidate(
        community="西北角片区", district="红桥区",
        reason="老城厢旧改区，价格在核心区中极低，地铁便利",
        avg_price_per_sqm=9000, monthly_rent=1650,
        property_type="老旧小区", build_year_range="1980-2000",
        key_drivers=["核心区价格洼地", "老城厢改造", "地铁1号线"],
        confidence=0.70,
        notes="西北角是红桥核心，价格在城区中最低，适合低价策略"
    ),
    Candidate(
        community="鞍山西道片区", district="南开区",
        reason="天大北面科贸街，IT从业者+学生双重需求",
        avg_price_per_sqm=10500, monthly_rent=1900,
        property_type="老小区", build_year_range="1990-2005",
        key_drivers=["天大周边", "科贸街产业", "IT人群租赁"],
        confidence=0.70,
        notes="鞍山西道是天津IT产业集中区，配套天大南大人才输出"
    ),
    Candidate(
        community="下瓦房片区", district="河西区",
        reason="河西成熟社区，配套完善，白领+家庭租赁需求",
        avg_price_per_sqm=12000, monthly_rent=2100,
        property_type="老小区+次新", build_year_range="1995-2010",
        key_drivers=["河西成熟社区", "配套完善", "白领租赁"],
        confidence=0.70,
        notes="下瓦房地处河西腹地，周边商业教育医疗配套齐全"
    ),
    Candidate(
        community="狮子林大街片区", district="河北区",
        reason="老城区+意式风情区周边，旅游+商务租赁需求，价格适中",
        avg_price_per_sqm=9500, monthly_rent=1700,
        property_type="老小区", build_year_range="1985-2000",
        key_drivers=["老城区", "意式风情区", "旅游商务", "跨河通勤"],
        confidence=0.65,
        notes="狮子林大街是河北区门户地段，海河沿岸景观，租赁有一定溢价"
    ),
]


# ==================== 分析引擎 ====================

def compute_rental_resilience(c: Candidate) -> float:
    score = 0.5
    drivers = " ".join(c.key_drivers)
    if "大学" in drivers or "天大" in drivers or "南开" in drivers or "高校" in drivers:
        score += 0.2
    if "地铁" in drivers:
        score += 0.1
    if "商圈" in drivers or "商业" in drivers or "CBD" in drivers:
        score += 0.1
    if "核心" in drivers or "市中心" in drivers:
        score += 0.1
    return min(score, 1.0)


def composite_score(c: Candidate, sentiment, pop) -> dict:
    quality = (
        0.35 * c.confidence +
        0.30 * compute_rental_resilience(c) +
        0.20 * 0.7 +
        0.15 * 0.7
    )
    sent_map = {"panic": 0.60, "bear_market": 0.75, "bottoming": 0.85,
                "early_recovery": 1.00, "bull_market": 0.80}
    sent_factor = sent_map.get(sentiment.sentiment_phase, 0.85)

    pop_map = {"strong_inflow": 1.20, "moderate_inflow": 1.05,
               "stable": 1.00, "outflow": 0.55}
    pop_factor = pop_map.get(pop.population_trend, 1.0)

    if pop.population_trend in ("strong_inflow", "moderate_inflow") and \
       sentiment.sentiment_phase in ("panic", "bear_market"):
        pop_factor += 0.10

    if abs(sentiment.price_vs_peak_pct) >= 20:
        pop_factor += 0.05

    composite = round(c.annual_yield_pct * quality * sent_factor * pop_factor, 2)

    if c.annual_yield_pct >= 5.0 and c.confidence >= 0.7:
        tier = "TIER 1 🔥"
    elif c.annual_yield_pct >= 4.5 and c.confidence >= 0.6:
        tier = "TIER 2 ⭐"
    elif c.annual_yield_pct >= 4.0 and c.confidence >= 0.5:
        tier = "TIER 3"
    else:
        tier = "TIER 4"

    if pop.population_trend in ("strong_inflow", "moderate_inflow") and \
       sentiment.sentiment_phase in ("bear_market", "bottoming"):
        advice = "🐻📈 左侧布局：情绪错杀+超跌"
    elif sentiment.sentiment_phase == "bear_market":
        advice = "⏳ 等待企稳信号"
    elif sentiment.sentiment_phase == "bottoming":
        advice = "磨底阶段，可入场"
    else:
        advice = "中性观望"

    return {
        "tier": tier, "composite_score": composite,
        "quality": round(quality, 2), "sentiment_factor": sent_factor,
        "population_factor": round(pop_factor, 2),
        "rental_resilience": round(compute_rental_resilience(c), 2),
        "advice": advice,
    }


def print_report(candidates, sentiment, population):
    console.print()
    console.print(Panel.fit("[bold cyan]🏠 房产租售比挖掘系统 v2[/bold cyan]\n[dim]数据来源: LLM 训练数据（无爬虫）[/dim]", border_style="cyan"))
    console.print("\n[bold]📍 天津 · 城市基本面[/bold]\n")

    pt = Table(title="👥 人口流入", box=box.SIMPLE)
    pt.add_column("指标", style="cyan"); pt.add_column("数据", style="white")
    pt.add_row("流入趋势", f"[bold yellow]{_pop_label(population.population_trend)}[/bold yellow]（年净流入 {population.net_migration_annual_wan} 万）")
    pt.add_row("常住人口", f"{population.total_population_wan} 万")
    pt.add_row("高校在校生", f"{population.student_population_wan} 万")
    pt.add_row("主导产业", "、".join(population.key_industries))
    pt.add_row("产业质量", f"[bold yellow]{population.industry_quality}[/bold yellow]")
    pt.add_row("房价收入比", population.income_to_price_ratio)
    pt.add_row("人口风险", f"[bold yellow]{population.population_risk}[/bold yellow]")
    pt.add_row("备注", population.population_note)
    console.print(pt)

    st = Table(title="📉 市场情绪", box=box.SIMPLE)
    st.add_column("指标", style="cyan"); st.add_column("数据", style="white")
    st.add_row("情绪阶段", f"[bold red]{_phase_label(sentiment.sentiment_phase)}[/bold red]（悲观 {sentiment.sentiment_score}/100）")
    st.add_row("12月价格趋势", f"{sentiment.price_trend_12m}（约 {sentiment.price_change_est_pct:+.0f}%）")
    st.add_row("距历史高点", f"[bold red]{_drawdown_label(abs(sentiment.price_vs_peak_pct))}[/bold red]（{sentiment.peak_year}年见顶）")
    st.add_row("成交量", sentiment.volume_trend)
    st.add_row("租赁市场", f"[bold yellow]{sentiment.rental_market}[/bold yellow] — {sentiment.rental_note}")
    st.add_row("库存压力", f"{sentiment.inventory_pressure}（去化约 {sentiment.months_to_clear} 个月）")
    st.add_row("政策方向", f"{sentiment.policy_stance}：{'、'.join(sentiment.key_policies)}")
    st.add_row("综合风险", f"[bold yellow]{sentiment.risk_level}[/bold yellow]")
    st.add_row("入场信号", f"[bold yellow]{sentiment.entry_signal}[/bold yellow]")
    st.add_row("建议", sentiment.entry_advice)
    console.print(st)

    console.print(f"\n🟢 利多: {'; '.join(sentiment.bullish_factors)}")
    console.print(f"🔴 利空: {'; '.join(sentiment.bearish_factors)}")
    console.print("\n[bold]🏆 天津核心区候选小区（三维评分）[/bold]\n")

    results = [(c, composite_score(c, sentiment, population)) for c in candidates]
    results.sort(key=lambda x: x[1]["composite_score"], reverse=True)

    table = Table(title="Top 候选", box=box.SIMPLE_HEAVY, width=100)
    table.add_column("#", style="dim", width=3); table.add_column("小区", style="bold white", width=14)
    table.add_column("区", style="cyan", width=8); table.add_column("租售比", justify="right", style="bold yellow", width=8)
    table.add_column("月租", justify="right", width=7); table.add_column("总价", justify="right", width=6)
    table.add_column("韧性", justify="right", width=5); table.add_column("情绪×人口", justify="right", width=12)
    table.add_column("综合", justify="right", style="bold green", width=6); table.add_column("评级", width=8)

    for rank, (c, s) in enumerate(results, 1):
        ys = "[bold green]" if c.annual_yield_pct >= 4.5 else ""; ye = "[/bold green]" if ys else ""
        table.add_row(str(rank), c.community, c.district, f"{ys}{c.annual_yield_pct}%{ye}",
                      f"¥{c.monthly_rent:,}", f"{c.total_price_wan:.0f}",
                      f"{s['rental_resilience']:.2f}", f"{s['sentiment_factor']:.2f}×{s['population_factor']:.2f}",
                      f"{s['composite_score']:.2f}", s['tier'])
    console.print(table)

    t1 = len([r for r in results if "TIER 1" in r[1]["tier"]])
    t2 = len([r for r in results if "TIER 2" in r[1]["tier"]])
    console.print(f"\n[bold]📊 总结:[/bold] {len(results)} 个候选 | [bold green]TIER 1: {t1}[/bold green] | [bold yellow]TIER 2: {t2}[/bold yellow]")
    console.print(f"[dim]所有数据来源于 LLM 训练知识库，未接入实时爬虫。[/dim]\n")
    return results


def _pop_label(t):
    return {"strong_inflow": "强流入", "moderate_inflow": "温和流入", "stable": "稳定", "outflow": "净流出"}.get(t, t)
def _phase_label(p):
    return {"panic": "恐慌", "bear_market": "下跌市", "bottoming": "磨底", "early_recovery": "复苏", "bull_market": "牛市"}.get(p, p)
def _drawdown_label(d):
    if d >= 40: return f"↓{d:.0f}% ⛔崩盘"
    if d >= 30: return f"↓{d:.0f}% 🔴超跌"
    if d >= 20: return f"↓{d:.0f}% 🟠深调"
    if d >= 10: return f"↓{d:.0f}% 🟡温和"
    return f"↓{d:.0f}% 🟢轻调"


if __name__ == "__main__":
    results = print_report(tianjin_candidates, tianjin_sentiment, tianjin_population)
    from report_generator import generate_report
    fp = generate_report("天津", results, tianjin_sentiment, tianjin_population)
    console.print(f"[green]✅ 报告已生成: {fp}[/green]")
