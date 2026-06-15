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

# ==================== 核心区定义 ====================
# 仅搜索各城市核心城区（主城区），排除远郊/新区
CORE_DISTRICTS = {
    "北京": ["东城区", "西城区", "朝阳区", "海淀区", "丰台区", "石景山区"],
    "上海": ["黄浦区", "静安区", "徐汇区", "长宁区", "虹口区", "杨浦区", "普陀区", "浦东新区"],
    "广州": ["天河区", "越秀区", "海珠区", "荔湾区", "白云区"],
    "深圳": ["福田区", "罗湖区", "南山区", "宝安区"],
    "成都": ["锦江区", "青羊区", "武侯区", "金牛区", "成华区"],
    "杭州": ["上城区", "拱墅区", "西湖区", "滨江区"],
    "青岛": ["市南区", "市北区", "崂山区", "李沧区"],
    "武汉": ["江岸区", "江汉区", "硚口区", "武昌区", "汉阳区", "洪山区"],
    "重庆": ["渝中区", "江北区", "南岸区", "沙坪坝区", "九龙坡区", "渝北区"],
    "天津": ["和平区", "南开区", "河西区", "河东区", "河北区", "红桥区"],
    "南京": ["玄武区", "秦淮区", "鼓楼区", "建邺区"],
    "西安": ["碑林区", "莲湖区", "新城区", "雁塔区", "未央区"],
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

# ==================== LLM 候选发现配置 ====================
# 是否启用 LLM 生成的候选小区（默认使用内置知识库）
USE_LLM_CANDIDATES = False

# LLM API 配置（支持 OpenAI 兼容接口）
LLM_API_KEY = ""       # 也可通过环境变量 LLM_API_KEY 设置
LLM_API_BASE = "https://api.openai.com/v1"
LLM_MODEL = "gpt-4o"

# 每城市最多返回候选小区数
MAX_CANDIDATES_PER_CITY = 30

# ==================== 小红书配置 ====================
# 每小区最多搜索笔记数
XHS_MAX_NOTES_PER_COMMUNITY = 10

# 小红书搜索延迟（秒）
XHS_DELAY_MIN = 3.0
XHS_DELAY_MAX = 6.0

# 小红书最多验证小区数（达标小区中取 Top N）
XHS_MAX_VERIFY_COMMUNITIES = 20

# ==================== 输出配置 ====================
OUTPUT_DIR = "output"

# Excel 报告文件名模板
OUTPUT_FILENAME = "rental_yield_report_{date}.xlsx"
