from pathlib import Path

import pandas as pd

# 找到当前项目文件夹
PROJECT_DIR = Path(__file__).resolve().parent.parent

# 读取模拟订单数据
orders = pd.read_csv(PROJECT_DIR / "data" / "orders.csv")

# 显示前 5 笔订单
print("前 5 笔订单：")
print(orders.head())

# 查看一共有多少笔订单
print("\n订单总数：", len(orders))

# 查看订单表有哪些字段
print("\n订单字段：", orders.columns.tolist())
# 计算 GMV：订单金额求和，再把澳分换算为澳元
gmv = orders["amount_cents"].sum() / 100

print(f"\n总 GMV：AUD {gmv:,.2f}")
# 统计不同订单号的数量
total_orders = orders["order_id"].nunique()

# 客单价 = GMV ÷ 订单量
average_order_value = gmv / total_orders if total_orders > 0 else 0

print(f"\n订单量：{total_orders:,}")
print(f"客单价：AUD {average_order_value:,.2f}")
# 读取商品流量数据
traffic = pd.read_csv(PROJECT_DIR / "data" / "traffic.csv")

# 汇总商品访问次数
total_sessions = traffic["sessions"].sum()

# 转化率 = 订单量 ÷ 商品访问次数
if total_sessions > 0:
    conversion_rate = total_orders / total_sessions
    print(f"\n商品访问次数：{total_sessions:,}")
    print(f"商品访问转化率：{conversion_rate:.2%}")
else:
    print("\n没有访问数据，无法计算转化率")

# 筛选已退款的订单
refunded_orders = orders[orders["refunded"] == True]

# 计算退款订单数和退款金额
refund_count = refunded_orders["order_id"].nunique()
refund_amount = refunded_orders["amount_cents"].sum() / 100

# 净销售额 = GMV - 退款金额
net_sales = gmv - refund_amount

print(f"\n退款订单数：{refund_count:,}")
print(f"退款金额：AUD {refund_amount:,.2f}")
print(f"净销售额：AUD {net_sales:,.2f}")

if total_orders > 0:
    refund_rate = refund_count / total_orders
    print(f"退款率：{refund_rate:.2%}")
else:
    print("没有订单，无法计算退款率")

# 按 SKU 分组，分别计算订单量、销售件数和成交金额
sku_summary = orders.groupby("sku").agg(
    order_count=("order_id", "nunique"),
    units_sold=("quantity", "sum"),
    gmv_cents=("amount_cents", "sum")
).reset_index()

# 将澳分换算为澳元
sku_summary["gmv_aud"] = sku_summary["gmv_cents"] / 100

# 按 GMV 从高到低排列
sku_summary = sku_summary.sort_values("gmv_aud", ascending=False)

print("\n商品 GMV 排名（含后续退款订单）：")
print(
    sku_summary[["sku", "order_count", "units_sold", "gmv_aud"]]
    .to_string(index=False)
)
# 读取商品资料
products = pd.read_csv(PROJECT_DIR / "data" / "products.csv")

# 用 SKU 编号，把商品名称和品类匹配到排名表
sku_report = sku_summary.merge(
    products[["sku", "product", "category"]],
    on="sku",
    how="left",
    validate="one_to_one"
)

# 按顺序展示需要的字段
sku_report = sku_report[
    ["sku", "product", "category", "order_count", "units_sold", "gmv_aud"]
]

print("\n带商品名称的 GMV 排名：")
print(sku_report.to_string(index=False))
# 把日期文字转换成日期类型，方便比较和计算
orders["date"] = pd.to_datetime(orders["date"])

# 以数据中的最后一天为截止日期
end_date = orders["date"].max()
start_date = end_date - pd.Timedelta(days=6)

# 筛选这 7 天内的订单，包含开始和结束日期
recent_orders = orders[
    orders["date"].between(start_date, end_date)
]

recent_gmv = recent_orders["amount_cents"].sum() / 100
recent_order_count = recent_orders["order_id"].nunique()

