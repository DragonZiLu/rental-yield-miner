"""
报告输出模块
- Excel 报告（openpyxl）
- 控制台摘要（rich）
"""

import os
import logging
from datetime import datetime
from typing import List, Dict

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

import config

logger = logging.getLogger(__name__)
console = Console()


# ==================== Excel 样式 ====================
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_FONT = Font(name="微软雅黑", size=11, bold=True, color="FFFFFF")
GREEN_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")   # ≥5%
YELLOW_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")  # 4%~5%
NORMAL_FONT = Font(name="微软雅黑", size=10)
BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)
CENTER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _style_header(ws, headers: List[str]):
    """设置表头样式"""
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = CENTER_ALIGN
        cell.border = BORDER


def _auto_width(ws, min_width=8, max_width=30):
    """自适应列宽"""
    for col_cells in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col_cells[0].column)
        for cell in col_cells:
            if cell.value:
                # 中文字符占2个宽度
                val = str(cell.value)
                char_len = sum(2 if ord(c) > 127 else 1 for c in val)
                max_len = max(max_len, char_len)
        width = min(max(max_len + 2, min_width), max_width)
        ws.column_dimensions[col_letter].width = width


def _write_data_rows(ws, df: pd.DataFrame, start_row: int = 2):
    """写入数据行并设置样式"""
    for i, (_, row) in enumerate(df.iterrows()):
        row_num = start_row + i
        for col_idx, col_name in enumerate(df.columns, 1):
            value = row[col_name]
            # 处理 pandas 类型
            if pd.isna(value):
                value = None
            elif hasattr(value, "item"):
                value = value.item()

            cell = ws.cell(row=row_num, column=col_idx, value=value)
            cell.font = NORMAL_FONT
            cell.alignment = CENTER_ALIGN
            cell.border = BORDER

            # 租售比颜色标记
            yield_val = row.get("年租售比(%)")
            if yield_val is not None and not pd.isna(yield_val):
                if yield_val >= 5.0:
                    cell.fill = GREEN_FILL
                elif yield_val >= 4.0:
                    cell.fill = YELLOW_FILL


def _highlight_yield(ws, df: pd.DataFrame, start_row: int = 2,
                     yield_col_name: str = "年租售比(%)"):
    """为租售比列添加条件颜色"""
    if yield_col_name not in df.columns:
        return
    col_idx = list(df.columns).index(yield_col_name) + 1
    for i, (_, row) in enumerate(df.iterrows()):
        value = row[yield_col_name]
        if pd.isna(value) or value is None:
            continue
        cell = ws.cell(row=start_row + i, column=col_idx)
        if value >= 5.0:
            cell.fill = GREEN_FILL
        elif value >= 4.0:
            cell.fill = YELLOW_FILL


def generate_excel(df_all: pd.DataFrame, output_dir: str = None):
    """
    生成 Excel 报告

    Sheets:
        - 达标小区汇总: 租售比 ≥ 4%，降序
        - 城市对比: 各城市统计
        - 全量数据: 所有爬取小区
    """
    if output_dir is None:
        output_dir = config.OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    filename = config.OUTPUT_FILENAME.format(date=date_str)
    filepath = os.path.join(output_dir, filename)

    wb = Workbook()

    # ---------- Sheet 1: 达标小区 ----------
    ws1 = wb.active
    ws1.title = "达标小区汇总"

    qualified = df_all[df_all["是否达标"]].sort_values("年租售比(%)", ascending=False)

    display_cols = [
        "城市", "小区名", "区域", "建筑年代",
        "均价_综合(元/㎡)", "月租金_综合(元)", "总价估算(万元)",
        "年租售比(%)", "数据来源", "数据质量"
    ]
    available_cols = [c for c in display_cols if c in qualified.columns]

    _style_header(ws1, available_cols)
    if len(qualified) > 0:
        _write_data_rows(ws1, qualified[available_cols])

    ws1.freeze_panes = "A2"
    _auto_width(ws1)

    # ---------- Sheet 2: 城市对比 ----------
    ws2 = wb.create_sheet("城市对比")

    from calculator import get_summary_stats
    city_stats = []
    for city in df_all["城市"].unique():
        city_df = df_all[df_all["城市"] == city]
        total, q_count, rate, avg_y, max_y = get_summary_stats(city_df)
        city_stats.append({
            "城市": city,
            "小区总数": total,
            "达标小区数": q_count,
            "达标率(%)": rate,
            "平均租售比(%)": avg_y,
            "最高租售比(%)": max_y,
        })
    stats_df = pd.DataFrame(city_stats).sort_values("达标率(%)", ascending=False)

    stats_cols = list(stats_df.columns)
    _style_header(ws2, stats_cols)
    _write_data_rows(ws2, stats_df)

    ws2.freeze_panes = "A2"
    _auto_width(ws2)

    # ---------- Sheet 3: 全量数据 ----------
    ws3 = wb.create_sheet("全量数据")
    all_cols = list(df_all.columns)
    _style_header(ws3, all_cols)
    _write_data_rows(ws3, df_all)

    # 高亮租售比列
    _highlight_yield(ws3, df_all)

    ws3.freeze_panes = "A2"
    _auto_width(ws3)

    # ---------- Sheet 4: 小红书验证（如果有数据）----------
    xhs_cols = ["城市", "小区名", "年租售比(%)", "月租金_综合(元)",
                 "总价估算(万元)", "数据来源", "小红书笔记数",
                 "小红书热度", "小红书置信度", "小红书验证状态"]
    available_xhs = [c for c in xhs_cols if c in df_all.columns]
    if "小红书笔记数" in df_all.columns:
        ws4 = wb.create_sheet("小红书验证")
        xhs_df = df_all[df_all["小红书笔记数"] > 0][available_xhs].sort_values(
            "小红书置信度", ascending=False
        )
        if len(xhs_df) > 0:
            _style_header(ws4, available_xhs)
            _write_data_rows(ws4, xhs_df)
            _highlight_yield(ws4, xhs_df)
            ws4.freeze_panes = "A2"
            _auto_width(ws4)
        else:
            ws4.cell(row=1, column=1, value="暂无小红书验证数据")
            ws4.cell(row=1, column=1).font = HEADER_FONT

    # ---------- 保存 ----------
    wb.save(filepath)
    logger.info(f"Excel 报告已保存: {filepath}")
    return filepath


