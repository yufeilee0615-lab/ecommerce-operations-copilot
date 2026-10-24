"""Reproducible synthetic data. Run: .venv/bin/python -m src.generate_data."""
from pathlib import Path
import random
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'


def generate(seed=42):
    rng = random.Random(seed)
    names = [('无线耳机','数码',12900), ('便携音箱','数码',8900),
             ('保温杯','家居',3900), ('收纳盒','家居',2500),
             ('瑜伽垫','运动',5900), ('运动水壶','运动',2900),
             ('帆布包','服饰',4900), ('棒球帽','服饰',3500)]
    products = pd.DataFrame([dict(sku=f'SKU-{i+1:03d}', product=n, category=c, price_cents=p)
                             for i, (n,c,p) in enumerate(names)])
    orders, traffic = [], []
    for date in pd.date_range('2026-08-14', '2026-10-12'):
        for p in products.itertuples():
            sessions = rng.randint(150, 260)
            probability, refund_probability = .065, .035
            # Deliberately planted scenarios in the final seven days.
            if date >= pd.Timestamp('2026-10-06'):
                if p.sku == 'SKU-001':
                    probability = .019
                if p.sku == 'SKU-003':
                    refund_probability = .24
                if p.sku == 'SKU-005':
                    sessions = int(sessions * .45)
            traffic.append(dict(date=date, sku=p.sku, sessions=sessions))
            for _ in range(sessions):
                if rng.random() < probability:
                    quantity = rng.choices([1,2,3], weights=[85,12,3])[0]
                    orders.append(dict(order_id=f'ORD-{len(orders)+1:06d}', date=date,
                                       sku=p.sku, quantity=quantity, amount_cents=p.price_cents*quantity,
                                       refunded=rng.random() < refund_probability))
    return products, pd.DataFrame(orders), pd.DataFrame(traffic)


if __name__ == '__main__':
    DATA_DIR.mkdir(exist_ok=True)
    for name, frame in zip(['products','orders','traffic'], generate()):
        frame.to_csv(DATA_DIR / f'{name}.csv', index=False, encoding='utf-8-sig')
        print(f'{name}: {len(frame):,} rows')
