#!/usr/bin/env python3
"""
房产租售比挖掘系统 - 主入口
遍历目标城市，双源抓取、合并、计算、报告
"""

import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict

import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

import config
from scrapers import KeScraper, AnjukeScraper, XiaohongshuScraper
from merger import merge
from calculator import calculate, get_qualified
from reporter import generate_excel, print_console_report, print_xhs_report

console = Console()

# ---------- 日志配置 ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("rental_miner.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")


def scrape_city(city_name: str, use_anjuke: bool = True) -> pd.DataFrame:
    """
    单城市完整流程：爬取 → 合并 → 计算
    返回该城市的 DataFrame
    """
    logger.info(f"========= {city_name} 开始处理 =========")
    ke_data = {"sales": [], "rentals": []}
    anjuke_data = {"sales": [], "rentals": []}

    try:
        # ----- 贝壳 -----
        ke = KeScraper(city_name)
        ke_data = ke.scrape()
    except Exception as e:
        logger.error(f"[{city_name}] 贝壳爬取异常: {e}")

    if use_anjuke:
        try:
            # ----- 安居客 -----
            aj = AnjukeScraper(city_name)
            anjuke_data = aj.scrape()
        except Exception as e:
            logger.error(f"[{city_name}] 安居客爬取异常: {e}")

    # ----- 合并 -----
    if not ke_data["sales"] and not anjuke_data["sales"]:
        logger.warning(f"[{city_name}] 无有效数据，跳过")
        return pd.DataFrame()

    try:
        df = merge(city_name, ke_data, anjuke_data)
    except Exception as e:
        logger.error(f"[{city_name}] 合并异常: {e}")
        return pd.DataFrame()

    # ----- 计算租售比 -----
    try:
        df = calculate(df)
    except Exception as e:
        logger.error(f"[{city_name}] 计算异常: {e}")
        return pd.DataFrame()

    qualified = get_qualified(df)
    logger.info(
        f"[{city_name}] 完成: {len(df)} 条 | 达标 {len(qualified)} 条 "
        f"| 最高租售比 {qualified['年租售比(%)'].max() if len(qualified) > 0 else 'N/A'}%"
    )

    return df


