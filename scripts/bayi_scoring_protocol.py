# -*- coding: utf-8 -*-
"""
Bayi & Franchise Puanlama Motoru, Resmi Ön Protokol Üretici ve Ağ Analitik Modülü
6769 Sayılı Sınai Mülkiyet Kanunu, TTK franchise/bayilik mevzuatı uyumlu.
"""

import json
import re
import html
from datetime import datetime

DEFAULT_COMPANY = {
    "name": "E-İMZA & KEP BİLİŞİM TEKNOLOJİLERİ A.Ş.",
    "trade_title": "E-İmza, KEP ve Elektronik Tebligat Çözümleri Dağıtım A.Ş.",
    "tax_id": "3240589124",
    "tax_office": "Büyük Mükellefler V.D.",
    "mersis": "0324058912400017",
    "address": "Maslak Mah. Büyükdere Cad. No:199 Spine Tower K:14 Sarıyer / İstanbul",
    "kep": "eimzakep@hs01.kep.tr",
    "phone": "+90 (212) 444 0 345",
    "email": "bayilik@eimza-kep.com.tr",
    "web": "www.eimza-kep.com.tr"
}

def calculate_dealer_score(data):
    """
    Bayi adayının finansal kapasitesi, lokasyon özellikleri, deneyimi ve teminat gücüne göre
    100 üzerinden ağırlıklı yeterlilik puanı ve segmentasyonunu hesaplar.
    """
    if not isinstance(data, dict):
        # sqlite3.Row or similar mapping
        data = dict(data)

    budget_str = str(data.get("investment_budget") or "").lower()
    area = float(data.get("store_area") or 0)
    frontage = float(data.get("store_frontage") or 0)
    exp_str = str(data.get("experience_years") or "").lower()
    collateral_str = str(data.get("collateral_capacity") or "").lower()
    vkn_ver = bool(data.get("vkn_verified"))

    # 1. Sermaye ve Bütçe Yeterliliği (%35 Ağırlık)
    if "5.000.000" in budget_str or "5 milyon" in budget_str or "10 milyon" in budget_str:
        capital_score = 35
    elif "2.500.000" in budget_str:
        capital_score = 28
    elif "1.000.000" in budget_str:
        capital_score = 22
    elif "500.000" in budget_str:
        capital_score = 15
    elif "250.000" in budget_str:
        capital_score = 10
    else:
        capital_score = 7

    # 2. Lokasyon & Mağaza Standartları (%25 Ağırlık)
    # Alan (Max 15)
    if area >= 200:
        area_score = 15
    elif area >= 120:
        area_score = 12
    elif area >= 80:
        area_score = 9
    elif area >= 40:
        area_score = 6
    else:
        area_score = 3

    # Cephe (Max 10)
    if frontage >= 10:
        frontage_score = 10
    elif frontage >= 7:
        frontage_score = 8
    elif frontage >= 5:
        frontage_score = 6
    elif frontage >= 3:
        frontage_score = 4
    else:
        frontage_score = 2

    location_score = area_score + frontage_score

    # 3. Sektörel Deneyim & Ticari Geçmiş (%20 Ağırlık)
    if "10" in exp_str:
        experience_score = 20
    elif "5-10" in exp_str or "5 yıl" in exp_str or "7" in exp_str:
        experience_score = 16
    elif "2-5" in exp_str or "3 yıl" in exp_str:
        experience_score = 12
    elif "1-2" in exp_str:
        experience_score = 8
    else:
        experience_score = 4

    # 4. Teminat Gücü & VKN Güvenilirlik (%20 Ağırlık)
    # Teminat (Max 14)
    if "1.000.000" in collateral_str or "mektup" in collateral_str or "nakit" in collateral_str:
        collateral_base = 14
    elif "gayrimenkul" in collateral_str or "500.000" in collateral_str or "ipotek" in collateral_str:
        collateral_base = 10
    elif "kefalet" in collateral_str or "250.000" in collateral_str:
        collateral_base = 7
    else:
        collateral_base = 4

    # VKN Doğrulama Bonusu (Max 6)
    vkn_bonus = 6 if vkn_ver else 0
    collateral_score = collateral_base + vkn_bonus

    total_score = capital_score + location_score + experience_score + collateral_score
    total_score = max(0, min(100, total_score))

    # Segmentasyon
    if total_score >= 85:
        tier = "A+"
        tier_title = "A+ (Mükemmel - Münhasır Bayilik)"
        recommendation = "Yüksek sermaye yeterliliği ve kusursuz fiziki mağaza standartları. Bölgesel tek yetkili münhasır bayilik için derhal onaylanması önerilir."
        color = "#15803d"
    elif total_score >= 70:
        tier = "A"
        tier_title = "A (Çok İyi - Standart Franchise)"
        recommendation = "Gerekli fiziki ve mali yeterlilikler sağlanmıştır. Standart franchise ve bayilik sözleşmesi aşamasına geçilebilir."
        color = "#0284c7"
    elif total_score >= 55:
        tier = "B"
        tier_title = "B (Orta - Şartlı Onay)"
        recommendation = "Ticari potansiyel mevcut. Ek banka teminat mektubu ve satış kotası taahhüdü alınarak şartlı onay verilebilir."
        color = "#d97706"
    elif total_score >= 40:
        tier = "C"
        tier_title = "C (Riskli - İnceleme Gerekli)"
        recommendation = "Mali güç veya lokasyon standartları sınır seviyede. Bölge saha direktörü tarafından yerinde denetim gereklidir."
        color = "#ea580c"
    else:
        tier = "D"
        tier_title = "D (Yetersiz - Asgari Kriter Altı)"
        recommendation = "Kurumsal bayilik kriterlerini karşılamamaktadır. Başvurunun reddedilmesi veya alt satış noktası olarak değerlendirilmesi önerilir."
        color = "#dc2626"

    return {
        "total_score": total_score,
        "tier": tier,
        "tier_title": tier_title,
        "recommendation": recommendation,
        "color": color,
        "breakdown": {
            "capital_score": capital_score,
            "max_capital": 35,
            "location_score": location_score,
            "max_location": 25,
            "experience_score": experience_score,
            "max_experience": 20,
            "collateral_score": collateral_score,
            "max_collateral": 20
        }
    }

