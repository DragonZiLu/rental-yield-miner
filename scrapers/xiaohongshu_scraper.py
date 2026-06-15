"""
小红书辅助验证模块
- 搜索小区名 + 租金/房价关键词
- 从笔记标题和摘要中提取价格信息
- 计算小区热度 & 置信度
"""

import re
import time
import random
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)

# 价格提取正则
PRICE_PATTERNS = [
    # 月租金: "租金2800", "月租2500元", "3500/月"
    (re.compile(r"(?:租金|月租|房租)[\s：:]*(\d{3,5})\s*(?:元|块|/月)"), "monthly_rent"),
    (re.compile(r"(\d{3,5})\s*(?:元|块)\s*/?\s*(?:月|每月)"), "monthly_rent"),
    # 总价: "总价58万", "58万", "挂牌价60w"
    (re.compile(r"(?:总价|挂牌价|售价|房价)[\s：:]*(\d{2,4})\s*(?:万|w|W)"), "total_price_wan"),
    (re.compile(r"(\d{2,4})\s*(?:万|w|W)\s*(?:总价|一套|拿下|入手)"), "total_price_wan"),
    # 租售比: "租售比4.5%", "回报率5%", "yield 4.2%"
    (re.compile(r"(?:租售比|回报率|租金回报|yield)[\s：:]*(\d+\.?\d*)\s*%"), "yield_pct"),
    # 面积: "50平", "60平米"
    (re.compile(r"(\d{2,3})\s*(?:平|平米|㎡|m2)"), "area_sqm"),
    # 单价: "1.2万/平", "12000元/平"
    (re.compile(r"(\d+\.?\d*)\s*万\s*/\s*(?:平|平米|㎡)"), "unit_price_wan"),
    (re.compile(r"(\d{4,5})\s*元?\s*/\s*(?:平|平米|㎡)"), "unit_price_yuan"),
]


