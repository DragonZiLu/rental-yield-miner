"""
安居客爬虫 - anjuke.com
爬取二手房均价 + 租金数据
"""

import re
import logging
from typing import List, Dict, Optional

from .base import BaseScraper
import config

logger = logging.getLogger(__name__)


class AnjukeScraper(BaseScraper):
    """安居客爬虫"""

    def __init__(self, city_name: str):
        super().__init__(city_name)
        city_code = config.CITIES.get(city_name, {}).get("anjuke", city_name)
        self.base_url = f"https://{city_code}.anjuke.com"

    # ==================== 二手房 ====================
    def _parse_sale_card(self, card) -> Optional[Dict]:
        """解析二手房列表卡片"""
        try:
            # 小区名
            community_el = card.select_one(".comm-address, .details-item span, .house-details .comm-address")
            if not community_el:
                community_el = card.select_one("a[href*='community']")
            if not community_el:
                return None
            community_name = community_el.get_text(strip=True)

            # 总价（万元）
            price_el = card.select_one(".price-det .total-price, .price", )
            total_price = None
            if price_el:
                price_text = price_el.get_text(strip=True)
                price_match = re.search(r"[\d.]+", price_text)
                if price_match:
                    total_price = float(price_match.group())

            # 面积
            area_el = card.select_one(".details-item .building-area, .house-info .area")
            area = None
            if area_el:
                area_text = area_el.get_text(strip=True)
                # 格式: "90㎡" 或 "90平米"
                area_match = re.search(r"([\d.]+)", area_text)
                if area_match:
                    area = float(area_match.group(1))

            # 区域
            district_el = card.select_one(".comm-address, .details-item span")
            district = district_el.get_text(strip=True) if district_el else ""

            # 建造年份
            year_el = card.select_one(".building-year, .details-item")
            year = None
            if year_el:
                year_text = year_el.get_text(strip=True)
                year_match = re.search(r"(\d{4})", year_text)
                if year_match:
                    year = int(year_match.group(1))

            return {
                "community": community_name,
                "total_price_wan": total_price,
                "area_sqm": area,
                "district": district,
                "build_year": year,
            }
        except Exception as e:
            logger.debug(f"解析安居客二手房卡片异常: {e}")
            return None

    def fetch_sale_listings(self) -> List[Dict]:
        """分页爬取二手房"""
        all_listings = []
        sale_url = f"{self.base_url}/sale/"

        for page in range(1, config.MAX_PAGES_PER_CITY + 1):
            page_url = f"{sale_url}p{page}/" if page > 1 else sale_url
            soup = self._fetch(page_url, referer=self.base_url)
            if not soup:
                logger.warning(f"[{self.city_name}] 安居客二手房第 {page} 页请求失败，停止翻页")
                break

            cards = soup.select(".list-item, .li-itemmod, .property-content")
            if not cards:
                cards = soup.select(".houseList li, .list-content .li-info")

            page_count = 0
            for card in cards:
                parsed = self._parse_sale_card(card)
                if parsed:
                    all_listings.append(parsed)
                    page_count += 1

            logger.info(f"[{self.city_name}] 安居客二手房 第{page}页 → 解析 {page_count} 条")

            if page_count == 0:
                break

            self._random_delay()

        return all_listings

    # ==================== 租金 ====================
    def _parse_rental_card(self, card) -> Optional[Dict]:
        """解析租金列表卡片"""
        try:
            # 小区名
            community_el = card.select_one(".zu-info .comm-address, .details-item a, .house-title a")
            if not community_el:
                return None
            community_name = community_el.get_text(strip=True)

            # 月租金
            price_el = card.select_one(".zu-side .price, .price-det .total-price")
            monthly_rent = None
            if price_el:
                price_text = price_el.get_text(strip=True)
                price_match = re.search(r"[\d.]+", price_text)
                if price_match:
                    monthly_rent = float(price_match.group())

            # 面积
            area_el = card.select_one(".details-item, .zu-info")
            area = None
            if area_el:
                area_text = area_el.get_text(strip=True)
                area_match = re.search(r"([\d.]+)㎡", area_text)
                if not area_match:
                    area_match = re.search(r"([\d.]+)平米", area_text)
                if area_match:
                    area = float(area_match.group(1))

            return {
                "community": community_name,
                "monthly_rent": monthly_rent,
                "area_sqm": area,
            }
        except Exception as e:
            logger.debug(f"解析安居客租金卡片异常: {e}")
            return None

    def fetch_rental_listings(self) -> List[Dict]:
        """分页爬取租金列表"""
        all_listings = []
        rent_url = f"{self.base_url}/rent/"

        for page in range(1, config.MAX_PAGES_PER_CITY + 1):
            page_url = f"{rent_url}p{page}/" if page > 1 else rent_url
            soup = self._fetch(page_url, referer=self.base_url)
            if not soup:
                logger.warning(f"[{self.city_name}] 安居客租金第 {page} 页请求失败，停止翻页")
                break

            cards = soup.select(".list-item, .li-itemmod")
            if not cards:
                cards = soup.select(".houseList li, .list-content .zu-itemmod")

            page_count = 0
            for card in cards:
                parsed = self._parse_rental_card(card)
                if parsed:
                    all_listings.append(parsed)
                    page_count += 1

            logger.info(f"[{self.city_name}] 安居客租金 第{page}页 → 解析 {page_count} 条")

            if page_count == 0:
                break

            self._random_delay()

        return all_listings