print(f"\n统计期间：{start_date:%Y-%m-%d} 至 {end_date:%Y-%m-%d}")
print(f"最近 7 天订单量：{recent_order_count:,}")
print(f"最近 7 天 GMV：AUD {recent_gmv:,.2f}")
# 找到前一个 7 天周期
previous_end = start_date - pd.Timedelta(days=1)
previous_start = previous_end - pd.Timedelta(days=6)

# 筛选前 7 天的订单
previous_orders = orders[
    orders["date"].between(previous_start, previous_end)
]

previous_gmv = previous_orders["amount_cents"].sum() / 100

print(f"\n对比期间：{previous_start:%Y-%m-%d} 至 {previous_end:%Y-%m-%d}")
print(f"前 7 天 GMV：AUD {previous_gmv:,.2f}")

# 增长率 =（本期金额 - 上期金额）÷ 上期金额
if previous_gmv > 0:
    gmv_growth = (recent_gmv - previous_gmv) / previous_gmv
    print(f"GMV 环比变化：{gmv_growth:+.2%}")
else:
    print("上期 GMV 为零，无法计算增长率")
# 分别计算每个 SKU 在本期、上期的 GMV
current_sku_gmv = recent_orders.groupby("sku")["amount_cents"].sum() / 100
previous_sku_gmv = previous_orders.groupby("sku")["amount_cents"].sum() / 100

# 按 SKU 对齐两期数据；某期没有订单的商品记为 0
sku_change = pd.concat(
    [current_sku_gmv, previous_sku_gmv],
    axis=1,
    keys=["current_gmv", "previous_gmv"]
).fillna(0)

# 计算金额变化：负数代表下降
sku_change["gmv_change"] = (
    sku_change["current_gmv"] - sku_change["previous_gmv"]
)

# 加上商品名称
sku_change = sku_change.reset_index().merge(
    products[["sku", "product"]],
    on="sku",
    how="left",
    validate="one_to_one"
)

# 金额减少最多的商品排在最前面
sku_change = sku_change.sort_values("gmv_change")

print("\n各商品 GMV 变化（单位：AUD）：")
print(
    sku_change[
        ["sku", "product", "previous_gmv", "current_gmv", "gmv_change"]
    ].to_string(index=False)
)
# 将流量表的日期转换成日期类型
traffic["date"] = pd.to_datetime(traffic["date"])

# 先分析无线耳机
target_sku = "SKU-005"

# 分别检查上期和本期
# 保存两期分析结果
period_results = {}

# 分别检查上期和本期
for label, period_start, period_end in [
    ("上期", previous_start, previous_end),
    ("本期", start_date, end_date),
]:
    sku_orders = orders[
        (orders["sku"] == target_sku)
        & orders["date"].between(period_start, period_end)
    ]

    sku_traffic = traffic[
        (traffic["sku"] == target_sku)
        & traffic["date"].between(period_start, period_end)
    ]

    order_count = sku_orders["order_id"].nunique()
    sessions = sku_traffic["sessions"].sum()

    period_results[label] = {
        "orders": order_count,
        "sessions": sessions,
        "conversion": order_count / sessions if sessions > 0 else None,
    }

    print(f"\n{label} · {target_sku}")
    print(f"商品访问次数：{sessions:,}")
    print(f"订单量：{order_count:,}")

    if sessions > 0:
        conversion = order_count / sessions
        print(f"转化率：{conversion:.2%}")
    else:
        print("没有访问数据，无法计算转化率")

# 取出两期结果
previous = period_results["上期"]
current = period_results["本期"]

print("\n转化率异常检查：")

if previous["sessions"] < 200 or current["sessions"] < 200:
    print("访问量不足，暂不进行异常判断")
else:
    # 小数差乘以 100，换算成百分点
    conversion_change_pp = (
        current["conversion"] - previous["conversion"]
    ) * 100

    print(f"转化率变化：{conversion_change_pp:+.2f} 个百分点")

    if conversion_change_pp <= -1:
        print(f"告警：{target_sku} 转化率下降至少 1 个百分点")
        print("建议检查价格、商品页、流量来源和评价，具体原因待验证")
    else:
        print("未触发转化率下降告警")

# 检查商品访问量是否明显下降
print("\n流量异常检查：")

if previous["sessions"] < 200:
    print("上期访问量不足，暂不进行流量异常判断")
