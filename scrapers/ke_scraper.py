"""
贝壳找房爬虫 - ke.com
爬取二手房均价 + 租金数据
"""

import re
import logging
from typing import List, Dict, Optional

from .base import BaseScraper
import config

logger = logging.getLogger(__name__)


class KeScraper(BaseScraper):
    """贝壳找房爬虫"""

    def __init__(self, city_name: str):
        super().__init__(city_name)
        city_code = config.CITIES.get(city_name, {}).get("ke", city_name)
        self.base_url = f"https://{city_code}.ke.com"
        # e.g. https://bj.ke.com (新域名格式)

    # ==================== 二手房 ====================
    def _parse_sale_card(self, card) -> Optional[Dict]:
        """从列表页卡片中提取小区级二手数据"""
        try:
            # 小区名
            community_el = card.select_one(".communityName a, .info .title a")
            if not community_el:
                return None
            community_name = community_el.get_text(strip=True)

            # 总价（万元）
            total_price_el = card.select_one(".totalPrice span, .priceInfo .totalPrice span")
            total_price = None
            if total_price_el:
                price_text = total_price_el.get_text(strip=True)
                price_match = re.search(r"[\d.]+", price_text)
                if price_match:
                    total_price = float(price_match.group())

            # 面积（㎡）
            area_el = card.select_one(".area, .square")
            area = None
            if area_el:
                area_text = area_el.get_text(strip=True)
                area_match = re.search(r"[\d.]+", area_text)
                if area_match:
                    area = float(area_match.group())

            # 区域
            district_el = card.select_one(".positionInfo a, .houseInfo a")
            district = district_el.get_text(strip=True) if district_el else ""

            # 建造年份
            year_el = card.select_one(".followInfo, .subInfo")
            year = None
            if year_el:
                year_text = year_el.get_text(strip=True)
                year_match = re.search(r"(\d{4})", year_text)
                if year_match:
                    year = int(year_match.group(1))

            return {
                "community": community_name,
                "total_price_wan": total_price,   # 总价（万元）
                "area_sqm": area,                  # 面积（㎡）
                "district": district,
                "build_year": year,
            }
        except Exception as e:
            logger.debug(f"解析二手房卡片异常: {e}")
            return None

    def fetch_sale_listings(self) -> List[Dict]:
        """分页爬取二手房源"""
        all_listings = []
        sale_url = f"{self.base_url}/ershoufang/"

        for page in range(1, config.MAX_PAGES_PER_CITY + 1):
            page_url = f"{sale_url}pg{page}/"
            soup = self._fetch(page_url, referer=self.base_url)
            if not soup:
                logger.warning(f"[{self.city_name}] 贝壳二手房第 {page} 页请求失败，停止翻页")
                break

            # 解析房源卡片
            cards = soup.select(".sellListContent li, .listContent li, .resblock-list li")
            if not cards:
                cards = soup.select(".content .leftContent ul li")

            page_count = 0
            for card in cards:
                parsed = self._parse_sale_card(card)
                if parsed:
                    all_listings.append(parsed)
                    page_count += 1

            logger.info(f"[{self.city_name}] 贝壳二手房 第{page}页 → 解析 {page_count} 条")

            if page_count == 0:
                # 无数据，可能已到末页或反爬
                break

            self._random_delay()

        return all_listings

    # ==================== 租金 ====================
    def _parse_rental_card(self, card) -> Optional[Dict]:
        """从租金列表页卡片提取数据"""
        try:
            # 小区名
            community_el = card.select_one(".content__list--item--des a, .info .title a")
            if not community_el:
                community_el = card.select_one(".content__list--item--aside")
            if not community_el:
                return None
            community_name = community_el.get_text(strip=True)

            # 月租金
            price_el = card.select_one(".content__list--item-price em, .price span")
            monthly_rent = None
            if price_el:
                price_text = price_el.get_text(strip=True)
                price_match = re.search(r"[\d.]+", price_text)
                if price_match:
                    monthly_rent = float(price_match.group())

            # 面积
            area_el = card.select_one(".content__list--item--des")
            area = None
            if area_el:
                area_text = area_el.get_text(strip=True)
                area_match = re.search(r"([\d.]+)㎡", area_text)
                if area_match:
                    area = float(area_match.group(1))

            return {
                "community": community_name,
                "monthly_rent": monthly_rent,  # 元/月
                "area_sqm": area,              # 面积（㎡）
            }
        except Exception as e:
            logger.debug(f"解析租金卡片异常: {e}")
            return None

    # ==================== 精准搜索 ====================
    def search_community(self, community_name: str) -> Optional[Dict]:
        """
        精准搜索指定小区，返回 {sale: {...}, rental: {...}} 或 None

        URL: https://{city}.ke.com/ershoufang/rs{社区名}/
        """
        from urllib.parse import quote
        encoded = quote(community_name)
        info = {"community": community_name, "source": "贝壳精准搜索"}

        # 二手房
        sale_url = f"{self.base_url}/ershoufang/rs{encoded}/"
        soup = self._fetch(sale_url, referer=self.base_url)
        if soup:
            card = soup.select_one(".sellListContent li, .listContent li, [class*=item]")
            if card:
                parsed = self._parse_sale_card(card)
                if parsed:
                    info.update(parsed)

        self._random_delay()

        # 租金
        rent_url = f"{self.base_url}/zufang/rs{encoded}/"
        soup = self._fetch(rent_url, referer=self.base_url)
        if soup:
            card = soup.select_one(".content__list--item, [class*=item]")
            if card:
                parsed = self._parse_rental_card(card)
                if parsed:
                    info.update(parsed)

        return info if "total_price_wan" in info or "monthly_rent" in info else None

    def search_communities(self, community_names: List[str]) -> List[Dict]:
        """批量精准搜索多个小区"""
        results = []
        for name in community_names:
            self._random_delay()
            r = self.search_community(name)
            if r:
                results.append(r)
            else:
                results.append({"community": name, "source": "贝壳精准搜索", "not_found": True})
        return results

    def fetch_rental_listings(self) -> List[Dict]:
        """分页爬取租金列表"""
        all_listings = []
        rent_url = f"{self.base_url}/zufang/"

        for page in range(1, config.MAX_PAGES_PER_CITY + 1):
            page_url = f"{rent_url}pg{page}/"
            soup = self._fetch(page_url, referer=self.base_url)
            if not soup:
                logger.warning(f"[{self.city_name}] 贝壳租金第 {page} 页请求失败，停止翻页")
                break

            cards = soup.select(".content__list--item, .content .leftContent .content__list--item, .rentContent li")
            page_count = 0
            for card in cards:
                parsed = self._parse_rental_card(card)
                if parsed:
                    all_listings.append(parsed)
                    page_count += 1

            logger.info(f"[{self.city_name}] 贝壳租金 第{page}页 → 解析 {page_count} 条")

            if page_count == 0:
                break

            self._random_delay()

        return all_listings
