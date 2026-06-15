"""
候选小区发现模块
- 内置知识库：基于训练数据的城市高租售比小区特征
- LLM API：调用外部大模型增强候选列表
- 输出结构化候选列表供爬虫精准验证
"""

import json
import os
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field

import config

logger = logging.getLogger(__name__)


@dataclass
class Candidate:
    """候选小区"""
    community: str                      # 小区名
    district: str = ""                  # 区域
    reason: str = ""                    # 推荐理由
    estimated_price_wan: Optional[float] = None   # 预估总价(万)
    estimated_rent: Optional[float] = None        # 预估月租(元)
    estimated_yield: Optional[float] = None       # 预估租售比(%)
    confidence: float = 0.5             # 置信度 0~1
    source: str = "builtin"             # 来源: builtin / llm


# ==================== 内置知识库 ====================
# 基于高租售比的典型特征和历史数据
#
# 高租售比小区的共性特征（训练数据中总结）：
# 1. 老城区核心地段、配套成熟但房价不高（老破小/老旧小区）
# 2. 高校/产业园区周边（学区刚需+租房需求旺盛）
# 3. 地铁/交通枢纽辐射区（通勤便利推高租金）
# 4. 市中心老旧小区（单价低、租金不低）
# 5. 新城开发区早期楼盘（买入价低、租金随人口流入上涨）
# 6. 户型以 40-70㎡ 为主（小户型租金回报更高）

