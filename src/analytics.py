"""Pure analysis functions. Money is stored as integer AUD cents."""
import pandas as pd


def select_period(orders, traffic, start, end, skus):
    def subset(frame):
        return frame.loc[frame.date.between(pd.Timestamp(start), pd.Timestamp(end)) & frame.sku.isin(skus)].copy()
    return subset(orders), subset(traffic)


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def metrics(orders, traffic):
    count = len(orders)
    cents = int(orders.amount_cents.sum())
    refunds = int(orders.refunded.sum())
    refund_cents = int(orders.loc[orders.refunded, 'amount_cents'].sum())
    sessions = int(traffic.sessions.sum())
    return dict(gmv=cents / 100, orders=count, sessions=sessions,
                conversion=ratio(count, sessions), aov=ratio(cents / 100, count),
                refund_rate=ratio(refunds, count), refunds=refunds,
                net_sales=(cents - refund_cents) / 100)


def daily_metrics(orders, traffic, start, end):
    days = pd.date_range(start, end, name='date')
    daily = orders.groupby('date').agg(amount_cents=('amount_cents', 'sum'), orders=('order_id', 'count'))
    daily = daily.reindex(days, fill_value=0)
    daily['gmv'] = daily.pop('amount_cents') / 100
    daily['sessions'] = traffic.groupby('date').sessions.sum().reindex(days, fill_value=0)
    return daily.reset_index()


def sku_comparison(products, current_orders, current_traffic, previous_orders, previous_traffic):
    rows = []
    for product in products.itertuples():
        sku = product.sku
        now = metrics(current_orders[current_orders.sku == sku], current_traffic[current_traffic.sku == sku])
        before = metrics(previous_orders[previous_orders.sku == sku], previous_traffic[previous_traffic.sku == sku])
        change = None if before['gmv'] == 0 else (now['gmv'] / before['gmv'] - 1) * 100
        conversion_pp = None if now['conversion'] is None or before['conversion'] is None else (now['conversion'] - before['conversion']) * 100
        reasons = []
        if before['orders'] >= 20 and change is not None and change <= -20:
            reasons.append('GMV 下降 ≥20%')
        if min(now['sessions'], before['sessions']) >= 200 and conversion_pp is not None and conversion_pp <= -1:
            reasons.append('转化率下降 ≥1 个百分点')
        if now['orders'] >= 20 and now['refund_rate'] >= .10:
            reasons.append('退款率 ≥10%')
        rows.append(dict(sku=sku, product=product.product, category=product.category,
                         gmv=now['gmv'], previous_gmv=before['gmv'], orders=now['orders'],
                         sessions=now['sessions'], gmv_change_pct=change,
                         conversion_pct=None if now['conversion'] is None else now['conversion'] * 100,
                         conversion_change_pp=conversion_pp,
                         refund_rate_pct=None if now['refund_rate'] is None else now['refund_rate'] * 100,
                         gmv_change=now['gmv'] - before['gmv'], alert='；'.join(reasons)))
    return pd.DataFrame(rows).sort_values('gmv_change')