class XiaohongshuScraper:
    """小红书搜索爬虫 - 用于辅助验证"""

    BASE_URL = "https://www.xiaohongshu.com"

    def __init__(self):
        self.session = self._build_session()
        self._ua = None
        if config.USE_RANDOM_UA:
            try:
                from fake_useragent import UserAgent
                self._ua = UserAgent()
            except Exception:
                pass

    def _build_session(self) -> requests.Session:
        sess = requests.Session()
        sess.headers.update({
            **config.DEFAULT_HEADERS,
            "Referer": "https://www.xiaohongshu.com/",
            "Origin": "https://www.xiaohongshu.com",
        })
        if config.PROXIES:
            sess.proxies.update(config.PROXIES)
        return sess

    def _get_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        headers = {}
        if self._ua:
            headers["User-Agent"] = self._ua.random
        if referer:
            headers["Referer"] = referer
        return headers

    def _random_delay(self, min_s: float = None, max_s: float = None):
        if min_s is None:
            min_s = config.XHS_DELAY_MIN
        if max_s is None:
            max_s = config.XHS_DELAY_MAX
        delay = random.uniform(min_s, max_s)
        logger.debug(f"XHS 延迟 {delay:.1f}s ...")
        time.sleep(delay)

    def _extract_prices(self, text: str) -> Dict[str, List[float]]:
        """从文本中提取价格相关数字"""
        results: Dict[str, List[float]] = {}
        for pattern, key in PRICE_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                values = [float(m) for m in matches]
                if key not in results:
                    results[key] = []
                results[key].extend(values)
        return results

    def search_community(self, city: str, community: str,
                         max_notes: int = None) -> Dict:
        """
        搜索指定小区的相关信息

        返回:
            {
                "city": 城市,
                "community": 小区名,
                "total_notes": 搜索结果总数,
                "notes": [{title, snippet, likes, url}, ...],
                "extracted": {monthly_rent: [2800, 3000], total_price_wan: [58, 62], ...},
                "heat_score": 热度评分,
                "confidence": 置信度 0~1,
            }
        """
        if max_notes is None:
            max_notes = config.XHS_MAX_NOTES_PER_COMMUNITY

        keyword = f"{community} {city} 租金"
        encoded = quote(keyword)
        search_url = f"{self.BASE_URL}/search_result?keyword={encoded}&type=51"

        result = {
            "city": city,
            "community": community,
            "total_notes": 0,
            "notes": [],
            "extracted": {},
            "heat_score": 0,
            "confidence": 0.0,
        }

        try:
            soup = self._fetch_page(search_url)
            if not soup:
                return result

            # 解析笔记卡片
            cards = soup.select(".note-item, .search-result-item, .feeds-page .note-item")
            if not cards:
                cards = soup.select("[class*=note], [class*=card], section.note-item")

            collected = 0
            all_text = ""

            for card in cards[:max_notes]:
                title_el = card.select_one(".title, .note-title, a.title, [class*=title]")
                snippet_el = card.select_one(".desc, .note-desc, [class*=desc]")
                like_el = card.select_one(".like-count, .count, [class*=like]")
                link_el = card.select_one("a[href]")

                title = title_el.get_text(strip=True) if title_el else ""
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                likes = 0
                if like_el:
                    like_match = re.search(r"[\d.]+万?$|[\d.]+", like_el.get_text(strip=True))
                    if like_match:
                        likes = self._parse_count(like_match.group())

                url = link_el.get("href", "") if link_el else ""
                if url and not url.startswith("http"):
                    url = self.BASE_URL + url

                if title or snippet:
                    result["notes"].append({
                        "title": title,
                        "snippet": snippet,
                        "likes": likes,
                        "url": url,
                    })
                    all_text += f"{title} {snippet} "
                    collected += 1

            result["total_notes"] = collected

            # 提取价格信息
            result["extracted"] = self._extract_prices(all_text)

            # 热度 = 笔记数 + 加权点赞
            total_likes = sum(n["likes"] for n in result["notes"])
            result["heat_score"] = collected * 10 + total_likes

            # 置信度 = 有多篇笔记提到相似价格
            result["confidence"] = self._calc_confidence(result["extracted"])

            logger.info(
                f"XHS [{city}] {community}: {collected}笔记 | "
                f"热度{result['heat_score']} | 置信度{result['confidence']:.2f}"
            )

        except Exception as e:
            logger.warning(f"XHS 搜索异常 [{city}]{community}: {e}")

        return result

    def search_city_yield(self, city: str, max_notes: int = 20) -> Dict:
        """
        搜索城市级别的"租售比"话题讨论

        返回: {notes: [...], extracted: {...}, top_communities: [...]}
        """
        keyword = f"{city} 租售比 投资"
        encoded = quote(keyword)
        search_url = f"{self.BASE_URL}/search_result?keyword={encoded}&type=51"

        result = {"notes": [], "extracted": {}, "top_communities": []}
        all_text = ""

        try:
            soup = self._fetch_page(search_url)
            if not soup:
                return result

            cards = soup.select(".note-item, .search-result-item, [class*=note]")
            for i, card in enumerate(cards[:max_notes]):
                title_el = card.select_one(".title, .note-title, [class*=title]")
                title = title_el.get_text(strip=True) if title_el else ""

                snippet_el = card.select_one(".desc, [class*=desc]")
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                if title:
                    result["notes"].append({"title": title, "snippet": snippet})
                    all_text += f"{title} {snippet} "

            result["extracted"] = self._extract_prices(all_text)

            # 从笔记中提取小区名（中文名 + 小区/花园/苑）
            community_pattern = re.compile(
                r"([\u4e00-\u9fa5]{2,6}(?:小区|花园|苑|城|府|庭|湾|里|园|庄|寓|居|公馆|壹号|国际))"
            )
            mentioned = community_pattern.findall(all_text)
            from collections import Counter
            result["top_communities"] = [c for c, _ in Counter(mentioned).most_common(10)]

        except Exception as e:
            logger.warning(f"XHS 城市搜索异常 [{city}]: {e}")

        return result

    def verify_communities(self, city: str, communities: List[str]) -> List[Dict]:
        """
        批量验证小区数据，按热度排序返回

        参数:
            city: 城市名
            communities: 待验证的小区名列表（top N 达标小区）

        返回:
            验证结果列表
        """
        results = []
        for community in communities:
            self._random_delay()
            r = self.search_community(city, community)
            results.append(r)
        return sorted(results, key=lambda x: x["confidence"], reverse=True)

    # ---------- 内部方法 ----------
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                headers = self._get_headers(self.BASE_URL)
                resp = self.session.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
                resp.raise_for_status()
                resp.encoding = "utf-8"
                return BeautifulSoup(resp.text, "lxml")
            except requests.RequestException as e:
                backoff = config.RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning(f"XHS 请求失败 (第{attempt}次): {e}，等待{backoff}s")
                time.sleep(backoff)
        return None

    @staticmethod
    def _parse_count(text: str) -> int:
        """解析 "1.2万" → 12000, "99" → 99"""
        text = text.strip()
        if "万" in text:
            return int(float(text.replace("万", "")) * 10000)
        try:
            return int(float(text))
        except ValueError:
            return 0

    @staticmethod
    def _calc_confidence(extracted: Dict[str, List[float]]) -> float:
        """
        基于提取数据的丰富度计算置信度 0~1
        有租金+总价 → 高；仅租金 → 中；无数据 → 0
        """
        score = 0.0
        if "monthly_rent" in extracted and len(extracted["monthly_rent"]) > 0:
            score += 0.4
        if "total_price_wan" in extracted and len(extracted["total_price_wan"]) > 0:
            score += 0.4
        if "yield_pct" in extracted and len(extracted["yield_pct"]) > 0:
            score += 0.3
        if "unit_price_wan" in extracted or "unit_price_yuan" in extracted:
            score += 0.2
        return min(score, 1.0)
