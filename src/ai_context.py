import json

import pandas as pd

from src.analytics import metrics, select_period, sku_comparison


def build_ai_context(products, orders, traffic):
    # 最近7天以数据截止日期为准，不使用电脑今天的日期
    end = traffic["date"].max()
    start = end - pd.Timedelta(days=6)
    previous_end = start - pd.Timedelta(days=1)
    previous_start = start - pd.Timedelta(days=7)
    skus = products["sku"].tolist()

    current_orders, current_traffic = select_period(
        orders, traffic, start, end, skus
    )
    previous_orders, previous_traffic = select_period(
        orders, traffic, previous_start, previous_end, skus
    )

    current = metrics(current_orders, current_traffic)
    previous = metrics(previous_orders, previous_traffic)

    comparison = sku_comparison(
        products,
        current_orders,
        current_traffic,
        previous_orders,
        previous_traffic,
    )

    summary = {
        "数据性质": "模拟数据，不代表真实店铺",
        "统计范围": "全部商品，不受看板筛选影响",
        "本期": f"{start:%Y-%m-%d} 至 {end:%Y-%m-%d}",
        "对比期": (
            f"{previous_start:%Y-%m-%d} 至 "
            f"{previous_end:%Y-%m-%d}"
        ),
        "本期指标": current,
        "上期指标": previous,
        "GMV环比百分数": (
            round((current["gmv"] / previous["gmv"] - 1) * 100, 2)
            if previous["gmv"] else None
        ),
    }

    return (
        "以下数据由项目中的 Python 分析函数计算。\n"
        "金额单位为 AUD。汇总中的 refund_rate 和 conversion "
        "是小数比例，例如0.07表示7%。"
        "商品表中以_pct结尾的字段已经是百分数，不能再乘100；"
        "conversion_change_pp单位是百分点。\n"
        "GMV包含后来退款的订单，不等于净销售额或利润。"
        "退款按原订单日期归属。null表示无法计算。\n"
        "alert是规则提示，不能证明业务原因。"
        "未提供评价原文、退款原因、成本或物流记录。\n\n"
        + json.dumps(summary, ensure_ascii=False, allow_nan=False)
        + "\n\n商品分析明细：\n"
        + comparison.round(4).to_json(
            orient="records", force_ascii=False
        )
    )