# 房产租售比挖掘系统 v2 规划

## 核心思路翻转

```
v1: 爬虫全量抓取 → 计算 → 过滤            ❌ 被 CAPTCHA 堵死
v2: LLM训练数据抽取 → 结构化 → 情绪调整    ✅ 无反爬 + 多维度风控
     └─ 可选爬虫验证（Top N 精准搜）
```

---

## 1. 系统架构

```
┌───────────────────────────────────────────────────────────────────┐
│                       系统入口 (main.py)                           │
│                                                                   │
│  ┌──────────────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │   LLM 数据抽取器      │─▶│  结构化引擎    │─▶│   报告输出    │  │
│  │   • 候选小区           │  │  • 标准化      │  │  • Excel     │  │
│  │   • 市场情绪 ⭐        │  │  • 三维评分 ⭐ │  │  • 控制台    │  │
│  │   • 人口流入 ⭐⭐      │  │  • TIER分级    │  └───────────────┘  │
│  └──────────────────────┘  └───────────────┘                      │
│              │                                                     │
│              ▼                                                     │
│  ┌──────────────────────────────────────────┐                     │
│  │          可选：爬虫验证 (Phase 1.5)        │                     │
│  │        Top N 候选精准搜索确认              │                     │
│  └──────────────────────────────────────────┘                     │
└───────────────────────────────────────────────────────────────────┘
```

---

## 2. Phase 1: LLM 训练数据抽取

### 2.1 每次运行三轮 LLM 提取

| 轮次 | 目的 | 输出 |
|------|------|------|
| **第一轮** | 城市人口流入分析 ⭐⭐ | 城市级 11 维人口指标 |
| **第二轮** | 市场情绪分析 ⭐ | 城市级 12 维情绪指标 |
| **第三轮** | 候选小区数据抽取 | 每个核心区 3-8 个结构化候选 |

### 2.2 候选小区抽取

**抽取维度：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `city` | str | 城市名 |
| `district` | str | 核心区 |
| `community` | str | 小区名/片区 |
| `avg_price_per_sqm` | int | 均价（元/㎡） |
| `ref_area_sqm` | int | 参考面积，默认 50 |
| `total_price_wan` | float | 50㎡参考总价(万) |
| `monthly_rent` | int | 参考月租金(元) |
| `annual_yield_pct` | float | 计算租售比(%) |
| `property_type` | str | 老旧小区/次新/公寓 |
| `build_year_range` | str | 楼龄范围 |
| `key_drivers` | list | 高租售比驱动因素 |
| `confidence` | float | 置信度 0~1 |
| `notes` | str | 补充说明 |

---

## 3. Phase 1b: 市场情绪提取 ⭐

### 3.1 为什么需要情绪维度

```
场景 A（真金白银）: 房价稳定 + 租金上涨 → 租售比 4.5%  → ✅ 安全边际
场景 B（价值陷阱）: 房价跌 20% + 租金持平 → 租售比 5.0% → ⚠️ 分母效应，需判断底部
场景 C（双杀风险）: 房价跌 + 租金跌  → 租售比 4.2%  → ❌ 回避
```

高租售比必须拆解为「租金收入」和「价格下跌」两个驱动因子。

### 3.2 城市级情绪指标体系

| 指标 | 类型 | 取值范围 | 说明 |
|------|------|----------|------|
| `price_trend_12m` | enum | `declining_steep`(-15%+) / `declining_moderate`(-5~15%) / `stable` / `rising` | 近12月房价趋势 |
| `price_change_est_pct` | float | -50 ~ +50 | 估算价格变动幅度(%) |
| `volume_trend` | enum | `freezing` / `shrinking` / `stable` / `recovering` / `active` | 成交量趋势 |
| `policy_stance` | enum | `tightening` / `neutral` / `loosening_moderate` / `loosening_aggressive` | 政策方向 |
| `key_policies` | list | - | 近期关键政策（限购/首付/利率） |
| `rental_market` | enum | `weakening` / `stable` / `strengthening` | 租赁市场强度 |
| `inventory_pressure` | enum | `high`(>24月) / `medium`(12-24) / `low`(<12月) | 挂牌量去化压力 |
| `months_to_clear` | int | - | 预估去化周期(月) |
| `sentiment_phase` | enum | `panic` / `bear_market` / `bottoming` / `early_recovery` / `bull_market` | 市场情绪阶段 |
| `sentiment_score` | int | 0~100 | 悲观指数：0=极度乐观，100=极度悲观 |
| `bearish_factors` | list | - | 利空因素 |
| `bullish_factors` | list | - | 利多因素 |
| `risk_level` | enum | `low` / `medium` / `high` / `extreme` | 综合风险等级 |
| `entry_signal` | enum | `wait` / `cautious` / `ok` / `aggressive` | 入场建议 |

