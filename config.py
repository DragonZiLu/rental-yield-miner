"""
房产租售比挖掘系统 - 全局配置文件
"""

# ==================== 城市配置 ====================
CITIES = {
    "北京": {"ke": "bj", "anjuke": "beijing"},
    "上海": {"ke": "sh", "anjuke": "shanghai"},
    "广州": {"ke": "gz", "anjuke": "guangzhou"},
    "深圳": {"ke": "sz", "anjuke": "shenzhen"},
    "成都": {"ke": "cd", "anjuke": "chengdu"},
    "杭州": {"ke": "hz", "anjuke": "hangzhou"},
    "青岛": {"ke": "qd", "anjuke": "qingdao"},
    "武汉": {"ke": "wh", "anjuke": "wuhan"},
    "重庆": {"ke": "cq", "anjuke": "chongqing"},
    "天津": {"ke": "tj", "anjuke": "tianjin"},
    "南京": {"ke": "nj", "anjuke": "nanjing"},
    "西安": {"ke": "xa", "anjuke": "xian"},
}

# ==================== 筛选阈值 ====================
# 年租售比最低阈值（百分比）：月租金 × 12 / 总价 × 100%
YIELD_THRESHOLD = 4.0

# 参考面积（平方米），用于估算总价 = 均价 × 参考面积
REFERENCE_AREA_SQM = 50

# 总价上限（万元），默认不限，可聚焦老破小
MAX_TOTAL_PRICE_WAN = None  # e.g., 300

# ==================== 爬虫配置 ====================
# 请求随机延迟范围（秒）
REQUEST_DELAY_MIN = 2.0
REQUEST_DELAY_MAX = 5.0

# 最大重试次数
MAX_RETRIES = 3

# 重试退避基础（秒）：backoff = base * (2 ** attempt)
RETRY_BACKOFF_BASE = 5

# 每个城市最大爬取页数（每页约 30 条小区数据）
MAX_PAGES_PER_CITY = 10

# 请求超时（秒）
REQUEST_TIMEOUT = 30

# User-Agent 轮换：False 则使用默认 UA
USE_RANDOM_UA = True

# 默认请求头（无随机 UA 时使用）
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# 代理配置（可选）
# 格式: {"http": "http://proxy:port", "https": "https://proxy:port"}
PROXIES = None

# 并发线程数（同时爬取贝壳 + 安居客）
MAX_WORKERS = 2

# ==================== 输出配置 ====================
OUTPUT_DIR = "output"

# Excel 报告文件名模板
OUTPUT_FILENAME = "rental_yield_report_{date}.xlsx"
