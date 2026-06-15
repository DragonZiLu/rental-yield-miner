#!/usr/bin/env python3
"""
北京单城市测试 - 纯 LLM 训练数据抽取（不启动爬虫）
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


# ==================== 北京训练数据 ====================

# ------ 市场情绪 ------
beijing_sentiment = MarketSentiment(
    city="北京",
    price_trend_12m="declining_moderate",
    price_change_est_pct=-5,
    price_vs_peak_pct=-10,
    peak_year=2023,
    volume_trend="shrinking",
    policy_stance="loosening_moderate",
    key_policies=["部分区域放宽限购", "首付比例下调", "房贷利率下调", "通州双限政策松绑"],
    rental_market="stable",
    rental_note="北京租赁市场全国最刚性，高校+央企+互联网三大支柱支撑。核心区租金几乎不受周期影响。"
               "但人口管控政策（疏解非首都功能）对远郊租赁有压制。",
    inventory_pressure="medium",
    months_to_clear=15,
    sentiment_phase="bottoming",
    sentiment_score=55,
    bearish_factors=[
        "二手房挂牌量攀升至16万套，买方市场特征明显",
        "人口管控政策持续，疏解非首都功能影响外围区域",
        "互联网行业裁员潮压制部分区域租赁需求（海淀-西二旗）",
        "改善型需求因政策门槛高被抑制"
    ],
    bullish_factors=[
        "房价全国最抗跌，距2023年高点仅回调10%，价格韧性极强",
        "教育资源全国第一，学区需求永恒支撑核心区",
        "央企/部委/高校/三甲医院聚集，高收入租客群体稳定",
        "人口管控反而保障核心区密度不失控，供给受限",
        "地铁网络全国最密，通勤覆盖极广",
    ],
    risk_level="low",
    entry_signal="ok",
    entry_advice="北京是全国最安全的高租售比市场。核心区（东城/西城/朝阳/海淀）老小区可积极关注；"
                 "回避通州/大兴/房山等外围区域。注意高总价门槛（核心区50㎡通常150万起步）。"
)

# ------ 人口数据 ------
beijing_population = Population(
    city="北京",
    population_trend="stable",
    net_migration_annual_wan=1.5,
    population_growth_3y_pct=0.3,
    total_population_wan=2188,
    working_age_pct=72,
    student_population_wan=95,
    key_industries=["信息技术/互联网", "金融", "科研教育", "文化传媒", "央企总部经济"],
    industry_quality="high",
    income_to_price_ratio="severely_unaffordable",
    demographic_health="good",
    population_risk="low",
    migration_sources=["全国高学历人才", "河北/东北/山东"],
    youth_attractiveness="high",
    population_note="北京人口总量受严格管控，表面增速低，但人口质量全国最高。"
                    "高学历+高收入人群集中，租金支付能力极强。"
                    "核心区实际常住人口密度远超统计数，租赁需求刚性极强。"
)

# ------ 候选小区（核心区：东城/西城/朝阳/海淀/丰台/石景山）------
beijing_candidates = [
    Candidate(
        community="劲松片区", district="朝阳区",
        reason="东三环老社区，CBD 3公里辐射圈，白领租赁首选地之一",
        avg_price_per_sqm=36000, monthly_rent=6000,
        property_type="老旧小区", build_year_range="1985-2000",
        key_drivers=["CBD辐射", "东三环核心地段", "地铁10号线", "白领租赁密集"],
        confidence=0.80,
        notes="劲松是朝阳老牌居住区，CBD上班族租房首选，小户型月租6000+"
    ),
    Candidate(
        community="天通苑", district="朝阳区",
        reason="亚洲最大社区，小户型供应量大，地铁5号线通勤CBD便利",
        avg_price_per_sqm=32000, monthly_rent=5500,
        property_type="大型社区", build_year_range="2000-2010",
        key_drivers=["大型社区", "小户型多", "地铁5号线", "CBD通勤"],
        confidence=0.80,
        notes="天通苑以'睡城'著称，但便宜+地铁是核心竞争力，小户型租售比表现好"
    ),
    Candidate(
        community="回龙观", district="海淀区",
        reason="IT从业者集中居住区，西二旗/上地通勤便利，租赁需求极旺",
        avg_price_per_sqm=34000, monthly_rent=5800,
        property_type="大型社区+次新", build_year_range="2000-2015",
        key_drivers=["互联网产业辐射", "西二旗/上地通勤", "地铁13/8号线", "IT白领集聚"],
        confidence=0.80,
        notes="回龙观是北京互联网人最集中的居住区，租客质量高、租金支付力强"
    ),
    Candidate(
        community="方庄片区", district="丰台区",
        reason="南城大型成熟社区，配套完善，价格在南三环内相对友好",
        avg_price_per_sqm=31000, monthly_rent=5200,
        property_type="老社区+次新", build_year_range="1990-2005",
        key_drivers=["南三环地段", "成熟社区", "地铁5/14号线", "价格相对友好"],
        confidence=0.75,
        notes="方庄是北京最早的商品房大社区之一，配套极度成熟，生活便利"
    ),
    Candidate(
        community="学院路片区", district="海淀区",
        reason="北航/北邮/北师大等高校密集区，学生+青年教师租赁需求稳定",
        avg_price_per_sqm=40000, monthly_rent=6700,
        property_type="老小区+单位宿舍", build_year_range="1980-2000",
        key_drivers=["高校密集", "学院路核心", "地铁10/13号线", "学术人群租赁"],
        confidence=0.75,
        notes="学院路是北京高校最密集区域，租赁需求以高学历人群为主"
    ),
    Candidate(
        community="潘家园片区", district="朝阳区",
        reason="东三环老社区，价格在核心区中偏低，地铁便利",
        avg_price_per_sqm=33000, monthly_rent=5500,
        property_type="老旧小区", build_year_range="1985-2000",
        key_drivers=["东三环地段", "地铁10号线", "核心区价格洼地"],
        confidence=0.75,
        notes="潘家园古玩市场周边老小区，位置好但价格在朝阳区偏低"
    ),
    Candidate(
        community="和平里片区", district="东城区",
        reason="东城核心+北二环，部委央企聚集地，租客质量极高",
        avg_price_per_sqm=50000, monthly_rent=7500,
        property_type="老旧小区+央产房", build_year_range="1970-2000",
        key_drivers=["东城核心", "二环内", "部委央企", "教育资源"],
        confidence=0.70,
        notes="和平里是北京传统高尚居住区，租金虽高但租客极优质"
    ),
    Candidate(
        community="西罗园片区", district="丰台区",
        reason="南三环内大型社区，交通便利价格亲民",
        avg_price_per_sqm=28000, monthly_rent=4500,
        property_type="大型老社区", build_year_range="1990-2000",
        key_drivers=["南三环内", "价格亲民", "地铁4/8号线", "大型社区配套"],
        confidence=0.70,
        notes="西罗园是南城性价比之选，适合追求低总价的投资者"
    ),
    Candidate(
        community="鲁谷片区", district="石景山区",
        reason="西五环成熟居住区，价格在主城六区中最低，地铁1号线",
        avg_price_per_sqm=26000, monthly_rent=4200,
        property_type="老社区+次新", build_year_range="1995-2010",
        key_drivers=["主城价格最低", "西五环", "地铁1号线", "成熟配套"],
        confidence=0.65,
        notes="石景山是城六区房价最低区域，鲁谷配套成熟适合刚需租赁"
    ),
]


# ==================== 分析引擎 ====================

def compute_rental_resilience(c: Candidate) -> float:
    score = 0.5
    drivers = " ".join(c.key_drivers)
    if "大学" in drivers or "高校" in drivers:
        score += 0.2
    if "地铁" in drivers:
        score += 0.1
    if "商圈" in drivers or "商业" in drivers:
        score += 0.1
    if "核心" in drivers or "市中心" in drivers or "CBD" in drivers:
        score += 0.1
    if "央企" in drivers or "部委" in drivers:
        score += 0.1
    return min(score, 1.0)


def composite_score(c: Candidate, sentiment: MarketSentiment, pop: Population) -> dict:
    quality = (
        0.35 * c.confidence +
        0.30 * compute_rental_resilience(c) +
        0.20 * 0.7 +
        0.15 * 0.7
    )

    sentiment_map = {
        "panic": 0.60, "bear_market": 0.75, "bottoming": 0.85,
        "early_recovery": 1.00, "bull_market": 0.80,
    }
    sent_factor = sentiment_map.get(sentiment.sentiment_phase, 0.85)

    pop_map = {
        "strong_inflow": 1.20, "moderate_inflow": 1.05,
        "stable": 1.00, "outflow": 0.55,
    }
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
        advice = "🐻📈 左侧布局"
    elif sentiment.sentiment_phase == "bottoming":
        advice = "磨底阶段，可入场"
    elif sentiment.sentiment_phase == "bear_market":
        advice = "⏳ 等待企稳"
    else:
        advice = "中性观望"

    return {
        "tier": tier,
        "composite_score": composite,
        "quality": round(quality, 2),
        "sentiment_factor": sent_factor,
        "population_factor": round(pop_factor, 2),
        "rental_resilience": round(compute_rental_resilience(c), 2),
        "advice": advice,
    }


# ==================== 控制台报告 ====================

def print_report(candidates, sentiment, population):
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🏠 房产租售比挖掘系统 v2[/bold cyan]\n"
        "[dim]数据来源: LLM 训练数据（无爬虫）[/dim]",
        border_style="cyan",
    ))

    console.print()
    console.print("[bold]📍 北京 · 城市基本面[/bold]")
    console.print()

    pop_table = Table(title="👥 人口流入", box=box.SIMPLE)
    pop_table.add_column("指标", style="cyan")
    pop_table.add_column("数据", style="white")
    pop_table.add_row("流入趋势", f"[bold yellow]{_pop_label(population.population_trend)}[/bold yellow]（年净流入 {population.net_migration_annual_wan} 万）")
    pop_table.add_row("常住人口", f"{population.total_population_wan} 万")
    pop_table.add_row("高校在校生", f"{population.student_population_wan} 万")
    pop_table.add_row("主导产业", "、".join(population.key_industries))
    pop_table.add_row("产业质量", f"[bold green]{population.industry_quality}[/bold green]")
    pop_table.add_row("房价收入比", f"[bold red]{population.income_to_price_ratio}[/bold red]")
    pop_table.add_row("人口风险", f"[bold green]{population.population_risk}[/bold green]")
    pop_table.add_row("备注", population.population_note)
    console.print(pop_table)

    sent_table = Table(title="📉 市场情绪", box=box.SIMPLE)
    sent_table.add_column("指标", style="cyan")
    sent_table.add_column("数据", style="white")
    sent_table.add_row("情绪阶段", f"[bold yellow]{_phase_label(sentiment.sentiment_phase)}[/bold yellow]（悲观 {sentiment.sentiment_score}/100）")
    sent_table.add_row("12月价格趋势", f"{sentiment.price_trend_12m}（约 {sentiment.price_change_est_pct:+.0f}%）")
    sent_table.add_row("距历史高点", f"[bold green]{_drawdown_label(abs(sentiment.price_vs_peak_pct))}[/bold green]（{sentiment.peak_year}年见顶）")
    sent_table.add_row("成交量", sentiment.volume_trend)
    sent_table.add_row("租赁市场", f"[bold green]{sentiment.rental_market}[/bold green] — {sentiment.rental_note}")
    sent_table.add_row("库存压力", f"{sentiment.inventory_pressure}（去化约 {sentiment.months_to_clear} 个月）")
    sent_table.add_row("政策方向", f"{sentiment.policy_stance}：{'、'.join(sentiment.key_policies)}")
    sent_table.add_row("综合风险", f"[bold green]{sentiment.risk_level}[/bold green]")
    sent_table.add_row("入场信号", f"[bold green]{sentiment.entry_signal}[/bold green]")
    sent_table.add_row("建议", sentiment.entry_advice)
    console.print(sent_table)

    console.print()
    console.print(f"🟢 利多: {'; '.join(sentiment.bullish_factors)}")
    console.print(f"🔴 利空: {'; '.join(sentiment.bearish_factors)}")

    console.print()
    console.print("[bold]🏆 北京核心区候选小区（三维评分）[/bold]")
    console.print()

    results = [(c, composite_score(c, sentiment, population)) for c in candidates]
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
        )

    console.print(table)

    tier1 = len([r for r in results if "TIER 1" in r[1]["tier"]])
    tier2 = len([r for r in results if "TIER 2" in r[1]["tier"]])
    console.print()
    console.print(f"[bold]📊 总结:[/bold] {len(results)} 个候选 | "
                  f"[bold green]TIER 1: {tier1}[/bold green] | "
                  f"[bold yellow]TIER 2: {tier2}[/bold yellow]")
    console.print(f"[dim]所有数据来源于 LLM 训练知识库，未接入实时爬虫。[/dim]")
    console.print()
    return results


def _pop_label(t):
    return {"strong_inflow": "强流入", "moderate_inflow": "温和流入", "stable": "稳定（人口管控）", "outflow": "净流出"}.get(t, t)

def _phase_label(p):
    return {"panic": "恐慌", "bear_market": "下跌市", "bottoming": "磨底", "early_recovery": "复苏", "bull_market": "牛市"}.get(p, p)

def _drawdown_label(d):
    if d >= 30: return f"↓{d:.0f}% 🔴超跌"
    if d >= 20: return f"↓{d:.0f}% 🟠深调"
    if d >= 10: return f"↓{d:.0f}% 🟡温和"
    return f"↓{d:.0f}% 🟢轻调"


if __name__ == "__main__":
    results = print_report(beijing_candidates, beijing_sentiment, beijing_population)

    from report_generator import generate_report
    filepath = generate_report("北京", results, beijing_sentiment, beijing_population)
    console.print(f"[green]✅ 报告已生成: {filepath}[/green]")