# ==================== 控制台报告 ====================
def print_console_report(df_all: pd.DataFrame):
    """
    打印控制台摘要报告（使用 rich）
    """

    from calculator import get_summary_stats, get_qualified

    total, q_count, rate, avg_y, max_y = get_summary_stats(df_all)
    cities_count = df_all["城市"].nunique()

    # 总览面板
    overview = Table(box=box.SIMPLE_HEAVY, show_header=False, title="📊 租售比挖掘报告")
    overview.add_column("指标", style="bold cyan")
    overview.add_column("数值", style="bold white")
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    overview.add_row("报告时间", report_date)
    overview.add_row("覆盖城市", f"{cities_count} 个")
    overview.add_row("总抓取小区", f"{total} 个")
    overview.add_row(f"达标 (≥{config.YIELD_THRESHOLD}%)", f"[bold green]{q_count}[/bold green] 个")
    overview.add_row("达标率", f"{rate}%")
    overview.add_row("平均租售比", f"{avg_y}%")
    overview.add_row("最高租售比", f"[bold yellow]{max_y}%[/bold yellow]")

    console.print()
    console.print(Panel(overview, title="Rental Yield Miner"))
    console.print()

    # Top 10 投资标的
    qualified = get_qualified(df_all)
    if len(qualified) > 0:
        top10 = qualified.head(10)

        table = Table(title="🏆 Top 10 投资标的", box=box.SIMPLE)
        table.add_column("排名", style="dim", width=5)
        table.add_column("城市", style="cyan")
        table.add_column("小区", style="bold white")
        table.add_column("区域", style="dim")
        table.add_column("租售比", style="bold yellow", justify="right")
        table.add_column("月租(元)", justify="right")
        table.add_column("总价(万)", justify="right")
        table.add_column("来源", width=10)

        for rank, (_, row) in enumerate(top10.iterrows(), 1):
            yield_val = row.get("年租售比(%)")
            yield_style = "[bold green]" if yield_val and yield_val >= 5 else ""
            yield_end = "[/bold green]" if yield_style else ""

            table.add_row(
                str(rank),
                str(row.get("城市", "")),
                str(row.get("小区名", ""))[:18],
                str(row.get("区域", ""))[:10],
                f"{yield_style}{yield_val}{yield_end}",
                str(row.get("月租金_综合(元)", "")),
                str(row.get("总价估算(万元)", "")),
                str(row.get("数据来源", "")),
            )

        console.print(table)
    else:
        console.print("[yellow]⚠ 暂无达标小区[/yellow]")
    console.print()


def print_xhs_report(df_all: pd.DataFrame):
    """打印小红书验证摘要"""
    if "小红书笔记数" not in df_all.columns:
        return

    verified = df_all[df_all["小红书笔记数"] > 0]
    if len(verified) == 0:
        console.print("[dim]📕 小红书: 无验证数据[/dim]")
        return

    high_conf = verified[verified["小红书置信度"] >= 0.5]

    console.print()
    table = Table(title="📕 小红书验证 Top 10（按置信度）", box=box.SIMPLE)
    table.add_column("排名", style="dim", width=5)
    table.add_column("城市", style="cyan")
    table.add_column("小区", style="bold white")
    table.add_column("租售比", style="bold yellow", justify="right")
    table.add_column("XHS笔记", justify="right")
    table.add_column("热度", justify="right")
    table.add_column("置信度", style="magenta", justify="right")

    for rank, (_, row) in enumerate(verified.head(10).iterrows(), 1):
        conf = row.get("小红书置信度", 0)
        conf_style = "[bold green]" if conf >= 0.5 else ""
        conf_end = "[/bold green]" if conf_style else ""

        table.add_row(
            str(rank),
            str(row.get("城市", "")),
            str(row.get("小区名", ""))[:18],
            str(row.get("年租售比(%)", "")),
            str(int(row.get("小红书笔记数", 0))),
            str(int(row.get("小红书热度", 0))),
            f"{conf_style}{conf:.2f}{conf_end}",
        )

    console.print(table)

    if len(high_conf) > 0:
        console.print(
            f"[green]✅ {len(high_conf)} 个小区在小红书获得高置信度验证 "
            f"(≥0.5)[/green]"
        )
    console.print()
