#!/usr/bin/env python3
"""
成都单城市测试 - 纯 LLM 训练数据抽取（不启动爬虫）
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

# ==================== 成都训练数据 ====================

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


# ------ 成都市场情绪（基于训练数据）------
chengdu_sentiment = MarketSentiment(
    city="成都",
    price_trend_12m="declining_moderate",
    price_change_est_pct=-8,
    price_vs_peak_pct=-18,
    peak_year=2021,
    volume_trend="shrinking",
    policy_stance="loosening_aggressive",
    key_policies=["全面取消限购", "首付降至15%", "房贷利率3.0%", "购房落户政策放宽"],
    rental_market="stable",
    rental_note="核心区（锦江青羊武侯金牛成华）租金韧性极强，高校+服务业支撑；远郊承压",
    inventory_pressure="high",
    months_to_clear=20,
    sentiment_phase="bottoming",
    sentiment_score=70,
    bearish_factors=[
        "二手房挂牌量突破20万套，去化周期约20个月",
        "开发商暴雷潮后市场信心修复缓慢",
        "部分远郊新区价格虚高后回调",
        "居民收入预期偏弱"
    ],
    bullish_factors=[
        "全国最强人口流入城市之一，年净流入超12万",
        "核心区距2021年高点仅回调18%，相对温和",
        "产业结构持续升级（电子信息、生物医药、数字经济）",
        "成渝双城经济圈国家战略加持",
        "110万高校在校生提供稳定租赁需求",
        "政策底已明确，全面松绑"
    ],
    risk_level="medium",
    entry_signal="cautious",
    entry_advice="核心区（锦江、青羊、武侯、成华）高租售比小区可分批建仓；回避天府新区远郊板块"
)

# ------ 成都人口数据（基于训练数据）------
chengdu_population = Population(
    city="成都",
    population_trend="strong_inflow",
    net_migration_annual_wan=12.5,
    population_growth_3y_pct=3.8,
    total_population_wan=2140,
    working_age_pct=68,
    student_population_wan=110,
    key_industries=["电子信息", "生物医药", "数字经济", "航空航天", "文创旅游"],
    industry_quality="high",
    income_to_price_ratio="moderate",
    demographic_health="good",
    population_risk="low",
    migration_sources=["省内三四线", "西北省份", "西藏"],
    youth_attractiveness="high",
    population_note="成都连续多年净流入超10万，全国顶尖。高校毕业生留存率高，'蓉漂'成为现象级人口迁移。产业结构持续升级，是西部唯一具备完整高端产业生态的城市。"
)

# ------ 成都候选小区（核心区：锦江/青羊/武侯/金牛/成华）------
chengdu_candidates = [
    Candidate(
        community="太升南路片区", district="锦江区",
        reason="市中心老区核心，春熙路辐射，交通商业极致发达，小户型密集",
        avg_price_per_sqm=12400, monthly_rent=2300,
        property_type="老旧小区", build_year_range="1990-2005",
        key_drivers=["市中心核心", "地铁1/2/3号线", "春熙路商圈", "小户型多"],
        confidence=0.80,
        notes="太升南路是成都老牌电子通讯商圈，周边老小区价格亲民但租金坚挺"
    ),
    Candidate(
        community="玉林小区", district="武侯区",
        reason="成都老牌文艺社区，生活便利极度成熟，小户型密集租金稳定",
        avg_price_per_sqm=11000, monthly_rent=2000,
        property_type="老旧小区", build_year_range="1995-2005",
        key_drivers=["老城区核心", "小酒馆/文艺社区", "地铁1/8号线", "配套极致成熟"],
        confidence=0.80,
        notes="玉林是成都最具代表性的老牌居住区，《成都》唱火后租赁需求更旺"
    ),
    Candidate(
        community="建设路片区", district="成华区",
        reason="电子科大沙河校区周边，学生+IT从业者双重需求，美食商圈加持",
        avg_price_per_sqm=10000, monthly_rent=1800,
        property_type="老小区+职工宿舍", build_year_range="1980-2000",
        key_drivers=["电子科大周边", "IT产业辐射", "建设路美食商圈"],
        confidence=0.80,
        notes="建设路是成华区核心，电子科大是成都IT人才摇篮，周边租赁需求旺盛"
    ),
    Candidate(
        community="光华村片区", district="青羊区",
        reason="西南财大周边，学生+金融从业者租赁需求，二环内成熟配套",
        avg_price_per_sqm=10400, monthly_rent=1900,
        property_type="老旧小区", build_year_range="1995-2005",
        key_drivers=["西南财大周边", "二环内地段", "金融产业人群"],
        confidence=0.75,
        notes="光华村-金沙片区是西贵之地，财大+金融城双重租赁支撑"
    ),
    Candidate(
        community="抚琴小区", district="金牛区",
        reason="老城区老旧小区，城西核心地段，单价极低但配套一应俱全",
        avg_price_per_sqm=9000, monthly_rent=1600,
        property_type="老旧小区", build_year_range="1985-2000",
        key_drivers=["价格极低", "城西成熟配套", "地铁2号线", "生活便利"],
        confidence=0.80,
        notes="抚琴是成都'老破小'的代表，单价低但租金相对稳定，租售比有优势"
    ),
    Candidate(
        community="九眼桥片区", district="武侯区",
        reason="市中心+川大周边，酒吧街+高校双重租赁需求，地段稀缺",
        avg_price_per_sqm=11600, monthly_rent=2100,
        property_type="老旧小区+次新", build_year_range="1995-2010",
        key_drivers=["川大周边", "市中心地段", "九眼桥商圈", "地铁2号线"],
        confidence=0.75,
        notes="九眼桥是成都夜生活地标，川大留学生+年轻白领租赁需求集中"
    ),
    Candidate(
        community="万年场片区", district="成华区",
        reason="老小区+地铁枢纽，万象城商圈辐射，通勤教育双支撑",
        avg_price_per_sqm=9600, monthly_rent=1700,
        property_type="老旧小区", build_year_range="1990-2005",
        key_drivers=["万象城商圈", "地铁4号线", "老小区价格低"],
        confidence=0.75,
        notes="万年场地处东二环，地铁直达春熙路，是城东门户地段"
    ),
    Candidate(
        community="八里庄片区", district="成华区",
        reason="主城旧改区，二仙桥-八里庄城市更新核心区，价格低且租金稳定",
        avg_price_per_sqm=9200, monthly_rent=1650,
        property_type="老小区+改造中", build_year_range="1985-2000",
        key_drivers=["城市更新区", "主城低价", "地铁7号线"],
        confidence=0.70,
        notes="八里庄曾是工业区，现为成华重点旧改片区，价格处于洼地"
    ),
    Candidate(
        community="双楠片区", district="武侯区",
        reason="成熟社区配套，二环内+地铁覆盖，居住舒适度高租住需求稳定",
        avg_price_per_sqm=12000, monthly_rent=2200,
        property_type="次新+老小区混搭", build_year_range="2000-2010",
        key_drivers=["二环内地段", "成熟社区", "地铁3/7号线", "配套完善"],
        confidence=0.70,
        notes="双楠是成都早期高档居住区，品质较好，白领租赁需求集中"
    ),
    Candidate(
        community="火车南站片区", district="武侯区",
        reason="交通枢纽+高新区辐射，商务+通勤租赁需求强",
        avg_price_per_sqm=13000, monthly_rent=2300,
        property_type="次新+老小区", build_year_range="2000-2015",
        key_drivers=["交通枢纽", "高新区辐射", "地铁1/7号线", "商务人群"],
        confidence=0.70,
        notes="火车南站-桐梓林片区是成都城南门户，高新区外溢租赁需求直接受益"
    ),
]


# ==================== 分析引擎 ====================

def compute_rental_resilience(c: Candidate) -> float:
    score = 0.5
    drivers = " ".join(c.key_drivers)
    if "大学" in drivers:
        score += 0.2
    if "地铁" in drivers:
        score += 0.1
    if "商圈" in drivers or "商业" in drivers:
        score += 0.1
    if "老城区" in drivers or "核心" in drivers or "市中心" in drivers:
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
        advice = "🐻📈 左侧布局：基本面好+情绪错杀，可分批建仓"
    elif sentiment.sentiment_phase == "bottoming":
        advice = "磨底阶段，核心区高租售比可入场"
    elif sentiment.sentiment_phase == "bear_market":
        advice = "⏳ 等待企稳信号，关注成交量回暖"
    elif sentiment.sentiment_phase in ("early_recovery", "bull_market"):
        advice = "⚠️ 注意追高风险，租售比可能被涨价压缩"
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
    console.print("[bold]📍 成都 · 城市基本面[/bold]")
    console.print()

    pop_table = Table(title="👥 人口流入", box=box.SIMPLE)
    pop_table.add_column("指标", style="cyan")
    pop_table.add_column("数据", style="white")
    pop_table.add_row("流入趋势", f"[bold green]{_pop_label(population.population_trend)}[/bold green]（年净流入 {population.net_migration_annual_wan} 万）")
    pop_table.add_row("常住人口", f"{population.total_population_wan} 万（近3年增速 {population.population_growth_3y_pct}%）")
    pop_table.add_row("高校在校生", f"{population.student_population_wan} 万")
    pop_table.add_row("主导产业", "、".join(population.key_industries))
    pop_table.add_row("产业质量", f"[bold green]{population.industry_quality}[/bold green]")
    pop_table.add_row("房价收入比", population.income_to_price_ratio)
    pop_table.add_row("人口风险", population.population_risk)
    pop_table.add_row("备注", population.population_note)
    console.print(pop_table)

    sent_table = Table(title="📉 市场情绪", box=box.SIMPLE)
    sent_table.add_column("指标", style="cyan")
    sent_table.add_column("数据", style="white")
    sent_table.add_row("情绪阶段", f"[bold yellow]{_phase_label(sentiment.sentiment_phase)}[/bold yellow]（悲观 {sentiment.sentiment_score}/100）")
    sent_table.add_row("12月价格趋势", f"{sentiment.price_trend_12m}（约 {sentiment.price_change_est_pct:+.0f}%）")
    sent_table.add_row("距历史高点", f"[bold]{_drawdown_label(abs(sentiment.price_vs_peak_pct))}[/bold]（{sentiment.peak_year}年见顶）")
    sent_table.add_row("成交量", sentiment.volume_trend)
    sent_table.add_row("租赁市场", f"{sentiment.rental_market} — {sentiment.rental_note}")
    sent_table.add_row("库存压力", f"{sentiment.inventory_pressure}（去化约 {sentiment.months_to_clear} 个月）")
    sent_table.add_row("政策方向", f"{sentiment.policy_stance}：{'、'.join(sentiment.key_policies)}")
    sent_table.add_row("综合风险", f"[bold yellow]{sentiment.risk_level}[/bold yellow]")
    sent_table.add_row("入场信号", f"[bold]{sentiment.entry_signal}[/bold]")
    sent_table.add_row("建议", sentiment.entry_advice)
    console.print(sent_table)

    console.print()
    console.print(f"🟢 利多: {'; '.join(sentiment.bullish_factors)}")
    console.print(f"🔴 利空: {'; '.join(sentiment.bearish_factors)}")

    console.print()
    console.print("[bold]🏆 成都核心区候选小区（三维评分）[/bold]")
    console.print()

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
    console.print(f"[dim]所有数据来源于 LLM 训练知识库，未接入实时爬虫[/dim]")
    console.print()

    return results


def _pop_label(t):
    return {"strong_inflow": "强流入", "moderate_inflow": "温和流入", "stable": "稳定", "outflow": "净流出"}.get(t, t)

def _phase_label(p):
    return {"panic": "恐慌", "bear_market": "下跌市", "bottoming": "磨底", "early_recovery": "复苏", "bull_market": "牛市"}.get(p, p)

def _drawdown_label(d):
    if d >= 30: return f"↓{d:.0f}% 🔴超跌"
    if d >= 20: return f"↓{d:.0f}% 🟠深调"
    if d >= 10: return f"↓{d:.0f}% 🟡温和"
    return f"↓{d:.0f}%"


if __name__ == "__main__":
    results = print_report(chengdu_candidates, chengdu_sentiment, chengdu_population)

    from report_generator import generate_report
    filepath = generate_report("成都", results, chengdu_sentiment, chengdu_population)
    console.print(f"[green]✅ 报告已生成: {filepath}[/green]")