BUILTIN_CANDIDATES: Dict[str, List[Dict]] = {
    "成都": [
        {"community": "玉林小区", "district": "武侯区", "reason": "老城区核心，生活便利，小户型多，租金稳定",
         "estimated_price_wan": 55, "estimated_rent": 2000, "estimated_yield": 4.4, "confidence": 0.8},
        {"community": "双楠小区", "district": "武侯区", "reason": "成熟社区，地铁覆盖，租住需求旺盛",
         "estimated_price_wan": 60, "estimated_rent": 2200, "estimated_yield": 4.4, "confidence": 0.7},
        {"community": "建设路小区", "district": "成华区", "reason": "电子科大周边，学区+产业双重租赁需求",
         "estimated_price_wan": 50, "estimated_rent": 1800, "estimated_yield": 4.3, "confidence": 0.8},
        {"community": "火车南站片区", "district": "武侯区", "reason": "交通枢纽辐射，通勤便利租客多",
         "estimated_price_wan": 65, "estimated_rent": 2300, "estimated_yield": 4.2, "confidence": 0.7},
        {"community": "抚琴小区", "district": "金牛区", "reason": "老城区老旧小区，单价低租金相对稳定",
         "estimated_price_wan": 45, "estimated_rent": 1600, "estimated_yield": 4.3, "confidence": 0.8},
        {"community": "光华村片区", "district": "青羊区", "reason": "西财周边，学生租房需求大",
         "estimated_price_wan": 52, "estimated_rent": 1900, "estimated_yield": 4.4, "confidence": 0.7},
        {"community": "九眼桥片区", "district": "武侯区", "reason": "市中心老小区，酒吧街辐射，租客稳定",
         "estimated_price_wan": 58, "estimated_rent": 2100, "estimated_yield": 4.3, "confidence": 0.7},
        {"community": "万年场片区", "district": "成华区", "reason": "老小区+地铁，通勤教育双支撑",
         "estimated_price_wan": 48, "estimated_rent": 1700, "estimated_yield": 4.3, "confidence": 0.7},
        {"community": "太升南路片区", "district": "锦江区", "reason": "市中心老区，交通商业发达，小户型多",
         "estimated_price_wan": 62, "estimated_rent": 2300, "estimated_yield": 4.5, "confidence": 0.8},
        {"community": "八里庄片区", "district": "成华区", "reason": "主城旧改区，价格低租金稳定",
         "estimated_price_wan": 46, "estimated_rent": 1650, "estimated_yield": 4.3, "confidence": 0.7},
    ],
    "北京": [
        {"community": "劲松片区", "district": "朝阳区", "reason": "东三环老社区，CBD辐射，白领租赁密集",
         "estimated_price_wan": 180, "estimated_rent": 6000, "estimated_yield": 4.0, "confidence": 0.8},
        {"community": "天通苑", "district": "朝阳区", "reason": "大规模社区，小户型多，地铁通勤",
         "estimated_price_wan": 160, "estimated_rent": 5500, "estimated_yield": 4.1, "confidence": 0.8},
        {"community": "回龙观", "district": "海淀区", "reason": "IT从业者集中居住区，租赁需求旺盛",
         "estimated_price_wan": 170, "estimated_rent": 5800, "estimated_yield": 4.1, "confidence": 0.8},
        {"community": "方庄片区", "district": "丰台区", "reason": "南城老社区，配套成熟价格相对友好",
         "estimated_price_wan": 155, "estimated_rent": 5200, "estimated_yield": 4.0, "confidence": 0.7},
        {"community": "学院路片区", "district": "海淀区", "reason": "高校密集区，学生+教师租赁",
         "estimated_price_wan": 200, "estimated_rent": 6700, "estimated_yield": 4.0, "confidence": 0.7},
        {"community": "潘家园片区", "district": "朝阳区", "reason": "东三环老社区，价格低位置好",
         "estimated_price_wan": 165, "estimated_rent": 5500, "estimated_yield": 4.0, "confidence": 0.7},
    ],
    "上海": [
        {"community": "彭浦新村", "district": "静安区", "reason": "老闸北核心，地铁1号线，小户型租赁活跃",
         "estimated_price_wan": 160, "estimated_rent": 5500, "estimated_yield": 4.1, "confidence": 0.8},
        {"community": "杨浦大学城", "district": "杨浦区", "reason": "复旦/同济/上财周边，学生租房刚需",
         "estimated_price_wan": 180, "estimated_rent": 6200, "estimated_yield": 4.1, "confidence": 0.8},
        {"community": "长宁天山片区", "district": "长宁区", "reason": "虹桥辐射，日企+外籍租赁需求",
         "estimated_price_wan": 200, "estimated_rent": 6800, "estimated_yield": 4.1, "confidence": 0.7},
        {"community": "普陀真如片区", "district": "普陀区", "reason": "老城区旧改区，价格相对低",
         "estimated_price_wan": 150, "estimated_rent": 5000, "estimated_yield": 4.0, "confidence": 0.7},
        {"community": "徐汇田林片区", "district": "徐汇区", "reason": "老社区+漕河泾产业区，白领租赁",
         "estimated_price_wan": 220, "estimated_rent": 7500, "estimated_yield": 4.1, "confidence": 0.7},
    ],
    "广州": [
        {"community": "天河棠下片区", "district": "天河区", "reason": "城中村改造区，IT从业者密集租赁",
         "estimated_price_wan": 120, "estimated_rent": 4200, "estimated_yield": 4.2, "confidence": 0.8},
        {"community": "海珠客村片区", "district": "海珠区", "reason": "大学城+CBD中间地带，租赁活跃",
         "estimated_price_wan": 130, "estimated_rent": 4500, "estimated_yield": 4.2, "confidence": 0.8},
        {"community": "越秀老城区", "district": "越秀区", "reason": "广州传统市中心，老旧小户型多",
         "estimated_price_wan": 140, "estimated_rent": 4800, "estimated_yield": 4.1, "confidence": 0.7},
        {"community": "荔湾中山八", "district": "荔湾区", "reason": "老西关，批发市场商圈租赁需求",
         "estimated_price_wan": 115, "estimated_rent": 4000, "estimated_yield": 4.2, "confidence": 0.7},
    ],
    "深圳": [
        {"community": "南山南油片区", "district": "南山区", "reason": "科技园辐射，IT白领租赁密集",
         "estimated_price_wan": 200, "estimated_rent": 6800, "estimated_yield": 4.1, "confidence": 0.7},
        {"community": "福田上下沙", "district": "福田区", "reason": "城中村改造区，CBD白领首选租赁地",
         "estimated_price_wan": 180, "estimated_rent": 6200, "estimated_yield": 4.1, "confidence": 0.8},
        {"community": "罗湖老城区", "district": "罗湖区", "reason": "深圳最早建成区，老旧小户型多",
         "estimated_price_wan": 160, "estimated_rent": 5500, "estimated_yield": 4.1, "confidence": 0.7},
        {"community": "宝安西乡片区", "district": "宝安区", "reason": "前海辐射+地铁，白领租赁需求增长",
         "estimated_price_wan": 170, "estimated_rent": 5800, "estimated_yield": 4.1, "confidence": 0.7},
    ],
    "重庆": [
        {"community": "观音桥商圈", "district": "江北区", "reason": "核心商圈住宅，单价相对低，租赁需求旺",
         "estimated_price_wan": 55, "estimated_rent": 2000, "estimated_yield": 4.4, "confidence": 0.8},
        {"community": "南坪片区", "district": "南岸区", "reason": "老商圈+大学城，学生白领双需求",
         "estimated_price_wan": 45, "estimated_rent": 1600, "estimated_yield": 4.3, "confidence": 0.7},
        {"community": "杨家坪商圈", "district": "九龙坡区", "reason": "成熟商圈，老旧小区价格低",
         "estimated_price_wan": 48, "estimated_rent": 1700, "estimated_yield": 4.3, "confidence": 0.7},
        {"community": "沙坪坝三峡广场", "district": "沙坪坝区", "reason": "多所高校聚集地，学生租房刚需",
         "estimated_price_wan": 50, "estimated_rent": 1800, "estimated_yield": 4.3, "confidence": 0.8},
        {"community": "大学城片区", "district": "沙坪坝区", "reason": "高校密集，师生租房需求庞大",
         "estimated_price_wan": 38, "estimated_rent": 1400, "estimated_yield": 4.4, "confidence": 0.7},
        {"community": "渝北两路片区", "district": "渝北区", "reason": "空港经济区，产业工人租房需求",
         "estimated_price_wan": 42, "estimated_rent": 1500, "estimated_yield": 4.3, "confidence": 0.6},
    ],
    "武汉": [
        {"community": "光谷片区", "district": "洪山区", "reason": "高校+科技企业密集，租房需求极大",
         "estimated_price_wan": 55, "estimated_rent": 2000, "estimated_yield": 4.4, "confidence": 0.9},
        {"community": "街道口片区", "district": "洪山区", "reason": "武大/华师周边，学生租房核心区",
         "estimated_price_wan": 60, "estimated_rent": 2200, "estimated_yield": 4.4, "confidence": 0.8},
        {"community": "徐东片区", "district": "武昌区", "reason": "商业+住宅混合，租客群体多元",
         "estimated_price_wan": 52, "estimated_rent": 1900, "estimated_yield": 4.4, "confidence": 0.7},
        {"community": "王家湾片区", "district": "汉阳区", "reason": "汉阳老商圈，房价相对低",
         "estimated_price_wan": 45, "estimated_rent": 1600, "estimated_yield": 4.3, "confidence": 0.7},
        {"community": "南湖片区", "district": "洪山区", "reason": "高校聚集，学生+教师租赁需求",
         "estimated_price_wan": 50, "estimated_rent": 1800, "estimated_yield": 4.3, "confidence": 0.7},
        {"community": "硚口路片区", "district": "硚口区", "reason": "汉口老城区，单价低通勤便利",
         "estimated_price_wan": 48, "estimated_rent": 1750, "estimated_yield": 4.4, "confidence": 0.7},
    ],
    "西安": [
        {"community": "小寨片区", "district": "雁塔区", "reason": "大学城核心，长安大学/陕师大等周边",
         "estimated_price_wan": 50, "estimated_rent": 1800, "estimated_yield": 4.3, "confidence": 0.8},
        {"community": "南稍门片区", "district": "碑林区", "reason": "老城区地铁站周边，通勤便利",
         "estimated_price_wan": 48, "estimated_rent": 1700, "estimated_yield": 4.3, "confidence": 0.7},
        {"community": "电子城片区", "district": "雁塔区", "reason": "高新区边缘，IT从业者租赁需求",
         "estimated_price_wan": 55, "estimated_rent": 2000, "estimated_yield": 4.4, "confidence": 0.7},
        {"community": "南门外片区", "district": "碑林区", "reason": "古城核心，商业+旅游租赁需求旺盛",
         "estimated_price_wan": 52, "estimated_rent": 1900, "estimated_yield": 4.4, "confidence": 0.8},
    ],
    "杭州": [
        {"community": "滨江长河片区", "district": "滨江区", "reason": "互联网公司集中，IT白领租房需求旺",
         "estimated_price_wan": 80, "estimated_rent": 3000, "estimated_yield": 4.5, "confidence": 0.7},
        {"community": "文三路片区", "district": "西湖区", "reason": "老城西大学圈，浙大周边租赁需求高",
         "estimated_price_wan": 72, "estimated_rent": 2700, "estimated_yield": 4.5, "confidence": 0.8},
        {"community": "朝晖片区", "district": "拱墅区", "reason": "市中心老小区，单价低配套成熟",
         "estimated_price_wan": 68, "estimated_rent": 2500, "estimated_yield": 4.4, "confidence": 0.7},
        {"community": "翠苑片区", "district": "西湖区", "reason": "文教区核心，高校+IT企业双支撑租赁",
         "estimated_price_wan": 75, "estimated_rent": 2800, "estimated_yield": 4.5, "confidence": 0.8},
    ],
    "南京": [
        {"community": "鼓楼老城区", "district": "鼓楼区", "reason": "南大/东大周边，学术人口+市中心租赁",
         "estimated_price_wan": 72, "estimated_rent": 2700, "estimated_yield": 4.5, "confidence": 0.8},
        {"community": "新街口周边", "district": "秦淮区", "reason": "南京市中心，商业繁华，小户型租赁活跃",
         "estimated_price_wan": 75, "estimated_rent": 2800, "estimated_yield": 4.5, "confidence": 0.8},
        {"community": "南湖片区", "district": "建邺区", "reason": "河西老小区，地铁便利，租客多元",
         "estimated_price_wan": 68, "estimated_rent": 2500, "estimated_yield": 4.4, "confidence": 0.7},
        {"community": "锁金村片区", "district": "玄武区", "reason": "南林周边，老小区+高校租赁需求",
         "estimated_price_wan": 60, "estimated_rent": 2200, "estimated_yield": 4.4, "confidence": 0.7},
    ],
    "青岛": [
        {"community": "台东商圈", "district": "市北区", "reason": "老城区商业中心，小户型密集，租金稳定",
         "estimated_price_wan": 55, "estimated_rent": 2000, "estimated_yield": 4.4, "confidence": 0.8},
        {"community": "李村商圈", "district": "李沧区", "reason": "老城区商圈+地铁，生活配套成熟",
         "estimated_price_wan": 58, "estimated_rent": 2100, "estimated_yield": 4.3, "confidence": 0.7},
        {"community": "市北老城区", "district": "市北区", "reason": "老旧小区集中，价格洼地，租客稳定",
         "estimated_price_wan": 52, "estimated_rent": 1900, "estimated_yield": 4.4, "confidence": 0.7},
        {"community": "麦岛片区", "district": "市南区", "reason": "海大周边，学生+旅游短租需求并存",
         "estimated_price_wan": 70, "estimated_rent": 2600, "estimated_yield": 4.5, "confidence": 0.7},
    ],
    "天津": [
        {"community": "王顶堤片区", "district": "南开区", "reason": "天大/南大周边，学生租赁需求大",
         "estimated_price_wan": 55, "estimated_rent": 2000, "estimated_yield": 4.4, "confidence": 0.8},
        {"community": "大直沽片区", "district": "河东区", "reason": "老城区地铁沿线，老旧小区价格低",
         "estimated_price_wan": 48, "estimated_rent": 1700, "estimated_yield": 4.3, "confidence": 0.7},
        {"community": "小白楼片区", "district": "和平区", "reason": "市中心CBD辐射，白领租赁需求稳定",
         "estimated_price_wan": 65, "estimated_rent": 2400, "estimated_yield": 4.4, "confidence": 0.7},
        {"community": "西北角片区", "district": "红桥区", "reason": "老城厢旧改区，交通便利价格低",
         "estimated_price_wan": 45, "estimated_rent": 1650, "estimated_yield": 4.4, "confidence": 0.7},
    ],
}