else:
    traffic_change = (
        current["sessions"] - previous["sessions"]
    ) / previous["sessions"]

    print(f"商品访问量变化：{traffic_change:+.2%}")

    if traffic_change <= -0.20:
        print(f"告警：{target_sku} 商品访问量下降至少 20%")
        print("建议检查广告投放、活动变化和流量渠道，具体原因待验证")
    else:
        print("未触发流量下降告警")

# 检查保温杯最近 7 天的退款情况
refund_sku = "SKU-003"

product_orders = recent_orders[
    recent_orders["sku"] == refund_sku
]

product_order_count = product_orders["order_id"].nunique()

product_refund_count = product_orders.loc[
    product_orders["refunded"] == True, "order_id"
].nunique()

print(f"\n退款异常检查 · {refund_sku}")
print(f"本期订单量：{product_order_count:,}")
print(f"退款订单量：{product_refund_count:,}")

if product_order_count < 20:
    print("订单量不足 20 单，暂不进行退款异常判断")
else:
    product_refund_rate = product_refund_count / product_order_count
    print(f"退款率：{product_refund_rate:.2%}")

    if product_refund_rate >= 0.10:
        print("告警：退款率达到或超过 10%")
        print("建议检查退款原因、质量和物流记录，具体原因待验证")
    else:
        print("未触发退款率告警")

# 定义一个可重复使用的退款检查函数
def check_refund(sku):
    sku_orders = recent_orders[recent_orders["sku"] == sku]

    order_count = sku_orders["order_id"].nunique()
    refund_count = sku_orders.loc[
        sku_orders["refunded"] == True, "order_id"
    ].nunique()

    if order_count < 20:
        return f"{sku}：订单不足 20 单，暂不判断"

    refund_rate = refund_count / order_count

    if refund_rate >= 0.10:
        return f"{sku}：退款率 {refund_rate:.2%}，触发退款告警"

    return f"{sku}：退款率 {refund_rate:.2%}，未触发退款告警"


# 调用函数，检查保温杯
print("\n函数检查结果：")
print(check_refund("SKU-003"))
# 依次检查商品表中的所有 SKU
print("\n全部商品退款检查：")

for sku in products["sku"].unique():
    result = check_refund(sku)
    print(result)

# 用列表收集每个商品的检查结果
refund_results = []

for sku in products["sku"].unique():
    refund_results.append({
        "sku": sku,
        "check_result": check_refund(sku),
    })

# 把列表转换成表格，并加上商品名称
refund_report = pd.DataFrame(refund_results)

refund_report = refund_report.merge(
    products[["sku", "product"]],
    on="sku",
    how="left",
    validate="one_to_one"
)

# 调整列的显示顺序
refund_report = refund_report[
    ["sku", "product", "check_result"]
]

print("\n商品退款检查表：")
print(refund_report.to_string(index=False))

# 创建专门存放分析报告的文件夹
REPORT_DIR = PROJECT_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# 文件名带上统计期间
output_path = REPORT_DIR / (
    f"refund_report_{start_date:%Y%m%d}_{end_date:%Y%m%d}.csv"
)

# 保存退款检查表
refund_report.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig"
)

print(f"\n退款检查表已保存到：{output_path}")

# 导入刚才写在另一个文件中的函数
from refund_analysis import analyze_refund

# 用最近 7 天的订单检查保温杯
refund_result = analyze_refund(recent_orders, "SKU-003")

print("\n新函数检查结果：")
print(f"商品编号：{refund_result['sku']}")
print(f"订单量：{refund_result['order_count']}")
print(f"退款订单量：{refund_result['refund_count']}")

if refund_result["refund_rate"] is not None:
    print(f"退款率：{refund_result['refund_rate']:.2%}")
else:
    print("退款率：无订单，无法计算")

print(f"检查状态：{refund_result['status']}")

# 收集全部商品的分析结果
structured_results = []

for sku in products["sku"].unique():
    result = analyze_refund(recent_orders, sku)
    structured_results.append(result)

# 转成表格，再匹配商品名称
structured_report = pd.DataFrame(structured_results)

