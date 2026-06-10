"""进口合规与认证要求查询服务"""
from __future__ import annotations

from typing import Optional, List

# 基于 HS 章节 + 目的国的认证要求规则
# hs_prefix: "" = 全品类适用, "84" = 前2位章节, "85" = 前2位章节
CERTIFICATION_RULES = [
    # ── 中国进口 ──
    {"dest_country": "CN", "hs_prefix": "84", "type": "CCC", "name": "中国强制认证 (CCC)", "issuer": "国家认监委", "mandatory": True},
    {"dest_country": "CN", "hs_prefix": "85", "type": "CCC", "name": "中国强制认证 (CCC)", "issuer": "国家认监委", "mandatory": True},
    {"dest_country": "CN", "hs_prefix": "95", "type": "CCC", "name": "中国强制认证 (CCC)-玩具", "issuer": "国家认监委", "mandatory": True},
    {"dest_country": "CN", "hs_prefix": "84", "type": "SRRC", "name": "无线电型号核准", "issuer": "工信部", "mandatory": True, "condition": "含无线通信功能"},
    {"dest_country": "CN", "hs_prefix": "85", "type": "SRRC", "name": "无线电型号核准", "issuer": "工信部", "mandatory": True, "condition": "含无线通信功能"},
    {"dest_country": "CN", "hs_prefix": "", "type": "MIIT", "name": "工信部进网许可", "issuer": "工信部", "mandatory": True, "condition": "电信设备"},

    # ── 欧盟进口 ──
    {"dest_country": "DE", "hs_prefix": "", "type": "CE", "name": "CE 标志", "issuer": "欧盟委员会", "mandatory": True},
    {"dest_country": "DE", "hs_prefix": "", "type": "REACH", "name": "REACH 化学品注册", "issuer": "ECHA", "mandatory": True, "condition": "含化学成分"},
    {"dest_country": "DE", "hs_prefix": "84", "type": "RoHS", "name": "RoHS 有害物质限制", "issuer": "欧盟委员会", "mandatory": True},
    {"dest_country": "DE", "hs_prefix": "85", "type": "RoHS", "name": "RoHS 有害物质限制", "issuer": "欧盟委员会", "mandatory": True},
    {"dest_country": "DE", "hs_prefix": "84", "type": "WEEE", "name": "WEEE 废弃电子电气设备指令", "issuer": "欧盟委员会", "mandatory": True},
    {"dest_country": "DE", "hs_prefix": "85", "type": "WEEE", "name": "WEEE 废弃电子电气设备指令", "issuer": "欧盟委员会", "mandatory": True},
    {"dest_country": "GB", "hs_prefix": "", "type": "UKCA", "name": "UKCA 标志", "issuer": "英国政府", "mandatory": True},
    {"dest_country": "GB", "hs_prefix": "84", "type": "RoHS", "name": "UK RoHS 有害物质限制", "issuer": "英国政府", "mandatory": True},
    {"dest_country": "GB", "hs_prefix": "85", "type": "RoHS", "name": "UK RoHS 有害物质限制", "issuer": "英国政府", "mandatory": True},

    # ── 美国进口 ──
    {"dest_country": "US", "hs_prefix": "84", "type": "FCC", "name": "FCC 认证（射频设备）", "issuer": "FCC", "mandatory": True, "condition": "产生射频的产品"},
    {"dest_country": "US", "hs_prefix": "85", "type": "FCC", "name": "FCC 认证（射频设备）", "issuer": "FCC", "mandatory": True, "condition": "产生射频的产品"},
    {"dest_country": "US", "hs_prefix": "84", "type": "UL", "name": "UL 安全认证", "issuer": "Underwriters Laboratories", "mandatory": False},
    {"dest_country": "US", "hs_prefix": "85", "type": "UL", "name": "UL 安全认证", "issuer": "Underwriters Laboratories", "mandatory": False},
    {"dest_country": "US", "hs_prefix": "84", "type": "DOE", "name": "DOE 能效认证", "issuer": "US Dept. of Energy", "mandatory": True, "condition": "消费电子"},
    {"dest_country": "US", "hs_prefix": "85", "type": "DOE", "name": "DOE 能效认证", "issuer": "US Dept. of Energy", "mandatory": True, "condition": "消费电子"},

    # ── 越南进口 ──
    {"dest_country": "VN", "hs_prefix": "84", "type": "CR", "name": "越南 CR 标志", "issuer": "MIC", "mandatory": True},
    {"dest_country": "VN", "hs_prefix": "85", "type": "CR", "name": "越南 CR 标志", "issuer": "MIC", "mandatory": True},
    {"dest_country": "VN", "hs_prefix": "", "type": "QCVN", "name": "越南国家技术法规合规", "issuer": "相关部委", "mandatory": True},

    # ── 泰国进口 ──
    {"dest_country": "TH", "hs_prefix": "84", "type": "TISI", "name": "泰国工业标准 TISI", "issuer": "TISI", "mandatory": True},
    {"dest_country": "TH", "hs_prefix": "85", "type": "TISI", "name": "泰国工业标准 TISI", "issuer": "TISI", "mandatory": True},

    # ── 印度进口 ──
    {"dest_country": "IN", "hs_prefix": "84", "type": "BIS", "name": "印度 BIS 认证", "issuer": "BIS", "mandatory": True},
    {"dest_country": "IN", "hs_prefix": "85", "type": "BIS", "name": "印度 BIS 认证", "issuer": "BIS", "mandatory": True},

    # ── 日本进口 ──
    {"dest_country": "JP", "hs_prefix": "84", "type": "PSE", "name": "电气用品安全法 PSE", "issuer": "METI", "mandatory": True},
    {"dest_country": "JP", "hs_prefix": "85", "type": "PSE", "name": "电气用品安全法 PSE", "issuer": "METI", "mandatory": True},

    # ── 韩国进口 ──
    {"dest_country": "KR", "hs_prefix": "84", "type": "KC", "name": "KC 安全认证", "issuer": "KATS", "mandatory": True},
    {"dest_country": "KR", "hs_prefix": "85", "type": "KC", "name": "KC 安全认证", "issuer": "KATS", "mandatory": True},

    # ── 巴西进口 ──
    {"dest_country": "BR", "hs_prefix": "84", "type": "ANATEL", "name": "ANATEL 电信认证", "issuer": "ANATEL", "mandatory": True, "condition": "电信设备"},
    {"dest_country": "BR", "hs_prefix": "85", "type": "ANATEL", "name": "ANATEL 电信认证", "issuer": "ANATEL", "mandatory": True, "condition": "电信设备"},
    {"dest_country": "BR", "hs_prefix": "84", "type": "INMETRO", "name": "INMETRO 认证", "issuer": "INMETRO", "mandatory": True},
    {"dest_country": "BR", "hs_prefix": "85", "type": "INMETRO", "name": "INMETRO 认证", "issuer": "INMETRO", "mandatory": True},

    # ── 墨西哥进口 ──
    {"dest_country": "MX", "hs_prefix": "84", "type": "NOM", "name": "NOM 强制认证", "issuer": "Secretaría de Economía", "mandatory": True},
    {"dest_country": "MX", "hs_prefix": "85", "type": "NOM", "name": "NOM 强制认证", "issuer": "Secretaría de Economía", "mandatory": True},

    # ── 澳大利亚进口 ──
    {"dest_country": "AU", "hs_prefix": "84", "type": "RCM", "name": "RCM 合规标志", "issuer": "ACMAA", "mandatory": True},
    {"dest_country": "AU", "hs_prefix": "85", "type": "RCM", "name": "RCM 合规标志", "issuer": "ACMAA", "mandatory": True},

    # ── 台湾进口 ──
    {"dest_country": "TW", "hs_prefix": "84", "type": "BSMI", "name": "BSMI 强制认证", "issuer": "BSMI", "mandatory": True},
    {"dest_country": "TW", "hs_prefix": "85", "type": "BSMI", "name": "BSMI 强制认证", "issuer": "BSMI", "mandatory": True},

    # ── 印度尼西亚进口 ──
    {"dest_country": "ID", "hs_prefix": "84", "type": "SNI", "name": "SNI 国家标准", "issuer": "BSN", "mandatory": True},
    {"dest_country": "ID", "hs_prefix": "85", "type": "SNI", "name": "SNI 国家标准", "issuer": "BSN", "mandatory": True},

    # ── 加拿大进口 ──
    {"dest_country": "CA", "hs_prefix": "84", "type": "IC", "name": "ISED 认证（无线电）", "issuer": "ISED Canada", "mandatory": True, "condition": "无线设备"},
    {"dest_country": "CA", "hs_prefix": "85", "type": "IC", "name": "ISED 认证（无线电）", "issuer": "ISED Canada", "mandatory": True, "condition": "无线设备"},
]


def get_import_requirements(dest_country: str, hs_code: str = "") -> List[dict]:
    """查询目的国对特定 HS 编码的认证要求"""
    hs_prefix = hs_code[:2] if hs_code else ""
    results = []

    for rule in CERTIFICATION_RULES:
        if rule["dest_country"] != dest_country:
            continue
        # 匹配 HS 前缀：空 = 全品类，否则匹配前2位
        if rule["hs_prefix"] and rule["hs_prefix"] != hs_prefix:
            continue
        item = {
            "type": rule["type"],
            "name": rule["name"],
            "issuing_authority": rule["issuer"],
            "is_mandatory": rule["mandatory"],
        }
        if rule.get("condition"):
            item["condition"] = rule["condition"]
        results.append(item)

    return results
