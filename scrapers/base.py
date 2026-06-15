"""
BaseScraper 抽象基类
- Session 管理
- Header 伪造（随机 UA）
- 请求延迟 & 重试（指数退避）
- HTML 解析
"""

import time
import random
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, List

import requests
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """爬虫抽象基类，封装通用反爬与请求逻辑"""

    def __init__(self, city_name: str):
        self.city_name = city_name
        self.session = self._build_session()

        # 尝试加载 fake-useragent
        self._ua = None
        if config.USE_RANDOM_UA:
            try:
                from fake_useragent import UserAgent
                self._ua = UserAgent()
                logger.debug("fake-useragent 已加载")
            except Exception:
                logger.warning("fake-useragent 加载失败，使用默认 User-Agent")
                self._ua = None

    # ---------- Session 构建 ----------
    def _build_session(self) -> requests.Session:
        sess = requests.Session()
        sess.headers.update(config.DEFAULT_HEADERS)
        if config.PROXIES:
            sess.proxies.update(config.PROXIES)
        return sess

    def _get_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """构造请求头（含随机 UA 与 Referer）"""
        headers = {}
        if self._ua:
            headers["User-Agent"] = self._ua.random
        if referer:
            headers["Referer"] = referer
        return headers

    # ---------- 反爬机制 ----------
    def _random_delay(self):
        """随机延迟 2~5 秒"""
        delay = random.uniform(config.REQUEST_DELAY_MIN, config.REQUEST_DELAY_MAX)
        logger.debug(f"延迟 {delay:.1f}s ...")
        time.sleep(delay)

    def _fetch(self, url: str, referer: Optional[str] = None,
               params: Optional[Dict] = None) -> Optional[BeautifulSoup]:
        """带重试机制的 GET 请求，返回 BeautifulSoup 对象"""
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                headers = self._get_headers(referer)
                resp = self.session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=config.REQUEST_TIMEOUT,
                )
                resp.raise_for_status()
                resp.encoding = "utf-8"
                logger.info(f"[{self.city_name}] {url} → {resp.status_code}")
                return BeautifulSoup(resp.text, "lxml")

            except requests.RequestException as e:
                backoff = config.RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning(
                    f"[{self.city_name}] 请求失败 (第 {attempt}/{config.MAX_RETRIES} 次): {e}，"
                    f"等待 {backoff}s 后重试..."
                )
                time.sleep(backoff)

        logger.error(f"[{self.city_name}] 请求最终失败: {url}")
        return None

    # ---------- 抽象方法 ----------
    @abstractmethod
    def fetch_sale_listings(self) -> List[Dict]:
        """获取二手房源列表 → [{小区名, 均价(万元), 区域, 建筑年代, ...}]"""
        ...

    @abstractmethod
    def fetch_rental_listings(self) -> List[Dict]:
        """获取租金列表 → [{小区名, 月租金(元), 面积, ...}]"""
        ...

    def scrape(self) -> Dict[str, List[Dict]]:
        """执行完整爬取流程，返回 {'sales': [...], 'rentals': [...]}"""
        logger.info(f"======== [{self.city_name}] 开始爬取 ========")
        sales = self.fetch_sale_listings()
        self._random_delay()
        rentals = self.fetch_rental_listings()
        logger.info(f"[{self.city_name}] 二手房 {len(sales)} 条 | 租金 {len(rentals)} 条")
        return {"sales": sales, "rentals": rentals}
