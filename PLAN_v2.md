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
┌──────────────────────────────────────────────────────────────┐
│                      系统入口 (main.py)                       │
│                                                              │
│  ┌─────────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │  LLM 数据抽取器  │─▶│  结构化引擎    │─▶│   报告输出    │  │
│  │  • 候选小区       │  │  • 标准化      │  │  • Excel     │  │
│  │  • 市场情绪 ⭐    │  │  • 情绪调整 ⭐ │  │  • 控制台    │  │
│  └─────────────────┘  │  • TIER分级    │  └───────────────┘  │
│            │          └───────────────┘                      │
│            ▼                                                 │
│  ┌─────────────────────────────────────┐                     │
│  │        可选：爬虫验证 (Phase 1.5)     │                     │
│  │      Top N 候选精准搜索确认           │                     │
│  └─────────────────────────────────────┘                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Phase 1: LLM 训练数据抽取

### 2.1 每次运行两轮 LLM 提取

| 轮次 | 目的 | 输出 |
|------|------|------|
| **第一轮** | 城市市场情绪分析 ⭐ | 城市级 12 维情绪指标 |
| **第二轮** | 候选小区数据抽取 | 每个核心区 3-8 个结构化候选 |

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

### 3.3 小区级风险叠加

在城市情绪基础上，每个候选小区叠加：

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

### 4.2 情绪调节计算 ⭐

```python
def sentiment_adjusted_score(candidate, market_sentiment):
    """
    综合评分 = 租售比 × 质量系数 × 情绪系数
    """
    # 质量系数
    quality = (
        0.4 * confidence +                         # LLM 置信度
        0.3 * rental_resilience(candidate) +       # 租金韧性
        0.3 * market_position(candidate)            # 市场地位
    )
    
    # 情绪系数 (悲观时压低，乐观时不变)
    sentiment_multiplier = sentiment_adjustment(market_sentiment)
    # sentiment_phase为panic时: ×0.7
    # bear_market时: ×0.8
    # bottoming时: ×0.9
    # early_recovery时: ×1.0
    # bull_market时: ×1.0 (但警惕过热追高)
    
    return yield_pct * quality * sentiment_multiplier
```

### 4.3 分层体系

```
TIER 1 (强烈推荐):  yield≥5% + confidence≥0.7 + risk≤medium   + entry_signal∈{cautious,ok}
TIER 2 (推荐关注):  yield≥4.5% + confidence≥0.6 + risk≤medium
TIER 3 (一般候选):  yield≥4%   + confidence≥0.5
TIER 4 (待验证):    yield≥4%   + confidence<0.5
TIER X (排除):     risk==extreme 或 双杀风险
```

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

### 5.1 Excel 输出（5 Sheet）

| Sheet | 内容 |
|-------|------|
| **强烈推荐** | TIER_1 (yield≥5% + high conf + low risk) |
| **推荐关注** | TIER_2 |
| **全量候选** | 所有 LLM 输出（含情绪列） |
| **市场情绪** ⭐ | 12 城市情绪仪表盘（price_trend / sentiment / entry_signal） |
| **爬虫验证** | 通过验证的候选 + 偏差对比（可选） |

### 5.2 情绪仪表盘示例

```
╔════════════════════════════════════════════════════════════╗
║            📊 12 城市市场情绪仪表盘                         ║
╠═══════╤══════════╤══════════╤═══════╤════════╤══════════╣
║ 城市  │ 价格趋势 │ 情绪阶段  │ 悲观度│ 风险   │ 入场建议  ║
╠═══════╪══════════╪══════════╪═══════╪════════╪══════════╣
║ 深圳  │ ↓-12%   │ bottoming│  65   │ medium │ cautious  ║
║ 上海  │ ↓-5%    │ bottoming│  50   │ medium │ cautious  ║
║ 北京  │ stable  │ recovery │  40   │ low    │ ok        ║
║ 成都  │ ↓-8%    │ bear     │  70   │ medium │ cautious  ║
║ 杭州  │ ↓-10%   │ bear     │  68   │ medium │ cautious  ║
║ 武汉  │ ↓-15%   │ panic    │  85   │ high   │ wait      ║
║ ...   │ ...      │ ...      │ ...   │ ...     │ ...      ║
╚═══════╧══════════╧══════════╧═══════╧════════╧══════════╝
```

### 5.3 控制台 Top 10（增强版）

```
🏆 Top 10 投资标的（情绪调整后综合评分）
#  城市  小区         租售比  租金韧性  情绪阶段  风险  建议
1  成都  太升南路      4.5%    ★★★★    bottoming 中   分批建仓
2  杭州  文三路        4.5%    ★★★★    bear      中   谨慎关注
3  武汉  光谷片区      4.4%    ★★★      panic     高   ⚠️ 等待企稳
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
  │     ├─ extract_market_sentiment("成都")
  │     │     └─ { price_trend, sentiment_phase, risk_level, ... }
  │     │
  │     └─ extract_candidates("成都")
  │           └─ [{ community, yield, confidence, ... }, ...]
  │
  ├─ data_engine.process(city_data)
  │     │
  │     ├─ 标准化 + 异常检测
  │     ├─ 情绪调整评分
  │     ├─ TIER 1-4 分类
  │     └─ 投资建议生成
  │
  ├─ [可选] verify_engine.verify_top(candidates[:10])
  │     └─ ke/anjuke 精准搜索 → 偏差对比
  │
  └─ reporter.generate(candidates, sentiment, verification)
        ├─ Excel 5 Sheet
        └─ 控制台（Top 10 + 情绪仪表盘）
```
