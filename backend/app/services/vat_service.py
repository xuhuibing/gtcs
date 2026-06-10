"""VAT/GST/消费税查询服务"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

# 国家 VAT/GST 默认税率（标准税率）
VAT_RATES = {
    "CN": {"tax_type": "VAT", "tax_name": "增值税", "rate": Decimal("0.13"), "notes": "一般商品13%; 农产品9%; 软件出口0%"},
    "VN": {"tax_type": "VAT", "tax_name": "Thuế GTGT", "rate": Decimal("0.10"), "notes": "标准10%; 部分商品优惠5%"},
    "TH": {"tax_type": "VAT", "tax_name": "ภาษีมูลค่าเพิ่ม", "rate": Decimal("0.07"), "notes": "标准7%"},
    "IN": {"tax_type": "IGST", "tax_name": "Integrated GST", "rate": Decimal("0.18"), "notes": "标准18%; 5%/12%/28%视商品类别"},
    "ID": {"tax_type": "VAT", "tax_name": "PPN", "rate": Decimal("0.11"), "notes": "标准11%"},
    "JP": {"tax_type": "JCT", "tax_name": "消費税", "rate": Decimal("0.10"), "notes": "标准10%; 食品8%"},
    "KR": {"tax_type": "VAT", "tax_name": "부가가치세", "rate": Decimal("0.10"), "notes": "标准10%"},
    "MY": {"tax_type": "SST", "tax_name": "Sales & Service Tax", "rate": Decimal("0.10"), "notes": "销售税5-10%; 服务税8%"},
    "SG": {"tax_type": "GST", "tax_name": "Goods & Services Tax", "rate": Decimal("0.09"), "notes": "标准9%"},
    "PH": {"tax_type": "VAT", "tax_name": "Value-Added Tax", "rate": Decimal("0.12"), "notes": "标准12%"},
    "DE": {"tax_type": "VAT", "tax_name": "Umsatzsteuer", "rate": Decimal("0.19"), "notes": "标准19%; 优惠7%"},
    "GB": {"tax_type": "VAT", "tax_name": "Value Added Tax", "rate": Decimal("0.20"), "notes": "标准20%; 优惠5%"},
    "FR": {"tax_type": "VAT", "tax_name": "TVA", "rate": Decimal("0.20"), "notes": "标准20%"},
    "IT": {"tax_type": "VAT", "tax_name": "IVA", "rate": Decimal("0.22"), "notes": "标准22%"},
    "ES": {"tax_type": "VAT", "tax_name": "IVA", "rate": Decimal("0.21"), "notes": "标准21%"},
    "NL": {"tax_type": "VAT", "tax_name": "BTW", "rate": Decimal("0.21"), "notes": "标准21%"},
    "AU": {"tax_type": "GST", "tax_name": "Goods & Services Tax", "rate": Decimal("0.10"), "notes": "标准10%"},
    "CA": {"tax_type": "GST/HST", "tax_name": "GST/HST", "rate": Decimal("0.05"), "notes": "联邦5%; 各省另有PST"},
    "BR": {"tax_type": "IPI+ICMS", "tax_name": "IPI + ICMS", "rate": Decimal("0.12"), "notes": "IPI 0-30%视产品; ICMS 7-18%按州"},
    "MX": {"tax_type": "IVA", "tax_name": "IVA", "rate": Decimal("0.16"), "notes": "标准16%; 边境8%"},
    "US": {"tax_type": "SALES_TAX", "tax_name": "Sales Tax", "rate": Decimal("0.00"), "notes": "无联邦VAT; 州销售税因州而异"},
    "TW": {"tax_type": "VAT", "tax_name": "營業稅", "rate": Decimal("0.05"), "notes": "标准5%"},
}

# 目的国 -> 税基 = CIF + 关税（标准VAT模式）
# 少数国家（如巴西IPI）在关税前计税，单独处理
VAT_BEFORE_DUTY = {"BR"}  # IPI 在关税前征（简化处理）


def get_vat_config(dest_country: str) -> dict:
    """获取目的国 VAT 配置"""
    cfg = VAT_RATES.get(dest_country.upper())
    if not cfg:
        return {
            "tax_type": "VAT",
            "tax_name": "Value Added Tax",
            "rate": Decimal("0.00"),
            "rate_pct": "0.00%",
            "notes": "未知国家，默认0%",
        }
    return {
        "tax_type": cfg["tax_type"],
        "tax_name": cfg["tax_name"],
        "rate": cfg["rate"],
        "rate_pct": f"{float(cfg['rate'] * 100):.2f}%",
        "notes": cfg["notes"],
    }


def calculate_vat(
    cif_value: Decimal,
    duty_amount: Decimal,
    dest_country: str,
) -> dict:
    """计算 VAT 金额

    标准公式（大多数国家）：
        VAT 税基 = CIF + 关税
        VAT 金额 = 税基 × VAT 率

    巴西 IPI 在关税前计税：
        VAT 税基 = CIF
    """
    cfg = VAT_RATES.get(dest_country.upper(), VAT_RATES.get("US"))
    rate = cfg["rate"]

    if dest_country.upper() in VAT_BEFORE_DUTY:
        taxable_base = cif_value
    else:
        taxable_base = cif_value + duty_amount

    amount = taxable_base * rate

    return {
        "tax_type": cfg["tax_type"],
        "tax_name": cfg["tax_name"],
        "rate_pct": f"{float(rate * 100):.2f}%",
        "rate": rate,
        "taxable_base": taxable_base.quantize(Decimal("0.01")),
        "amount": amount.quantize(Decimal("0.01")),
    }