### 3.3 人口流入分析 ⭐⭐

**为什么人口数据是关键维度：**

```
人口流入 → 租赁需求增长 → 租金有支撑 → 租售比可持续
人口流出 → 租赁需求萎缩 → 租金承压     → 租售比只是暂时的
```

**四种组合判断：**

| 租售比 | 人口趋势 | 情绪 | 判断 |
|--------|----------|------|------|
| 高(≥5%) | 强流入 | 悲观 | 🟢 **黄金坑**：基本面好+情绪错杀 |
| 高(≥4.5%) | 流入 | 企稳 | 🟢 **优质标的**：三重确认 |
| 高(≥4%) | 弱流入 | 悲观 | 🟡 **谨慎关注**：需求增长放缓 |
| 高(≥4%) | 流出 | 悲观 | 🔴 **价值陷阱**：需求在萎缩 |
| 高(≥4%) | 流出 | any | 🔴 **回避**：结构性衰退 |
| 低(<4%) | 强流入 | 乐观 | 🟡 **成长型**：赌升值而非租金 |

#### 3.3.1 人口指标

| 指标 | 类型 | 说明 |
|------|------|------|
| `population_trend` | enum | `strong_inflow`(显著流入) / `moderate_inflow` / `stable` / `outflow` |
| `net_migration_annual_wan` | float | 年均净流入人口(万) |
| `population_growth_3y_pct` | float | 近3年人口增速(%) |
| `total_population_wan` | float | 常住人口(万) |
| `working_age_pct` | float | 劳动年龄人口占比(%) |
| `student_population_wan` | float | 高校在校生(万) |
| `key_industries` | list | 主导产业（判断就业质量） |
| `income_to_price_ratio` | str | 房价收入比定性：`affordable` / `moderate` / `expensive` / `severely_unaffordable` |
| `demographic_health` | enum | 人口结构健康度：`excellent` / `good` / `fair` / `poor` |
| `population_risk` | enum | 人口风险：`low` / `medium` / `high`（流出风险） |

#### 3.3.2 人口 LLM Prompt

```
你是一位中国人口与城市研究专家。基于你的训练数据，
分析 {城市} 的人口流入趋势和结构特征。

输出 JSON：

{
  "city": "成都",
  "population_trend": "strong_inflow",
  "net_migration_annual_wan": 12.5,
  "population_growth_3y_pct": 3.8,
  "total_population_wan": 2140,
  "working_age_pct": 68,
  "student_population_wan": 110,
  "key_industries": ["电子信息", "生物医药", "数字经济", "航空航天"],
  "industry_quality": "high",    // high/medium/low
  "income_to_price_ratio": "moderate",
  "demographic_health": "good",
  "population_risk": "low",
  "migration_sources": ["省内三四线", "西北省份"],
  "youth_attractiveness": "high",
  "population_note": "成都连续多年净流入超10万，高校毕业生留存率高"
}
```

### 3.4 小区级风险叠加

在城市情绪+人口基础上，每个候选小区叠加：

| 调整维度 | 说明 |
|----------|------|
| **租金韧性** | 大学周边(高) > 老城区(中高) > 产业新区(低) |
| **价格底部距离** | 跌了多少 vs 历史峰值 → 判断安全边际 |
| **流动性风险** | 老破小：好租难卖 vs 次新：租售两旺 |
| **政策受益度** | 老旧小区改造 / 学区 / 地铁规划等 |

### 3.4 情绪 LLM Prompt

```
你是一位中国房地产市场分析师。基于你的训练数据，
分析 {城市} 当前（截至数据截止期）的房地产市场情绪。

输出 JSON 格式，包含以下字段：

{
  "city": "成都",
  "market_overview": "一句话总结",
  "price_trend_12m": "declining_moderate",
  "price_change_est_pct": -8,
  "volume_trend": "shrinking",
  "policy_stance": "loosening_aggressive",
  "key_policies": ["取消限购", "降首付至15%", "利率3.0%"],
  "rental_market": "stable",
  "rental_note": "核心区租金韧性较强",
  "inventory_pressure": "high",
  "months_to_clear": 20,
  "sentiment_phase": "bottoming",
  "sentiment_score": 70,
  "bearish_factors": ["挂牌量历史高位", "收入预期弱", "人口流入放缓"],
  "bullish_factors": ["政策底确认", "价格回调充分", "租金回报回升"],
  "risk_level": "medium",
  "entry_signal": "cautious",
  "entry_advice": "核心区高租售比可分批建仓，回避远郊"
}
```

---

## 4. Phase 2: 结构化引擎

### 4.1 数据清洗

```
LLM 输出 → 字段标准化 → 异常检测(租金×面积比异常?) → 去重合并 → 核心区校验
```

