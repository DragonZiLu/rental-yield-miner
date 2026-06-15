# 🏠 房产租售比挖掘系统

从**贝壳找房** + **安居客**双源抓取一二线城市小区挂牌价和租金，计算年租售比，自动筛选高回报率投资标的并生成 Excel 报告。

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📊 租售比公式

```
年租售比 (%) = 月均租金(元) × 12 / (均价(元/㎡) × 参考面积(50㎡)) × 100%
```

- ≥ **4%** 视为达标标的
- ≥ **5%** 高亮为优质标的

---

## 🗺️ 覆盖城市

| 分类 | 城市 |
|------|------|
| 一线 | 北京、上海、广州、深圳 |
| 新一线/二线 | 成都、杭州、青岛、武汉、重庆、天津、南京、西安 |

**共 12 城**，可自定义扩展。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行

```bash
# 单城市测试
python main.py --cities 成都

# 全量 12 城市
python main.py

# 自定义阈值 + 总价上限（聚焦老破小）
python main.py --threshold 3.5 --max-price 200

# 仅贝壳数据源
python main.py --no-anjuke

# 控制每城最大爬取页数
python main.py --pages 5
```

### 3. 输出

- **Excel 报告** → `output/rental_yield_report_YYYYMMDD.xlsx`
  - Sheet 1：达标小区汇总（按租售比降序）
  - Sheet 2：城市对比统计
  - Sheet 3：全量数据
- **控制台摘要** → Top 10 投资标的 + 汇总统计

---

## 📖 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--cities` | 指定城市，空格分隔 | 全部 12 城 |
| `--threshold` | 最低租售比阈值 (%) | 4.0 |
| `--max-price` | 总价上限（万元） | 不限 |
| `--no-anjuke` | 禁用安居客，仅贝壳 | 否 |
| `--pages` | 每城最大爬取页数 | 10 |
| `--output-dir` | 报告输出目录 | output |

---

## 🧱 项目结构

```
rental-yield-miner/
├── config.py                # 全局配置（城市、阈值、反爬参数）
├── scrapers/
│   ├── __init__.py
│   ├── base.py              # BaseScraper 抽象基类
│   ├── ke_scraper.py        # 贝壳找房爬虫
│   └── anjuke_scraper.py    # 安居客爬虫
├── merger.py                # 双源数据合并与交叉验证
├── calculator.py            # 租售比计算 + 阈值过滤
├── reporter.py              # Excel 输出 + 控制台摘要
├── main.py                  # 主入口 + CLI
├── output/                  # 报告输出目录
└── requirements.txt
```

---

## 🛡️ 反爬机制

- **随机 User-Agent**：`fake-useragent` 自动轮换
- **请求延迟**：每次间隔 2~5 秒随机延迟
- **Session 复用**：`requests.Session` + Referer 伪造
- **指数退避重试**：最多 3 次，base=5s
- **代理支持**：可在 `config.py` 配置代理池

---

## 📦 依赖

```
requests    ≥ 2.31     HTTP 请求
beautifulsoup4 ≥ 4.12   HTML 解析
lxml        ≥ 4.9      XML/HTML 解析器
fake-useragent ≥ 1.4   随机 UA 轮换
openpyxl    ≥ 3.1      Excel 读写
pandas      ≥ 2.0      数据处理
tqdm        ≥ 4.66     进度条
rich        ≥ 13.0     控制台美化
python-dotenv ≥ 1.0    环境变量
```

---

## ⚠️ 注意事项

1. **反爬验证**：贝壳和安居客有较强的反爬机制（CAPTCHA），`requests` 直接请求可能触发人机验证。如遇"人机验证"页面，需使用 Selenium/Playwright 等浏览器自动化方案。
2. **CSS 选择器**：目标网站页面结构可能不定期变更，若解析 0 条需检查并调整选择器。
3. **请求频率**：默认延迟 2~5 秒，降低频率可减少封禁风险。

---

## 📄 License

MIT
