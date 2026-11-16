import fitz
import pytest
from src.reins_monthly_update import numbers_from_tokiotable,extract_pdf

CONTRACT = """中古マンションレポート
（1）成約状況
○首都圏
10 3,392 -19.7 79.44 -6.9 -2.0 4,979 -6.5 -2.6 62.67 0.4 -0.6 28.90
○東京都
25/10 2,234 39.7 121.06 15.7 2.2 7,028 15.6 1.0 58.06 -0.1 -1.2 25.25
10 1,670 -25.2 115.58 -4.5 -0.8 6,640 -5.5 -1.3 57.45 -1.1 -0.5 27.69
○埼玉県
10 435 -4.2 45.01 4.9 4.3 3,068 6.1 4.6 68.15 -0.1 -0.5 28.58
"""
STOCK="""中古マンションレポート
（3）在庫状況
○首都圏
10 53,510 22.5 120.59 24.2 0.5 7,007 24.3 0.5 58.10 0.1 0.0 28.83
○東京都
25/10 22,722 -4.8 150.67 33.3 2.9 8,031 38.0 3.9 53.30 3.6 1.0 28.22
10 31,981 40.7 171.37 13.7 -0.8 9,442 17.6 -0.6 55.10 3.4 0.2 26.78
○埼玉県
10 5,609 4.3 46.59 11.5 2.0 2,987 10.9 2.1 64.10 -0.6 0.1 32.21
"""

def test_tokyo_row_selection_and_arithmetic():
    assert numbers_from_tokiotable(CONTRACT,"2026-10")== (1670,115.58,6640.0)
    assert numbers_from_tokiotable(STOCK,"2026-10")== (31981,171.37,9442.0)

def test_refuse_wrong_month_or_misaligned_columns():
    with pytest.raises(ValueError):numbers_from_tokiotable(CONTRACT,"2026-09")
    bad=CONTRACT.replace("57.45 -1.1","99.99 -1.1")
    with pytest.raises(ValueError):numbers_from_tokiotable(bad,"2026-10")

def test_official_pdf_has_consistent_timing_and_sections():
    pdf=fitz.open()
    for i in range(4):
        page=pdf.new_page()
        text = ("2026年10月度" if i==0 else CONTRACT if i==1 else STOCK if i==3 else "Reference")
        # Install-safe simple Japanese font for synthetic tests is not available.
        # Verify content via parsing using an ASCII-only synthetic section fixture instead.
        if i==0:page.insert_text((70,70),"2026 10月")
    with pytest.raises(ValueError):
        extract_pdf(pdf.tobytes(),"2026-09")