### 4.2 三维综合评分计算 ⭐

```python
def composite_score(candidate, sentiment, population):
    """
    综合评分 = 租售比 × 质量系数 × 情绪系数 × 人口系数
    
    三维交叉判断逻辑：
    """
    
    # 1. 质量系数（候选自身质量）
    quality = (
        0.35 * confidence +                         # LLM 置信度
        0.30 * rental_resilience(candidate) +       # 租金韧性
        0.20 * market_position(candidate) +          # 市场地位
        0.15 * location_score(candidate)             # 区位评分
    )
    
    # 2. 情绪系数（市场时机）
    sentiment_map = {
        "panic":          0.60,   # 恐慌：大幅折价，但风险高
        "bear_market":    0.75,   # 下跌：谨慎
        "bottoming":      0.85,   # 磨底：逐步安全
        "early_recovery": 1.00,   # 复苏：最佳时机
        "bull_market":    0.80,   # 牛市：警惕追高（租售比会被压缩）
    }
    sentiment_factor = sentiment_map.get(sentiment.sentiment_phase, 0.85)
    
    # 3. 人口系数（需求支撑）⭐
    population_map = {
        "strong_inflow":    1.20,   # 强流入：需求持续增长 → 加分
        "moderate_inflow":  1.05,   # 温和流入
        "stable":           1.00,   # 稳定
        "outflow":          0.55,   # 净流出：需求萎缩 → 大幅减分
    }
    pop_factor = population_map.get(population.population_trend, 1.0)
    
    # 特殊调整：人口流入 + 市场悲观 = 黄金坑
    if population.population_trend in ("strong_inflow", "moderate_inflow") \
       and sentiment.sentiment_phase in ("panic", "bear_market"):
        pop_factor += 0.10  # 额外加分：基本面好+情绪错杀
    
    # 人口流出 + 市场任何状态 = 结构性问题
    if population.population_trend == "outflow":
        quality *= 0.6  # 进一步压低质量系数
    
    composite = candidate.annual_yield_pct * quality * sentiment_factor * pop_factor
    
    return round(composite, 2)
```

### 4.3 风险矩阵（三维交叉）

| 租售比 | 情绪 | 人口 | 标签 | 操作建议 |
|--------|------|------|------|----------|
| ≥5% | bottoming/recovery | 强流入 | 🟢 **黄金坑** | 积极建仓 |
| ≥4.5% | bottoming/recovery | 流入 | 🟢 **优质标的** | 分批建仓 |
| ≥4% | bear/bottoming | 强流入 | 🟢 **左侧布局** | 小仓试探 |
| ≥4.5% | bear/panic | 流入 | 🟡 **等待企稳** | 观察不入 |
| ≥4% | any | 稳定 | 🟡 **中性** | 按租售比判断 |
| ≥4% | any | 流出 | 🔴 **回避** | 不参与 |
| <4% | any | 强流入 | 🟡 **成长型** | 赌升值 |

### 4.4 分层体系

```
TIER 1 (强烈推荐):  yield≥5% + confidence≥0.7 + pop=流入 + risk≤medium
TIER 2 (推荐关注):  yield≥4.5% + confidence≥0.6 + pop≠流出 + risk≤medium
TIER 3 (一般候选):  yield≥4% + confidence≥0.5
TIER 4 (待验证):    yield≥4% + confidence<0.5
TIER X (排除):     risk=extreme 或 pop=outflow（人口流出自动排除）

### 4.4 投资建议生成

结合情绪自动生成建议文案：

```python
def generate_advice(candidate, sentiment):
    if sentiment.phase == "bottoming" and candidate.yield >= 4.5:
        return "价格已回调充分，租售比具备安全边际，可分批建仓"
    elif sentiment.phase in ("bear_market", "panic") and candidate.rental_resilience == "high":
        return "市场悲观但租金韧性极强，适合左侧布局"
    elif sentiment.phase == "panic" and candidate.rental_resilience == "low":
        return "⚠️ 回避：市场恐慌+租金承压，双杀风险高"
    # ...
