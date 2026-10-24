import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


class AppTests(unittest.TestCase):
    def test_filters_and_pages(self):
        at=AppTest.from_file(APP,default_timeout=30).run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.metric),5)
        initial=at.metric[0].value
        at.selectbox(key='period').set_value(30).run()
        self.assertFalse(at.exception)
        self.assertNotEqual(at.metric[0].value,initial)
        at.multiselect(key='categories').set_value([]).run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.metric),0)
        at.multiselect(key='categories').set_value(['数码']).run()
        self.assertFalse(at.exception)
        at.radio(key='page').set_value('SKU Analysis').run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.dataframe[0].value),2)
        at.checkbox(key='only_alerts').check().run()
        self.assertFalse(at.exception)
                # 检查运营周报页面
        at.radio(key='page').set_value('Weekly Report').run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.metric), 4)

        # 未筛选时，显示全部 8 个商品
        self.assertEqual(len(at.dataframe[0].value), 8)

        # 勾选退款告警后，只显示保温杯
        at.checkbox[0].check().run()
        self.assertFalse(at.exception)
        self.assertEqual(
            at.dataframe[0].value["sku"].tolist(),
            ["SKU-003"]
        )

        # 返回运营看板仍可正常显示
        at.radio(key='page').set_value('Dashboard').run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.metric), 5)