def main():
    parser = argparse.ArgumentParser(
        description="房产租售比挖掘系统 - 一二线城市房价租金数据抓取与分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                          # 全量 12 城市
  python main.py --cities 成都 杭州 青岛  # 指定城市
  python main.py --threshold 3.5          # 自定义租售比阈值
  python main.py --max-price 200          # 总价上限 200 万
  python main.py --no-anjuke              # 仅贝壳数据源
  python main.py --pages 5                # 每城最大页数
        """,
    )
    parser.add_argument(
        "--cities", nargs="+",
        help="指定城市（默认全量12城）",
    )
    parser.add_argument(
        "--threshold", type=float, default=config.YIELD_THRESHOLD,
        help=f"租售比最低阈值（默认 {config.YIELD_THRESHOLD}%%）",
    )
    parser.add_argument(
        "--max-price", type=float, default=config.MAX_TOTAL_PRICE_WAN,
        help="总价上限（万元）",
    )
    parser.add_argument(
        "--no-anjuke", action="store_true",
        help="禁用安居客数据源（仅使用贝壳）",
    )
    parser.add_argument(
        "--pages", type=int, default=config.MAX_PAGES_PER_CITY,
        help=f"每城市最大爬取页数（默认 {config.MAX_PAGES_PER_CITY}）",
    )
    parser.add_argument(
        "--output-dir", type=str, default=config.OUTPUT_DIR,
        help=f"报告输出目录（默认 {config.OUTPUT_DIR}）",
    )
    parser.add_argument(
        "--with-xhs", action="store_true",
        help="启用小红书辅助验证（对达标小区进行社交媒体交叉验证）",
    )

    args = parser.parse_args()

    # 更新全局配置
    config.YIELD_THRESHOLD = args.threshold
    config.MAX_TOTAL_PRICE_WAN = args.max_price
    config.MAX_PAGES_PER_CITY = args.pages

    # 选择城市
    if args.cities:
        invalid = set(args.cities) - set(config.CITIES.keys())
        if invalid:
            console.print(f"[red]错误: 不支持的城市 {invalid}[/red]")
            console.print(f"可用城市: {list(config.CITIES.keys())}")
            sys.exit(1)
        cities = args.cities
    else:
        cities = list(config.CITIES.keys())

    use_anjuke = not args.no_anjuke
    use_xhs = args.with_xhs

    # ==================== 开始 ====================
    console.print()
    data_sources = "贝壳找房"
    if use_anjuke:
        data_sources += " + 安居客"
    if use_xhs:
        data_sources += " + 小红书验证"

    console.print(Panel.fit(
        f"[bold cyan]🏠 房产租售比挖掘系统[/bold cyan]\n"
        f"目标城市: {', '.join(cities)}\n"
        f"范围: 仅核心城区\n"
        f"数据源: {data_sources}\n"
        f"最低租售比: {config.YIELD_THRESHOLD}%\n"
        f"总价上限: {'不限' if config.MAX_TOTAL_PRICE_WAN is None else f'{config.MAX_TOTAL_PRICE_WAN}万'}\n"
        f"每城最大页数: {config.MAX_PAGES_PER_CITY}",
        border_style="cyan",
    ))
    console.print()

    # ==================== 城市遍历 ====================
    all_dfs: List[pd.DataFrame] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]爬取中...", total=len(cities))

        for city in cities:
            progress.update(task, description=f"[cyan]正在处理: {city}")
            try:
                df = scrape_city(city, use_anjuke=use_anjuke)
                if not df.empty:
                    all_dfs.append(df)
            except Exception as e:
                logger.error(f"[{city}] 处理失败: {e}")
            progress.advance(task)

    # ==================== 汇总 ====================
    if not all_dfs:
        console.print("[red]没有获取到任何有效数据[/red]")
        sys.exit(1)

    df_all = pd.concat(all_dfs, ignore_index=True)

    # 重新计算（确保全局配置一致）
    df_all = calculate(df_all)

    # ==================== 小红书验证 ====================
    xhs_results = []
    if use_xhs:
        console.print()
        console.print("[bold magenta]📕 小红书辅助验证中...[/bold magenta]")
        try:
            xhs = XiaohongshuScraper()
            qualified = get_qualified(df_all)

            if len(qualified) > 0:
                # 取每城 top N 小区做验证
                top_n = min(config.XHS_MAX_VERIFY_COMMUNITIES, len(qualified))
                to_verify = qualified.head(top_n)

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        "[magenta]小红书搜索...", total=len(to_verify)
                    )
                    for _, row in to_verify.iterrows():
                        city = row["城市"]
                        community = row["小区名"]
                        progress.update(
                            task,
                            description=f"[magenta]搜索: {community}",
                        )
                        r = xhs.search_community(city, community)
                        xhs_results.append(r)
                        progress.advance(task)

                # 将 XHS 数据合并到 df_all
                xhs_map = {}
                for r in xhs_results:
                    key = r["community"].lower().strip()
                    xhs_map[key] = r

                df_all["小红书笔记数"] = df_all.apply(
                    lambda row: xhs_map.get(
                        str(row.get("小区名", "")).lower().strip(), {}
                    ).get("total_notes", 0),
                    axis=1,
                )
                df_all["小红书热度"] = df_all.apply(
                    lambda row: xhs_map.get(
                        str(row.get("小区名", "")).lower().strip(), {}
                    ).get("heat_score", 0),
                    axis=1,
                )
                df_all["小红书置信度"] = df_all.apply(
                    lambda row: xhs_map.get(
                        str(row.get("小区名", "")).lower().strip(), {}
                    ).get("confidence", 0.0),
                    axis=1,
                )
                df_all["小红书验证状态"] = df_all.apply(
                    lambda row: "已验证" if row["小红书笔记数"] > 0 else "未验证",
                    axis=1,
                )

                console.print(
                    f"[green]✅ 小红书验证完成: {len(xhs_results)} 个小区[/green]"
                )
            else:
                console.print("[yellow]⚠ 无达标小区，跳过小红书验证[/yellow]")
        except Exception as e:
            logger.error(f"小红书验证异常: {e}")
            console.print(f"[red]❌ 小红书验证失败: {e}[/red]")

    # ==================== 报告输出 ====================
    # Excel
    try:
        excel_path = generate_excel(df_all, output_dir=args.output_dir)
        console.print(f"[green]✅ Excel 报告: {excel_path}[/green]")
    except Exception as e:
        logger.error(f"Excel 生成失败: {e}")
        console.print(f"[red]❌ Excel 生成失败: {e}[/red]")

    # 控制台摘要
    print_console_report(df_all)

    # 小红书验证报告（如果有）
    if use_xhs:
        print_xhs_report(df_all)

    return df_all


if __name__ == "__main__":
    main()