# ==================== 候选发现器 ====================

class CandidateFinder:
    """
    大模型驱动的候选小区发现

    两种模式：
    1. 内置知识库（builtin）：直接使用训练数据中已知的高租售比区域特征
    2. LLM API（llm）：调用外部大模型获取更实时、更丰富的候选
    """

    def __init__(self, use_llm: bool = None):
        if use_llm is None:
            use_llm = config.USE_LLM_CANDIDATES
        self.use_llm = use_llm

    def find_candidates(self, city: str,
                        max_candidates: int = None) -> List[Candidate]:
        """
        获取目标城市的高租售比潜力小区候选列表

        参数:
            city: 城市名（中文）
            max_candidates: 最大返回数

        返回:
            Candidate 列表，按预估租售比降序
        """
        if max_candidates is None:
            max_candidates = config.MAX_CANDIDATES_PER_CITY

        candidates: List[Candidate] = []

        # ----- 1. 内置知识库（仅核心区）-----
        core_dists = config.CORE_DISTRICTS.get(city, [])
        builtin = BUILTIN_CANDIDATES.get(city, [])
        for item in builtin:
            # 核心区过滤
            if core_dists and item.get("district", "") not in core_dists:
                continue
            candidates.append(Candidate(
                community=item["community"],
                district=item.get("district", ""),
                reason=item.get("reason", ""),
                estimated_price_wan=item.get("estimated_price_wan"),
                estimated_rent=item.get("estimated_rent"),
                estimated_yield=item.get("estimated_yield"),
                confidence=item.get("confidence", 0.5),
                source="builtin",
            ))

        if not candidates and not self.use_llm:
            logger.warning(f"[{city}] 内置知识库中无核心区候选小区")

        # ----- 2. LLM API 增强 -----
        if self.use_llm and config.LLM_API_KEY:
            try:
                llm_candidates = self._call_llm(city, max_candidates)
                candidates.extend(llm_candidates)
                # 去重：按小区名
                seen = set()
                unique = []
                for c in candidates:
                    key = c.community.lower()
                    if key not in seen:
                        seen.add(key)
                        unique.append(c)
                candidates = unique
            except Exception as e:
                logger.warning(f"LLM 候选发现失败 [{city}]: {e}")

        # 排序：按预估租售比降序，同则按置信度
        candidates.sort(key=lambda c: (
            -(c.estimated_yield or 0),
            -c.confidence,
        ))

        result = candidates[:max_candidates]
        logger.info(
            f"[{city}] 候选发现: {len(result)} 个小区 "
            f"(内置 {len(builtin)} 个{' + LLM' if self.use_llm else ''})"
        )
        return result

    def _call_llm(self, city: str, max_count: int) -> List[Candidate]:
        """
        调用 LLM API 获取候选小区列表
        """
        import requests as req

        core_dists = config.CORE_DISTRICTS.get(city, [])
        dists_str = "、".join(dists.replace("区","") for dists in core_dists) if core_dists else "所有主城区"

        prompt = f"""你是一位中国房地产投资专家。请分析{city}市核心城区的高租售比小区。

⚠️ 重要限制：只考虑以下核心城区：{dists_str}。不要包含郊区/新区/远郊。

背景知识：
- 租售比 = 月租金×12 / 总价×100%
- 高租售比（≥4%）通常出现在：老城区核心地段、大学周边、产业园区、交通枢纽辐射区
- 小户型（40-70㎡）租金回报率更高
- 老旧小区单价低但租金相对稳定

请列出{city}市核心城区中预估租售比可能 ≥ 4% 的小区（最多{max_count}个）。

严格按 JSON 数组格式输出，每个对象包含：
- community: 小区名
- district: 所在区域（必须是上述核心城区之一）
- reason: 推荐理由（1-2句话）
- estimated_total_price_wan: 预估总价（万元，按50㎡参考面积）
- estimated_monthly_rent: 预估月租金（元）
- estimated_yield: 预估租售比（%）

只输出 JSON 数组，不要其他文字。"""

        api_key = config.LLM_API_KEY or os.getenv("LLM_API_KEY", "")
        api_base = config.LLM_API_BASE
        model = config.LLM_MODEL

        resp = req.post(
            f"{api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 2000,
            },
            timeout=60,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        # 尝试解析 JSON（可能包裹在 markdown 代码块中）
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]

        items = json.loads(content)
        return [
            Candidate(
                community=item["community"],
                district=item.get("district", ""),
                reason=item.get("reason", ""),
                estimated_price_wan=item.get("estimated_total_price_wan"),
                estimated_rent=item.get("estimated_monthly_rent"),
                estimated_yield=item.get("estimated_yield"),
                confidence=0.6,
                source="llm",
            )
            for item in items
        ]

    def get_candidate_communities(self, city: str) -> List[str]:
        """仅返回小区名列表，供爬虫使用"""
        candidates = self.find_candidates(city)
        return [c.community for c in candidates]

    def to_candidate_map(self, city: str) -> Dict[str, Candidate]:
        """返回 {小区名: Candidate} 映射"""
        candidates = self.find_candidates(city)
        return {c.community: c for c in candidates}
