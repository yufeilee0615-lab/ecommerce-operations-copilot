def analyze_refund(orders, sku):
    # 筛选指定商品的订单
    sku_orders = orders[orders["sku"] == sku]

    order_count = sku_orders["order_id"].nunique()
    refund_count = sku_orders.loc[
        sku_orders["refunded"] == True, "order_id"
    ].nunique()

    # 没有订单时，退款率没有定义
    refund_rate = (
        refund_count / order_count
        if order_count > 0
        else None
    )

    # 订单不足时，不进行告警判断
    if order_count < 20:
        status = "样本不足"
    elif refund_rate >= 0.10:
        status = "退款告警"
    else:
        status = "未触发"

    # 返回分开的字段，方便后续生成表格
    return {
        "sku": sku,
        "order_count": order_count,
        "refund_count": refund_count,
        "refund_rate": refund_rate,
        "status": status,
    }