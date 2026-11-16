import csv
import io
import json
import zipfile
from src.extract import parse_zip,extract

def edinet_blob():
    lines=[
        ["要素ID","項目名","コンテキストID","相対年度","連結・個別","期間・時点","ユニットID","単位","値"],
        ["jppfs_cor:RealEstateForSale","販売用不動産","CurrentYearInstant","当期末","連結","時点","JPY","円","800"],
        ["jppfs_cor:RealEstateForSaleInProcess","仕掛販売用不動産","CurrentYearInstant","当期末","連結","時点","JPY","円","200"],
        ["jppfs_cor:CostOfSales","売上原価","CurrentYearDuration","当期","連結","期間","JPY","円","600"],
        ["jppfs_cor:NetSales","売上高","CurrentYearDuration","当期","連結","期間","JPY","円","900"],
        ["jppfs_cor:NetSales","個別売上高","CurrentYearDuration_NonConsolidatedMember","当期","個別","期間","JPY","円","99000"],
    ]
    s=io.StringIO()
    w=csv.writer(s,delimiter="\t");w.writerows(lines)
    f=io.BytesIO()
    with zipfile.ZipFile(f,"w") as z:
        z.writestr("XBRL_TO_CSV/jpcrp030000-asr_test.csv",s.getvalue().encode("utf-16"))
    return f.getvalue()

def test_parse_official_edinet_layout():
    result=parse_zip(edinet_blob())
    assert result[("RealEstateForSale","CurrentYearInstant")]=={800}
    assert result[("NetSales","CurrentYearDuration")]=={900}

def test_machine_extracted_property_inventory_is_flagged():
    doc={"ticker":"2975","company":"Sample","period_end":"2025-11-30","doc_type_code":"120","doc_id":"S1"}
    row=extract(doc,edinet_blob())
    assert int(row["inventory_jpy"])==1000
    assert int(row["revenue_jpy"])==900
    audit=json.loads(row["audit_note"])
    assert audit["status"]=="MACHINE_EXTRACTED_UNREVIEWED"
    assert audit["inventory_definition"]=="SUM_DISCLOSED_REAL_ESTATE_COMPONENTS_NOT_TOTAL_INVENTORIES"

def test_interim_document_not_used_as_annual():
    doc={"ticker":"2975","company":"Sample","period_end":"2026-11-30","doc_type_code":"160","doc_id":"S2"}
    assert extract(doc,edinet_blob()) is None
