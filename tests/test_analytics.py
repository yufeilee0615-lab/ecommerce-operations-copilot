import unittest
import pandas as pd
from src.analytics import metrics, daily_metrics, sku_comparison, select_period
from src.generate_data import generate


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.orders = pd.DataFrame({'order_id':['1','2'], 'date':pd.to_datetime(['2026-10-01']*2),
                                    'sku':['A','A'], 'amount_cents':[1000,3000], 'refunded':[False,True]})
        self.traffic = pd.DataFrame({'date':pd.to_datetime(['2026-10-01']), 'sku':['A'], 'sessions':[100]})

    def test_money_and_weighted_rates(self):
        result = metrics(self.orders,self.traffic)
        self.assertEqual(result['gmv'],40)
        self.assertEqual(result['net_sales'],10)
        self.assertEqual(result['aov'],20)
        self.assertEqual(result['conversion'],.02)
        self.assertEqual(result['refund_rate'],.5)

    def test_empty_and_zero_order_dates(self):
        empty = self.orders.iloc[:0]
        self.assertIsNone(metrics(empty,self.traffic.iloc[:0])['conversion'])
        self.assertEqual(metrics(empty,self.traffic)['conversion'],0)
        self.assertIsNone(metrics(empty,self.traffic)['aov'])
        daily = daily_metrics(self.orders,self.traffic,'2026-10-01','2026-10-03')
        self.assertEqual(daily.gmv.tolist(),[40,0,0])

    def test_generated_integrity_and_anomalies(self):
        products,orders,traffic = generate()
        self.assertFalse(orders.order_id.duplicated().any())
        pd.testing.assert_frame_equal(orders,generate()[1])
        counts=orders.groupby(['date','sku']).size()
        sessions=traffic.set_index(['date','sku']).sessions
        self.assertTrue((counts <= sessions.reindex(counts.index)).all())
        current=select_period(orders,traffic,'2026-10-06','2026-10-12',products.sku)
        prior=select_period(orders,traffic,'2026-09-29','2026-10-05',products.sku)
        result=sku_comparison(products,*current,*prior).set_index('sku')
        self.assertIn('转化率',result.loc['SKU-001','alert'])
        self.assertIn('退款率',result.loc['SKU-003','alert'])
        self.assertIn('GMV',result.loc['SKU-005','alert'])
        self.assertAlmostEqual(result.gmv_change.sum(),metrics(*current)['gmv']-metrics(*prior)['gmv'])

    def test_zero_baseline_and_minimum_sample(self):
        products=pd.DataFrame({'sku':['A'],'product':['test'],'category':['test']})
        result=sku_comparison(products,self.orders,self.traffic,self.orders.iloc[:0],self.traffic.iloc[:0]).iloc[0]
        self.assertTrue(pd.isna(result.gmv_change_pct))
        self.assertEqual(result.alert,'') # Two orders do not meet refund sample threshold.
