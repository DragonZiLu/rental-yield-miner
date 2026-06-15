# 房产租售比挖掘系统

从贝壳找房、安居客双源抓取一二线城市小区挂牌价和租金，计算年租售比，筛选高回报率标的。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 创建输出目录
mkdir -p output

# 单城市测试
python main.py --cities 成都

# 全量 12 城市运行
python main.py

# 自定义阈值
python main.py --threshold 3.5 --max-price 200

# 仅贝壳数据源
python main.py --no-anjuke
```

## 租售比公式

```
年租售比 = 月均租金 × 12 / 小区均价 × 参考面积(50㎡) × 100%
```

## 项目结构

```
rental-yield-miner/
├── config.py               # 全局配置
├── scrapers/                # 爬虫模块
│   ├── base.py              # 抽象基类
│   ├── ke_scraper.py        # 贝壳找房
│   └── anjuke_scraper.py    # 安居客
├── merger.py               # 双源数据合并
├── calculator.py            # 租售比计算
├── reporter.py              # 报告生成
├── main.py                  # 入口
└── output/                  # 报告输出目录
```
