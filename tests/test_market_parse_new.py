"""行情解析测试（扩展：沪深300 / 黄金ETF，含 key 与涨跌幅计算）。"""
from collectors import market


def test_market_parse_with_new_codes():
    text = '''var hq_str_s_sh000300="沪深300,4684.9916,-5.9249,-0.13,1849123,60111915";
var hq_str_rt_hkHSI="HSI,恒生指数,25998.590,25937.490,26060.320,25647.660,25679.449,-258.040,-0.990,0.000";
var hq_str_gb_$inx="标普500指数,7753.1099,-0.06,2026-08-11 04:38:43,-4.5300,7751.7402";
var hq_str_sh518880="黄金ETF华安,9.126,9.103,9.023,9.144,9.020,9.023,9.024,479939656,4358883326.000,602900,9.023,237900,9.020,9.030,9.023";
'''
    rows = market.parse(text)
    assert len(rows) == 4
    hs = next(r for r in rows if r["key"] == "hs300")
    assert hs["name"] == "沪深300" and hs["price"] == "4684.9916" and hs["pct"] == "-0.13"
    hk = next(r for r in rows if r["key"] == "hsi")
    assert hk["change"] == "-258.040" and hk["pct"] == "-0.990"
    sp = next(r for r in rows if r["key"] == "spx")
    assert sp["price"] == "7753.1099"
    gold = next(r for r in rows if r["key"] == "gold_etf")
    assert gold["name"] == "黄金ETF华安" and gold["price"] == "9.023"
    assert abs(float(gold["change"]) - (-0.080)) < 0.001
    assert abs(float(gold["pct"]) - (-0.88)) < 0.02