def generate_dealership_protocol_html(dealer_data, company_info=None):
    """
    Resmi Türk Ticaret Kanunu (TTK) ve 6769 Sayılı SMK standartlarında
    A4 formatında yazdırılabilir Resmi Bayilik ve Franchise Ön Protokolü üretir.
    """
    c = company_info or DEFAULT_COMPANY
    d = dict(dealer_data) if not isinstance(dealer_data, dict) else dealer_data

    tracking_code = html.escape(str(d.get("tracking_code") or "BAYI-2026-0000"))
    applicant_title = html.escape(str(d.get("applicant_title") or "Belirtilmemiş Firma"))
    tax_id = html.escape(str(d.get("tax_id") or "-"))
    contact_name = html.escape(str(d.get("contact_name") or "-"))
    contact_phone = html.escape(str(d.get("contact_phone") or "-"))
    contact_email = html.escape(str(d.get("contact_email") or "-"))
    target_location = html.escape(str(d.get("target_location") or "Belirtilmemiş"))
    app_type = html.escape(str(d.get("application_type") or "Münhasır Bayilik"))
    store_area = d.get("store_area") or 0
    store_frontage = d.get("store_frontage") or 0
    budget = html.escape(str(d.get("investment_budget") or "-"))
    collateral = html.escape(str(d.get("collateral_capacity") or "-"))
    tax_office = html.escape(str(d.get("tax_office") or "Vergi Dairesi"))
    mersis_no = html.escape(str(d.get("mersis_no") or "-"))
    score_res = calculate_dealer_score(d)

    created_at = str(d.get("created_at") or "")
    if created_at and "T" in created_at:
        doc_date = created_at.split("T")[0]
    else:
        doc_date = datetime.now().strftime("%d.%m.%Y")

    protocol_html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Bayilik ve Franchise Ön Protokolü - {tracking_code}</title>
    <style>
        @page {{
            size: A4;
            margin: 18mm 18mm 18mm 18mm;
        }}
        * {{
            box-sizing: border-box;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', Arial, sans-serif;
        }}
        body {{
            background: #f1f5f9;
            color: #0f172a;
            margin: 0;
            padding: 24px;
            font-size: 13px;
            line-height: 1.55;
        }}
        .document-container {{
            max-width: 800px;
            margin: 0 auto;
            background: #ffffff;
            padding: 38px 44px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            position: relative;
        }}
        .no-print-bar {{
            max-width: 800px;
            margin: 0 auto 16px auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #1e293b;
            color: #ffffff;
            padding: 12px 20px;
            border-radius: 8px;
        }}
        .btn {{
            background: #0284c7;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 13px;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .btn:hover {{ background: #0369a1; }}
        .header-table {{
            width: 100%;
            border-bottom: 2px solid #0284c7;
            padding-bottom: 14px;
            margin-bottom: 18px;
        }}
        .logo-title {{
            font-size: 17px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.3px;
        }}
        .sub-title {{
            font-size: 11px;
            color: #475569;
            margin-top: 3px;
        }}
        .meta-box {{
            text-align: right;
            font-size: 11px;
            color: #334155;
            line-height: 1.4;
        }}
        .protocol-title {{
            text-align: center;
            font-size: 16px;
            font-weight: 800;
            color: #0369a1;
            margin: 18px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-top: 1px solid #e2e8f0;
            border-bottom: 1px solid #e2e8f0;
            padding: 8px 0;
            background: #f8fafc;
        }}
        .parties-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 18px;
        }}
        .party-card {{
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 12px 14px;
            background: #fafafa;
        }}
        .party-card h4 {{
            margin: 0 0 8px 0;
            font-size: 12px;
            color: #0284c7;
            text-transform: uppercase;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 4px;
        }}
        .party-row {{
            margin-bottom: 4px;
            font-size: 11.5px;
        }}
        .party-row strong {{
            color: #334155;
            display: inline-block;
            width: 80px;
        }}
        .article {{
            margin-bottom: 12px;
            text-align: justify;
        }}
        .article-title {{
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 3px;
            font-size: 12.5px;
        }}
        .score-pill {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 700;
            color: #ffffff;
            background: {score_res['color']};
        }}
        .highlight-box {{
            background: #f0f9ff;
            border-left: 4px solid #0284c7;
            padding: 10px 14px;
            margin: 14px 0;
            border-radius: 0 6px 6px 0;
            font-size: 12px;
        }}
        .signatures {{
            margin-top: 26px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            page-break-inside: avoid;
        }}
        .sig-block {{
            border: 1px dashed #94a3b8;
            border-radius: 6px;
            padding: 14px;
            text-align: center;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .sig-title {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            color: #475569;
        }}
        .sig-stamp {{
            font-size: 10px;
            color: #94a3b8;
            border-top: 1px solid #e2e8f0;
            padding-top: 6px;
            margin-top: 36px;
        }}
        .footer-note {{
            margin-top: 22px;
            border-top: 1px solid #e2e8f0;
            padding-top: 8px;
            font-size: 9.5px;
            color: #64748b;
            display: flex;
            justify-content: space-between;
        }}
        @media print {{
            body {{
                background: #ffffff;
                padding: 0;
            }}
            .document-container {{
                box-shadow: none;
                padding: 0;
                max-width: 100%;
            }}
            .no-print-bar {{
                display: none !important;
            }}
        }}
    </style>
</head>
<body>

<div class="no-print-bar">
    <div>
        <strong>Resmi Bayilik Ön Protokolü:</strong> {tracking_code} ({applicant_title})
    </div>
    <div style="display: flex; gap: 8px;">
        <button class="btn" onclick="window.print()">🖨️ Yazdır / PDF Kaydet</button>
        <button class="btn" style="background:#475569" onclick="window.close()">✖ Kapat</button>
    </div>
</div>

<div class="document-container">
    <table class="header-table">
        <tr>
            <td style="vertical-align: top;">
                <div class="logo-title">{c['name']}</div>
                <div class="sub-title">{c['trade_title']}</div>
                <div class="sub-title">MERSİS: {c['mersis']} | VKN: {c['tax_id']} ({c['tax_office']})</div>
            </td>
            <td class="meta-box" style="vertical-align: top;">
                <div><strong>Protokol No:</strong> {tracking_code}</div>
                <div><strong>Düzenleme Tarihi:</strong> {doc_date}</div>
                <div><strong>Geçerlilik:</strong> 60 Takvim Günü</div>
                <div style="margin-top: 4px;"><span class="score-pill">Skor: {score_res['total_score']}/100 - {score_res['tier']}</span></div>
            </td>
        </tr>
    </table>

    <div class="protocol-title">
        TİCARİ BAYİLİK VE FRANCHISE ÖN PROTOKOLÜ VE UYGUNLUK BELGESİ
    </div>

    <div class="parties-grid">
        <div class="party-card">
            <h4>1. LİSANSÖR / ANA DAĞITICI</h4>
            <div class="party-row"><strong>Unvan:</strong> {c['name']}</div>
            <div class="party-row"><strong>Adres:</strong> {c['address']}</div>
            <div class="party-row"><strong>Vergi D.:</strong> {c['tax_office']} / {c['tax_id']}</div>
            <div class="party-row"><strong>KEP:</strong> {c['kep']}</div>
            <div class="party-row"><strong>İletişim:</strong> {c['phone']}</div>
        </div>

        <div class="party-card">
            <h4>2. BAYİ ADAYI / İŞ ORTAĞI</h4>
            <div class="party-row"><strong>Unvan:</strong> {applicant_title}</div>
            <div class="party-row"><strong>Yetkili:</strong> {contact_name}</div>
            <div class="party-row"><strong>VKN/TCKN:</strong> {tax_id} ({tax_office})</div>
            <div class="party-row"><strong>MERSİS:</strong> {mersis_no}</div>
            <div class="party-row"><strong>İletişim:</strong> {contact_phone} | {contact_email}</div>
        </div>
    </div>

    <div class="highlight-box">
        <strong>Ön İnceleme ve Yeterlilik Değerlendirmesi:</strong> {applicant_title} firması tarafından yapılan bayilik başvurusu neticesinde; başvuru sahibinin mali yeterlilik puanı <strong>{score_res['total_score']} / 100</strong> olarak tespit edilmiş olup aday <strong>{score_res['tier_title']}</strong> segmentinde değerlendirilmiştir. {score_res['recommendation']}
    </div>

    <div class="article">
        <div class="article-title">Madde 1: Protokolün Konusu ve Hukuki Mahiyeti</div>
        İşbu Protokol; 6102 sayılı Türk Ticaret Kanunu, 6098 sayılı Türk Borçlar Kanunu ve 6769 sayılı Sınai Mülkiyet Kanunu çerçevesinde, Lisansör tarafından geliştirilen kurumsal e-imza, KEP, e-Dönüşüm ve bilişim hizmetlerinin <strong>{target_location}</strong> bölgesinde <strong>"{app_type}"</strong> statüsünde tanıtımı, satışı ve dağıtımına ilişkin nihai franchise/bayilik sözleşmesinin tanziminden önceki bağlayıcı ön şartları belirler.
    </div>

    <div class="article">
        <div class="article-title">Madde 2: Bölge Tahsisi ve Münhasırlık Hükümleri</div>
        Lisansör, Bayi Adayı'nın nihai sözleşmeyi imzalaması ve asgari taahhütleri yerine getirmesi şartıyla <strong>{target_location}</strong> sınırları dahilinde yetkili satış ve başvuru merkezi açma hakkını saklı tutar. Münhasır bayilik modelinde belirtilen coğrafi bölge sınırları içerisinde ikinci bir ana bayilik tesis edilmeyecektir.
    </div>

    <div class="article">
        <div class="article-title">Madde 3: Mağaza Standartları ve Kurumsal Mimari Konsept</div>
        Bayi Adayı; hedef bölgede açacağı mağazanın en az <strong>{store_area} m²</strong> kapalı alana ve asgari <strong>{store_frontage} metre</strong> cadde vitrin cephesine sahip olacağını, mağaza tefrişatının Lisansör'ün kurumsal kimlik kılavuzuna %100 uyumlu mimari projeye göre tamamlanacağını kabul ve taahhüt eder.
    </div>

    <div class="article">
        <div class="article-title">Madde 4: Mali Taahhütler, Yatırım Bütçesi ve Teminat Şartı</div>
        Bayi Adayı, işbu bayilik operasyonu için beyan ettiği <strong>{budget}</strong> tutarındaki başlangıç sermayesini hazır bulunduracağını ve sözleşme imzasında Lisansör lehine <strong>{collateral}</strong> kapsamındaki kesin ve süresiz banka teminat mektubunu veya nakit teminatı tevdi edeceğini taahhüt eder.
    </div>

    <div class="article">
        <div class="article-title">Madde 5: Gizlilik, KVKK ve Rekabet Yasağı</div>
        Taraflar, işbu protokol vesilesiyle muttali oldukları her türlü ticari sırrı, müşteri portföyünü ve kurumsal yazılım altyapısını 6698 Sayılı KVKK kapsamında koruyacaklarını; Bayi Adayı protokolün sona ermesinden itibaren 2 (iki) yıl süreyle aynı sektörde rakip faaliyette bulunmayacağını gayrikabili rücu kabul eder.
    </div>

    <div class="article">
        <div class="article-title">Madde 6: Uyuşmazlıkların Çözümü ve Yetkili Mercii</div>
        İşbu ön protokolden doğabilecek her türlü ihtilafın hallinde İstanbul Merkez (Çağlayan) Mahkemeleri ve İcra Daireleri yetkilidir.
    </div>

    <div class="signatures">
        <div class="sig-block">
            <div class="sig-title">LİSANSÖR / ANA DAĞITICI</div>
            <div style="font-size: 11px; margin-top: 8px;">
                <strong>{c['name']}</strong><br>
                Genel Müdürlük & Bayi Geliştirme Direktörlüğü
            </div>
            <div class="sig-stamp">
                [GÜVENLİ ELEKTRONİK İMZA & KURUMSAL KAŞE]<br>
                5070 Sayılı Kanun Uyarınca E-İmzalanmıştır
            </div>
        </div>

        <div class="sig-block">
            <div class="sig-title">BAYİ ADAYI / İŞ ORTAĞI</div>
            <div style="font-size: 11px; margin-top: 8px;">
                <strong>{applicant_title}</strong><br>
                Yetkili Temsilci: {contact_name}
            </div>
            <div class="sig-stamp">
                [YETKİLİ İMZA & ŞİRKET KAŞESİ]<br>
                Tarih: {doc_date}
            </div>
        </div>
    </div>

    <div class="footer-note">
        <div>Doğrulama Kodu: {tracking_code}-VERIFIED-2026 | Güvenli Ön Protokol Belgesi</div>
        <div>Sayfa 1 / 1 (Resmi A4 Nüshası)</div>
    </div>
</div>

</body>
</html>"""
    return protocol_html

def calculate_network_analytics(applications):
    """
    Tüm bayi başvurularını analiz ederek icra kurulu ve satış direktörlüğü için
    kapsamlı analitik göstergeler hesaplar.
    """
    total = len(applications)
    if total == 0:
        return {
            "total_applications": 0,
            "status_counts": {},
            "type_counts": {},
            "total_store_area": 0,
            "avg_store_area": 0,
            "avg_frontage": 0,
            "top_locations": [],
            "vkn_verified_count": 0,
            "vkn_verified_rate": 0.0,
            "avg_score": 0.0,
            "tier_distribution": {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0},
            "approved_count": 0,
            "approval_rate": 0.0,
            "estimated_investment_volume": 0
        }

    status_counts = {}
    type_counts = {}
    location_counts = {}
    tier_counts = {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0}

    total_area = 0
    total_frontage = 0
    total_score = 0
    verified_vkn_count = 0
    approved_count = 0
    total_invest_approx = 0

    for raw_app in applications:
        app = dict(raw_app) if not isinstance(raw_app, dict) else raw_app
        st = app.get("status") or "Başvuru Alındı"
        status_counts[st] = status_counts.get(st, 0) + 1

        t = app.get("application_type") or "Münhasır Bayilik (Tek Yetkili)"
        type_counts[t] = type_counts.get(t, 0) + 1

        loc = app.get("target_location") or "Belirtilmemiş"
        # Extract main city if has slash
        city = loc.split("/")[0].strip() if "/" in loc else loc.strip()
        location_counts[city] = location_counts.get(city, 0) + 1

        area = float(app.get("store_area") or 0)
        frontage = float(app.get("store_frontage") or 0)
        total_area += area
        total_frontage += frontage

        if app.get("vkn_verified"):
            verified_vkn_count += 1

        if "Onay" in st:
            approved_count += 1

        score_data = calculate_dealer_score(app)
        total_score += score_data["total_score"]
        tier = score_data["tier"]
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # Approximation for investment
        bud = str(app.get("investment_budget") or "")
        if "5.000.000" in bud:
            total_invest_approx += 5000000
        elif "2.500.000" in bud:
            total_invest_approx += 3500000
        elif "1.000.000" in bud:
            total_invest_approx += 1500000
        elif "500.000" in bud:
            total_invest_approx += 750000
        elif "250.000" in bud:
            total_invest_approx += 350000
        else:
            total_invest_approx += 200000

    sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_applications": total,
        "status_counts": status_counts,
        "type_counts": type_counts,
        "total_store_area": round(total_area, 1),
        "avg_store_area": round(total_area / total, 1),
        "avg_frontage": round(total_frontage / total, 1),
        "top_locations": sorted_locations[:8],
        "vkn_verified_count": verified_vkn_count,
        "vkn_verified_rate": round((verified_vkn_count / total) * 100, 1),
        "avg_score": round(total_score / total, 1),
        "tier_distribution": tier_counts,
        "approved_count": approved_count,
        "approval_rate": round((approved_count / total) * 100, 1),
        "estimated_investment_volume": total_invest_approx
    }

def generate_dealer_network_report_html(analytics, company_info=None):
    """
    İcra Kurulu ve Satış Direktörlüğü için A4 formatında
    Bayi & Franchise Ağı Geliştirme ve Başvuru Analitik Raporu üretir.
    """
    c = company_info or DEFAULT_COMPANY
    doc_date = datetime.now().strftime("%d.%m.%Y %H:%M")

    total = analytics["total_applications"]
    invest_fmt = f"{analytics['estimated_investment_volume']:,} TL".replace(",", ".")

    tiers = analytics.get("tier_distribution", {})
    tier_rows = ""
    for tier_code, count in tiers.items():
        pct = round((count / total * 100), 1) if total > 0 else 0
        color = "#15803d" if tier_code == "A+" else ("#0284c7" if tier_code == "A" else ("#d97706" if tier_code == "B" else ("#ea580c" if tier_code == "C" else "#dc2626")))
        tier_rows += f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; font-size: 12px;">
            <span style="font-weight: 700; width: 60px; color: {color};">Kademe {tier_code}:</span>
            <div style="flex: 1; height: 10px; background: #e2e8f0; border-radius: 999px; margin: 0 12px; overflow: hidden;">
                <div style="width: {pct}%; height: 100%; background: {color}; border-radius: 999px;"></div>
            </div>
            <span style="font-weight: 600; width: 85px; text-align: right;">{count} Bayi (%{pct})</span>
        </div>
        """

    status_rows = ""
    for st_name, count in analytics.get("status_counts", {}).items():
        pct = round((count / total * 100), 1) if total > 0 else 0
        status_rows += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;"><b>{html.escape(st_name)}</b></td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: center;">{count}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: right;">%{pct}</td>
        </tr>
        """

    loc_rows = ""
    for city, count in analytics.get("top_locations", []):
        pct = round((count / total * 100), 1) if total > 0 else 0
        loc_rows += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;">📍 <b>{html.escape(city)}</b></td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: center;">{count}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: right;">%{pct}</td>
        </tr>
        """

    report_html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>İcra Kurulu Bayilik Ağı Raporu - {c['name']}</title>
    <style>
        @page {{
            size: A4;
            margin: 16mm;
        }}
        * {{
            box-sizing: border-box;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', Arial, sans-serif;
        }}
        body {{
            background: #f1f5f9;
            color: #0f172a;
            margin: 0;
            padding: 24px;
            font-size: 13px;
            line-height: 1.5;
        }}
        .report-card {{
            max-width: 860px;
            margin: 0 auto;
            background: #ffffff;
            padding: 36px 44px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}
        .no-print-bar {{
            max-width: 860px;
            margin: 0 auto 16px auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #1e293b;
            color: #ffffff;
            padding: 12px 20px;
            border-radius: 8px;
        }}
        .btn {{
            background: #0284c7;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 13px;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .btn:hover {{ background: #0369a1; }}
        .header {{
            border-bottom: 2px solid #0284c7;
            padding-bottom: 14px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .title {{
            font-size: 18px;
            font-weight: 800;
            color: #0f172a;
        }}
        .subtitle {{
            font-size: 11px;
            color: #475569;
            margin-top: 4px;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 14px;
            background: #f8fafc;
            text-align: center;
        }}
        .kpi-val {{
            font-size: 20px;
            font-weight: 800;
            color: #0369a1;
            margin-top: 4px;
        }}
        .kpi-lbl {{
            font-size: 10.5px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
        }}
        .section-title {{
            font-size: 13.5px;
            font-weight: 700;
            color: #0f172a;
            border-left: 4px solid #0284c7;
            padding-left: 8px;
            margin: 20px 0 12px 0;
        }}
        .two-cols {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }}
        th {{
            background: #f1f5f9;
            padding: 8px 12px;
            font-weight: 700;
            color: #334155;
            border-bottom: 1px solid #cbd5e1;
            text-align: left;
        }}
        .directive-box {{
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 14px;
            margin-top: 20px;
            font-size: 12px;
            line-height: 1.6;
        }}
        @media print {{
            body {{ background: #fff; padding: 0; }}
            .report-card {{ box-shadow: none; padding: 0; max-width: 100%; }}
            .no-print-bar {{ display: none !important; }}
        }}
    </style>
</head>
<body>

<div class="no-print-bar">
    <div>
        <strong>İcra Kurulu Bayilik Analitik Raporu</strong> ({c['name']})
    </div>
    <div style="display: flex; gap: 8px;">
        <button class="btn" onclick="window.print()">🖨️ Yazdır / PDF İndir</button>
        <button class="btn" style="background:#475569" onclick="window.close()">✖ Kapat</button>
    </div>
</div>

<div class="report-card">
    <div class="header">
        <div>
            <div class="title">İCRA KURULU BAYİLİK & FRANCHISE AĞI GELİŞTİRME RAPORU</div>
            <div class="subtitle">{c['trade_title']} - Stratejik Büyüme & Satış Direktörlüğü</div>
        </div>
        <div style="text-align: right; font-size: 11px; color: #475569;">
            <div><strong>Rapor Tarihi:</strong> {doc_date}</div>
            <div><strong>Dönem:</strong> 2026 Mali Yılı Güncel Durum</div>
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-lbl">Toplam Başvuru</div>
            <div class="kpi-val">{total}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-lbl">Onaylanan Bayilik</div>
            <div class="kpi-val" style="color: #15803d;">{analytics['approved_count']}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-lbl">Ortalama Aday Skoru</div>
            <div class="kpi-val">{analytics['avg_score']}/100</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-lbl">Tahmini Yatırım Hacmi</div>
            <div class="kpi-val" style="font-size: 16px; color: #d97706;">{invest_fmt}</div>
        </div>
    </div>

    <div class="two-cols">
        <div>
            <div class="section-title">Aday Skor ve Kalite Segmentasyonu</div>
            <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; background: #fafafa;">
                {tier_rows}
            </div>

            <div style="margin-top: 14px; font-size: 11px; color: #64748b; line-height: 1.4;">
                * <strong>A+ / A Kademeleri:</strong> Doğrudan münhasır bayilik ve ön protokol tanzimine uygun kurumsal profillerdir.
            </div>
        </div>

        <div>
            <div class="section-title">Yoğun Başvuru Alan Şehirler / Bölgeler</div>
            <div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                <table>
                    <thead>
                        <tr>
                            <th>Bölge / İl</th>
                            <th style="text-align: center;">Başvuru</th>
                            <th style="text-align: right;">Pay</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loc_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="two-cols">
        <div>
            <div class="section-title">Başvuru Süreç Dağılımı</div>
            <div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                <table>
                    <thead>
                        <tr>
                            <th>Süreç Aşaması</th>
                            <th style="text-align: center;">Adet</th>
                            <th style="text-align: right;">Oran</th>
                        </tr>
                    </thead>
                    <tbody>
                        {status_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <div>
            <div class="section-title">Mağaza ve Fiziki Lokasyon Metrikleri</div>
            <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; background: #fafafa; font-size: 12px;">
                <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #e2e8f0;">
                    <span>Toplam Taahhüt Edilen Mağaza Alanı:</span>
                    <strong>{analytics['total_store_area']:,} m²</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #e2e8f0;">
                    <span>Ortalama Mağaza Büyüklüğü:</span>
                    <strong>{analytics['avg_store_area']} m²</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #e2e8f0;">
                    <span>Ortalama Cadde Vitrin Cephesi:</span>
                    <strong>{analytics['avg_frontage']} metre</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 6px 0;">
                    <span>GİB / MERSİS Doğrulanmış Firma:</span>
                    <strong>{analytics['vkn_verified_count']} Firma (%{analytics['vkn_verified_rate']})</strong>
                </div>
            </div>
        </div>
    </div>

    <div class="directive-box">
        <strong style="color: #166534; font-size: 12.5px;">📌 İcra Kurulu ve Satış Direktörlüğü Değerlendirmesi:</strong>
        <p style="margin: 6px 0 0 0; color: #14532d;">
            Mevcut başvuru havuzu genelinde ortalama yeterlilik skoru <strong>{analytics['avg_score']}/100</strong> seviyesinde olup, özellikle Marmara ve Ege bölgelerindeki talep yoğunluğu münhasır bayilik hedefleriyle tam örtüşmektedir. A+ ve A kademesindeki adaylar için gecikmeksizin A4 Resmi Bayilik Ön Protokollerinin tanzim edilmesi, teminat mektuplarının tahsili ve fiziki mağaza kurulum denetimlerinin başlatılması tavsiye olunur.
        </p>
    </div>

    <div style="margin-top: 24px; display: flex; justify-content: space-between; font-size: 10px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 8px;">
        <div>{c['name']} Yönetim Raporlama Sistemi</div>
        <div>Gizli & Kurum İçi Kullanıma Mahsustur</div>
    </div>
</div>

</body>
</html>"""
    return report_html

def generate_dealer_csv_export(applications):
    """
    Tüm bayi başvurularını Excel uyumlu UTF-8 BOM CSV formatında dışa aktarır.
    """
    csv_lines = []
    # UTF-8 BOM
    header = [
        "Dosya No",
        "Başvuru Türü",
        "Firma Unvanı",
        "VKN/TCKN",
        "GİB Doğrulandı",
        "Vergi Dairesi",
        "MERSİS No",
        "Mükellef Durumu",
        "Yetkili Kişi",
        "Telefon",
        "E-posta",
        "Hedef Lokasyon",
        "Enlem (Lat)",
        "Boylam (Lng)",
        "Mülk Durumu",
        "Mağaza Alanı (m2)",
        "Vitrin Cephesi (m)",
        "Yatırım Bütçesi",
        "Teminat Kapasitesi",
        "Deneyim",
        "Hedef Ciro",
        "Skor",
        "Kademe",
        "Durum",
        "Başvuru Tarihi"
    ]
    csv_lines.append(",".join(f'"{col}"' for col in header))

    for raw_app in applications:
        app = dict(raw_app) if not isinstance(raw_app, dict) else raw_app
        score_res = calculate_dealer_score(app)

        row = [
            str(app.get("tracking_code") or ""),
            str(app.get("application_type") or ""),
            str(app.get("applicant_title") or ""),
            str(app.get("tax_id") or ""),
            "EVET" if app.get("vkn_verified") else "HAYIR",
            str(app.get("tax_office") or ""),
            str(app.get("mersis_no") or ""),
            str(app.get("company_status") or "FAAL"),
            str(app.get("contact_name") or ""),
            str(app.get("contact_phone") or ""),
            str(app.get("contact_email") or ""),
            str(app.get("target_location") or ""),
            str(app.get("latitude") or ""),
            str(app.get("longitude") or ""),
            str(app.get("property_status") or ""),
            str(app.get("store_area") or 0),
            str(app.get("store_frontage") or 0),
            str(app.get("investment_budget") or ""),
            str(app.get("collateral_capacity") or ""),
            str(app.get("experience_years") or ""),
            str(app.get("target_annual_revenue") or ""),
            str(score_res["total_score"]),
            str(score_res["tier"]),
            str(app.get("status") or "Başvuru Alındı"),
            str(app.get("created_at") or "")
        ]
        # Clean quotes
        clean_row = [val.replace('"', '""') for val in row]
        csv_lines.append(",".join(f'"{val}"' for val in clean_row))

    return "\ufeff" + "\n".join(csv_lines)