structured_report = structured_report.merge(
    products[["sku", "product"]],
    on="sku",
    how="left",
    validate="one_to_one"
)

# 按退款率从高到低排序
structured_report = structured_report.sort_values(
    "refund_rate",
    ascending=False,
    na_position="last"
)

print("\n全部商品退款分析：")
print(
    structured_report[
        ["sku", "product", "order_count",
         "refund_count", "refund_rate", "status"]
    ].to_string(
        index=False,
        formatters={"refund_rate": "{:.2%}".format}
    )
)

# 整理新版报告的列顺序
structured_report = structured_report[
    ["sku", "product", "order_count",
     "refund_count", "refund_rate", "status"]
]

# 保存为独立的结构化报告
structured_path = REPORT_DIR / (
    f"refund_structured_{start_date:%Y%m%d}_{end_date:%Y%m%d}.csv"
)

structured_report.to_csv(
    structured_path,
    index=False,
    encoding="utf-8-sig"
)

print(f"\n新版退款报告已保存到：{structured_path}")

# 生成运营周报正文
weekly_refunds = int(structured_report["refund_count"].sum())
weekly_refund_rate = (
    weekly_refunds / recent_order_count
    if recent_order_count > 0
    else None
)

growth_text = (
    f"{(recent_gmv / previous_gmv - 1):+.2%}"
    if previous_gmv > 0
    else "无法计算（上期 GMV 为零）"
)

refund_rate_text = (
    f"{weekly_refund_rate:.2%}"
    if weekly_refund_rate is not None
    else "无法计算（本期无订单）"
)

# 逐个列出商品的 GMV 变化
product_lines = []
for row in sku_change.itertuples(index=False):
    product_lines.append(
        f"- {row.sku} {row.product}："
        f"上期 AUD {row.previous_gmv:,.2f}，"
        f"本期 AUD {row.current_gmv:,.2f}，"
        f"变化 AUD {row.gmv_change:+,.2f}。"
    )

# 只列出触发退款告警的商品
refund_lines = []
for row in structured_report.itertuples(index=False):
    if row.status == "退款告警":
        refund_lines.append(
            f"- {row.sku} {row.product}："
            f"{int(row.order_count)} 单中退款 "
            f"{int(row.refund_count)} 单，"
            f"退款率 {row.refund_rate:.2%}。"
        )

weekly_text = "\n\n".join([
    "# 电商运营周报",
    f"本期：{start_date:%Y-%m-%d} 至 {end_date:%Y-%m-%d}",
    f"对比期：{previous_start:%Y-%m-%d} 至 "
    f"{previous_end:%Y-%m-%d}",
    "## 一、销售概览",
    f"本期订单量：{recent_order_count:,} 单。",
    f"本期 GMV：AUD {recent_gmv:,.2f}；"
    f"上期 GMV：AUD {previous_gmv:,.2f}；"
    f"环比变化：{growth_text}。",
    f"本期退款订单量：{weekly_refunds:,} 单；"
    f"整体退款率：{refund_rate_text}。",
    "## 二、商品 GMV 变化",
    "\n".join(product_lines) or "暂无商品销售数据。",
    "## 三、退款告警",
    "\n".join(refund_lines) or "本期未触发退款告警。",
    "## 四、建议排查事项",
    "- 对 GMV 减少较多的商品，对比访问量、转化率和客单价。",
    "- 对退款告警商品，核查退款原因、质量和物流记录。",
    "- 记录排查证据、处理措施和负责人，下期复查指标。",
    "## 五、统计口径",
    "本报告使用模拟数据，由固定模板生成，未接入 AI。"
    "GMV 包含后续全额退款的订单，不等于净销售额或利润。"
    "退款按原下单日期归属，每笔模拟订单只有一种商品。"
    "退款告警条件为本期至少 20 单且退款率达到 10%。"
    "商品金额变化用于描述变化贡献，不能证明业务原因。"
])

weekly_path = REPORT_DIR / (
    f"weekly_report_{start_date:%Y%m%d}_{end_date:%Y%m%d}.md"
)
weekly_path.write_text(weekly_text, encoding="utf-8")

print(f"\n运营周报已保存到：{weekly_path}")