```

---

## 5. Phase 3: 报告输出

### 5.1 Excel 输出（6 Sheet）

| Sheet | 内容 |
|-------|------|
| **强烈推荐** | TIER_1 (yield≥5% + high conf + low risk) |
| **推荐关注** | TIER_2 |
| **全量候选** | 所有 LLM 输出（含情绪列 + 人口列） |
| **城市基本面** ⭐⭐ | 12 城人口 + 情绪 + 租售比三维对比 |
| **市场情绪** | 12 城情绪走势详情 |
| **爬虫验证** | 通过验证的候选 + 偏差对比（可选） |

### 5.2 城市基本面仪表盘（人口+情绪+收益）

```
╔══════════════════════════════════════════════════════════════════════════╗
║               📊 12 城市基本面仪表盘（人口 + 情绪 + 收益）                ║
╠═══════╤══════════╤══════════╤══════╤══════════╤══════╤════════╤════════╣
║ 城市  │ 人口趋势 │ 年流入   │ 情绪  │ 价格趋势  │ 悲观 │ 达标数  │ 判断   ║
╠═══════╪══════════╪══════════╪══════╪══════════╪══════╪════════╪════════╣
║ 成都  │ 强流入   │ +12.5万  │ 磨底 │ ↓-8%     │  70  │  8个    │ 🟢关注 ║
║ 杭州  │ 强流入   │ +15万    │ 下跌 │ ↓-10%    │  68  │  3个    │ 🟢关注 ║
║ 深圳  │ 流入     │ +8万     │ 磨底 │ ↓-12%    │  65  │  2个    │ 🟢关注 ║
║ 武汉  │ 流入     │ +5万     │ 恐慌 │ ↓-15%    │  85  │  4个    │ 🟡等待 ║
║ 天津  │ 弱流入   │ +1万     │ 下跌 │ ↓-8%     │  72  │  3个    │ 🟡谨慎 ║
║ 西安  │ 稳定     │ +2万     │ 下跌 │ ↓-6%     │  60  │  3个    │ 🟡中性 ║
║ ...   │ ...      │ ...      │ ...  │ ...      │ ...  │ ...     │ ...    ║
╚═══════╧══════════╧══════════╧══════╧══════════╧══════╧════════╧════════╝
```

### 5.3 控制台 Top 10（增强版）

```
🏆 Top 10 投资标的（三维综合评分：租售比×情绪×人口）
#  城市  小区        租售比  人口    情绪    风险  综合  建议
1  成都  太升南路     4.5%   🟢强流入  磨底   中   5.2   分批建仓
2  杭州  文三路       4.5%   🟢强流入  下跌   中   4.9   谨慎关注
3  成都  玉林小区     4.4%   🟢强流入  磨底   中   4.8   分批建仓
4  深圳  福田上下沙   4.1%   🟢流入    磨底   中   4.6   分批建仓
5  武汉  光谷片区     4.4%   🟡流入    恐慌   高   4.2   ⚠️等待企稳
6  西安  南门外       4.4%   🟡稳定    下跌   中   4.0   谨慎关注
7  天津  王顶堤       4.4%   ⚠️弱流入  下跌   中   3.6   观察不入
... 
```

---

## 6. 实施计划

### Step 1: 重构 candidate_finder → llm_extractor
- 新增 `extract_market_sentiment(city)` → 返回城市情绪数据
- 新增 `extract_candidates(city)` → 返回候选小区
- `extract_city_full(city)` → 两轮合并，一次返回完整数据
- 保持内置知识库作为 fallback

### Step 2: 新建 data_engine.py
- `SentimentAnalyzer` 类：情绪指标解析、风险评级
- `ScoringEngine` 类：情绪调整后的综合评分
- `Advisor` 类：自动生成投资建议文案

### Step 3: 重构 main.py
- `--mode llm`（默认）：纯 LLM 模式
- `--mode verify`：LLM + 爬虫验证
- 增加 `--sentiment-only`：仅输出情绪仪表盘

### Step 4: 更新 reporter.py
- Excel 增加「市场情绪」Sheet
- 控制台增加情绪仪表盘
- 颜色标记：绿色=企稳/恢复，红色=恐慌/下跌

---

## 7. 数据流图

```
main.py
  │
  ├─ llm_extractor.extract_city_full("成都")
  │     │
  │     ├─ extract_population("成都")         ⭐⭐ 第一轮
  │     │     └─ { pop_trend, net_migration, student_pop, ... }
  │     │
  │     ├─ extract_market_sentiment("成都")    ⭐ 第二轮
  │     │     └─ { price_trend, sentiment_phase, risk_level, ... }
  │     │
  │     └─ extract_candidates("成都")          第三轮
  │           └─ [{ community, yield, confidence, ... }, ...]
  │
  ├─ data_engine.process(city_data)
  │     │
  │     ├─ 标准化 + 异常检测
  │     ├─ 三维评分 (租售比 × 情绪 × 人口)
  │     │     ├─ 人口流入+悲观 = 黄金坑加分
  │     │     └─ 人口流出 = 自动降级/排除
  │     ├─ TIER 1-4 + TIER X 分类
  │     └─ 投资建议生成
  │
  ├─ [可选] verify_engine.verify_top(candidates[:10])
  │     └─ ke/anjuke 精准搜索 → 偏差对比
  │
  └─ reporter.generate(candidates, sentiment, population, verification)
        ├─ Excel 6 Sheet
        └─ 控制台（Top 10 + 基本面仪表盘）
```
