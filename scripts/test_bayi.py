# -*- coding: utf-8 -*-
import unittest
import os
import sys
import sqlite3
import json
from io import BytesIO
from unittest.mock import MagicMock

# Ensure parent directory and scripts directory are in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import server
from bayi_vkn_validator import (
    validate_vkn_checksum,
    validate_tckn_checksum,
    validate_mersis_format,
    verify_company_vkn
)
from bayi_scoring_protocol import (
    calculate_dealer_score,
    generate_dealership_protocol_html,
    calculate_network_analytics,
    generate_dealer_network_report_html,
    generate_dealer_csv_export
)

class TestDealerSystem(unittest.TestCase):
    def setUp(self):
        server.init_db()
        self.conn = sqlite3.connect(server.DB_FILE)
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        cur.execute("DELETE FROM dealer_applications WHERE tracking_code LIKE 'BAYI-TEST%'")
        self.conn.commit()

    def tearDown(self):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM dealer_applications WHERE tracking_code LIKE 'BAYI-TEST%'")
        self.conn.commit()
        self.conn.close()

    def test_database_table_exists(self):
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dealer_applications'")
        row = cur.fetchone()
        self.assertIsNotNone(row, "dealer_applications tablosu oluşturulmuş olmalıdır.")

    def test_table_has_map_and_vkn_columns(self):
        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(dealer_applications)")
        columns = [row["name"] for row in cur.fetchall()]
        self.assertIn("latitude", columns, "latitude kolonu bulunmalıdır.")
        self.assertIn("longitude", columns, "longitude kolonu bulunmalıdır.")
        self.assertIn("map_address", columns, "map_address kolonu bulunmalıdır.")
        self.assertIn("vkn_verified", columns, "vkn_verified kolonu bulunmalıdır.")
        self.assertIn("tax_office", columns, "tax_office kolonu bulunmalıdır.")
        self.assertIn("mersis_no", columns, "mersis_no kolonu bulunmalıdır.")
        self.assertIn("company_status", columns, "company_status kolonu bulunmalıdır.")

    def test_dealer_insert_and_retrieve_with_location_and_vkn(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO dealer_applications (
                tracking_code, application_type, applicant_title, contact_name,
                tax_id, contact_phone, contact_email, target_location,
                property_status, store_area, store_frontage, location_details,
                investment_budget, collateral_capacity, experience_years,
                target_annual_revenue, business_vision, status, created_at,
                latitude, longitude, map_address, vkn_verified, tax_office,
                mersis_no, company_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "BAYI-TEST-001",
            "Münhasır Bayilik (Tek Yetkili)",
            "Ege Perakende Ltd. Şti.",
            "Murat Aydın",
            "1234567890",
            "02324445566",
            "info@egeperakende.com",
            "İzmir / Konak",
            "Mülk Kendimize Ait",
            200,
            12.5,
            "Konak Meydanı ana cadde üzeri",
            "5.000.000 TL ve üzeri",
            "1.000.000 TL ve üzeri teminat sağlayabilirim",
            "10 Yıl ve Üzeri",
            "15.000.000 TL",
            "Bölgede güçlü dağıtım ve satış hedefi",
            "Başvuru Alındı",
            "2026-09-20T10:00:00Z",
            38.4192,
            27.1287,
            "Konak / İzmir (38.4192, 27.1287)",
            1,
            "Konak Vergi Dairesi",
            "123456789000014",
            "FAAL"
        ))
        self.conn.commit()

        cur.execute("SELECT * FROM dealer_applications WHERE tracking_code = 'BAYI-TEST-001'")
        record = cur.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record["applicant_title"], "Ege Perakende Ltd. Şti.")
        self.assertEqual(record["store_area"], 200)
        self.assertAlmostEqual(record["latitude"], 38.4192, places=4)
        self.assertAlmostEqual(record["longitude"], 27.1287, places=4)
        self.assertEqual(record["vkn_verified"], 1)
        self.assertEqual(record["tax_office"], "Konak Vergi Dairesi")
        self.assertEqual(record["mersis_no"], "123456789000014")

    def test_vkn_and_tckn_validation_algorithms(self):
        # Valid 10-digit VKNs
        self.assertTrue(validate_vkn_checksum("1234567890"))
        self.assertTrue(validate_vkn_checksum("8010452361"))
        self.assertTrue(validate_vkn_checksum("4580219638"))

        # Invalid VKN
        self.assertFalse(validate_vkn_checksum("1234567899"))
        self.assertFalse(validate_vkn_checksum("12345"))
        self.assertFalse(validate_vkn_checksum("ABCDEFGHIJ"))

        # Valid 11-digit TCKN
        self.assertTrue(validate_tckn_checksum("12345678950"))

        # Invalid TCKN
        self.assertFalse(validate_tckn_checksum("12345678951"))
        self.assertFalse(validate_tckn_checksum("02345678950"))
        self.assertFalse(validate_tckn_checksum(""))

        # MERSIS format
        self.assertTrue(validate_mersis_format("1234567890000140"))
        self.assertFalse(validate_mersis_format("12345"))

    def test_verify_company_vkn_service(self):
        res = verify_company_vkn("1234567890")
        self.assertTrue(res["valid"])
        self.assertTrue(res["is_verified"])
        self.assertEqual(res["tax_office"], "Konak Vergi Dairesi")
        self.assertEqual(res["status"], "FAAL")

        res_tckn = verify_company_vkn("12345678950")
        self.assertTrue(res_tckn["valid"])
        self.assertTrue(res_tckn["is_verified"])
        self.assertEqual(res_tckn["status"], "FAAL")

        res_invalid = verify_company_vkn("0000000000")
        self.assertFalse(res_invalid["valid"])
        self.assertFalse(res_invalid["is_verified"])

    def test_dealer_status_update(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO dealer_applications (tracking_code, applicant_title, status)
            VALUES (?, ?, ?)
        """, ("BAYI-TEST-002", "Marmara Dağıtım", "Başvuru Alındı"))
        self.conn.commit()

        cur.execute("""
            UPDATE dealer_applications
            SET status = 'Onaylandı (Bayilik Verildi)'
            WHERE tracking_code = 'BAYI-TEST-002'
        """)
        self.conn.commit()

        cur.execute("SELECT status FROM dealer_applications WHERE tracking_code = 'BAYI-TEST-002'")
        row = cur.fetchone()
        self.assertEqual(row["status"], "Onaylandı (Bayilik Verildi)")

    def test_calculate_dealer_score_tiers(self):
        # A+ Candidate: High budget, 200m2 store, 12m frontage, 10+ yrs, high collateral, verified VKN
        high_candidate = {
            "investment_budget": "5.000.000 TL ve üzeri",
            "store_area": 250,
            "store_frontage": 12.0,
            "experience_years": "10 Yıl ve Üzeri",
            "collateral_capacity": "1.000.000 TL ve üzeri teminat sağlayabilirim",
            "vkn_verified": 1
        }
        res_high = calculate_dealer_score(high_candidate)
        self.assertGreaterEqual(res_high["total_score"], 85)
        self.assertEqual(res_high["tier"], "A+")
        self.assertEqual(res_high["breakdown"]["capital_score"], 35)
        self.assertEqual(res_high["breakdown"]["location_score"], 25)

        # B Candidate: Moderate budget, 90m2 store, 5m frontage, 3 yrs
        mid_candidate = {
            "investment_budget": "1.000.000 TL - 2.500.000 TL",
            "store_area": 90,
            "store_frontage": 6.0,
            "experience_years": "2-5 Yıl",
            "collateral_capacity": "Gayrimenkul İpoteği",
            "vkn_verified": 0
        }
        res_mid = calculate_dealer_score(mid_candidate)
        self.assertIn(res_mid["tier"], ["A", "B"])
        self.assertGreaterEqual(res_mid["total_score"], 55)

        # D Candidate: Low budget, small kiosk, no experience
        low_candidate = {
            "investment_budget": "100.000 TL",
            "store_area": 20,
            "store_frontage": 2.0,
            "experience_years": "Yeni Girişimci",
            "collateral_capacity": "Yok",
            "vkn_verified": 0
        }
        res_low = calculate_dealer_score(low_candidate)
        self.assertLess(res_low["total_score"], 40)
        self.assertEqual(res_low["tier"], "D")

    def test_dealership_protocol_html_generation(self):
        dealer = {
            "tracking_code": "BAYI-TEST-PROTO",
            "applicant_title": "Anadolu Bilişim Dağıtım Ltd.",
            "tax_id": "8010452361",
            "tax_office": "Kordon Vergi Dairesi",
            "mersis_no": "801045236100019",
            "contact_name": "Ahmet Yılmaz",
            "contact_phone": "0532 111 2233",
            "contact_email": "ahmet@anadolubilisim.com",
            "target_location": "Ankara / Çankaya",
            "application_type": "Münhasır Bayilik (Tek Yetkili)",
            "store_area": 180,
            "store_frontage": 9.5,
            "investment_budget": "5.000.000 TL ve üzeri",
            "collateral_capacity": "Banka Teminat Mektubu",
            "vkn_verified": 1,
            "created_at": "2026-10-23T12:00:00"
        }
        html_doc = generate_dealership_protocol_html(dealer)
        self.assertIn("<!DOCTYPE html>", html_doc)
        self.assertIn("BAYI-TEST-PROTO", html_doc)
        self.assertIn("Anadolu Bilişim Dağıtım Ltd.", html_doc)
        self.assertIn("Türk Ticaret Kanunu", html_doc)
        self.assertIn("6769 sayılı Sınai Mülkiyet Kanunu", html_doc)
        self.assertIn("Ankara / Çankaya", html_doc)
        self.assertIn("180 m²", html_doc)
        self.assertIn("Banka Teminat Mektubu", html_doc)
        self.assertIn("@media print", html_doc)

    def test_calculate_network_analytics(self):
        sample_apps = [
            {
                "tracking_code": "APP-1",
                "applicant_title": "Firma A",
                "target_location": "İstanbul / Kadıköy",
                "status": "Onaylandı (Bayilik Verildi)",
                "application_type": "Münhasır Bayilik (Tek Yetkili)",
                "store_area": 200,
                "store_frontage": 10.0,
                "investment_budget": "5.000.000 TL ve üzeri",
                "experience_years": "10 Yıl ve Üzeri",
                "collateral_capacity": "1.000.000 TL ve üzeri teminat sağlayabilirim",
                "vkn_verified": 1
            },
            {
                "tracking_code": "APP-2",
                "applicant_title": "Firma B",
                "target_location": "İstanbul / Şişli",
                "status": "Başvuru Alındı",
                "application_type": "Franchise Şube Ortaklığı",
                "store_area": 100,
                "store_frontage": 6.0,
                "investment_budget": "1.000.000 TL - 2.500.000 TL",
                "experience_years": "2-5 Yıl",
                "collateral_capacity": "Gayrimenkul İpoteği",
                "vkn_verified": 0
            },
            {
                "tracking_code": "APP-3",
                "applicant_title": "Firma C",
                "target_location": "İzmir / Konak",
                "status": "Reddedildi",
                "application_type": "Mevcut Mağazaya Bayilik Ekleme",
                "store_area": 40,
                "store_frontage": 3.0,
                "investment_budget": "250.000 TL - 500.000 TL",
                "experience_years": "Yeni Girişimci",
                "collateral_capacity": "Kefalet",
                "vkn_verified": 1
            }
        ]
        analytics = calculate_network_analytics(sample_apps)
        self.assertEqual(analytics["total_applications"], 3)
        self.assertEqual(analytics["approved_count"], 1)
        self.assertAlmostEqual(analytics["approval_rate"], 33.3, places=1)
        self.assertEqual(analytics["vkn_verified_count"], 2)
        self.assertEqual(analytics["total_store_area"], 340.0)
        self.assertAlmostEqual(analytics["avg_store_area"], 113.3, places=1)
        self.assertGreater(analytics["estimated_investment_volume"], 0)
        self.assertTrue(len(analytics["top_locations"]) > 0)
        self.assertEqual(analytics["top_locations"][0][0], "İstanbul")
        self.assertEqual(analytics["top_locations"][0][1], 2)

    def test_dealer_network_report_html_generation(self):
        analytics = {
            "total_applications": 12,
            "status_counts": {"Başvuru Alındı": 5, "Onaylandı": 4, "Reddedildi": 3},
            "type_counts": {"Münhasır Bayilik": 8, "Franchise": 4},
            "total_store_area": 1850.0,
            "avg_store_area": 154.2,
            "avg_frontage": 8.4,
            "top_locations": [("İstanbul", 6), ("İzmir", 3), ("Ankara", 3)],
            "vkn_verified_count": 10,
            "vkn_verified_rate": 83.3,
            "avg_score": 76.5,
            "tier_distribution": {"A+": 4, "A": 5, "B": 2, "C": 1, "D": 0},
            "approved_count": 4,
            "approval_rate": 33.3,
            "estimated_investment_volume": 35000000
        }
        report_html = generate_dealer_network_report_html(analytics)
        self.assertIn("<!DOCTYPE html>", report_html)
        self.assertIn("FRANCHISE", report_html)
        self.assertIn("GELİŞTİRME RAPORU", report_html)
        self.assertIn("35.000.000 TL", report_html)
        self.assertIn("76.5/100", report_html)
        self.assertIn("İstanbul", report_html)
        self.assertIn("@media print", report_html)

    def test_generate_dealer_csv_export(self):
        sample_apps = [{
            "tracking_code": "BAYI-CSV-01",
            "application_type": "Münhasır Bayilik",
            "applicant_title": "Test Ltd.",
            "tax_id": "1234567890",
            "vkn_verified": 1,
            "tax_office": "Konak",
            "mersis_no": "123456789000014",
            "company_status": "FAAL",
            "contact_name": "Can Yılmaz",
            "contact_phone": "0555 123 4567",
            "contact_email": "can@test.com",
            "target_location": "İzmir / Konak",
            "latitude": 38.4,
            "longitude": 27.1,
            "property_status": "Kiralık",
            "store_area": 150,
            "store_frontage": 8.0,
            "investment_budget": "5.000.000 TL ve üzeri",
            "collateral_capacity": "Banka Teminatı",
            "experience_years": "5-10 Yıl",
            "target_annual_revenue": "10.000.000 TL",
            "status": "Başvuru Alındı",
            "created_at": "2026-10-23T14:00:00"
        }]
        csv_output = generate_dealer_csv_export(sample_apps)
        self.assertTrue(csv_output.startswith("\ufeff"), "UTF-8 BOM bulunmalıdır.")
        self.assertIn("Dosya No", csv_output)
        self.assertIn("BAYI-CSV-01", csv_output)
        self.assertIn("Test Ltd.", csv_output)
        self.assertIn("EVET", csv_output)
        self.assertIn("Skor", csv_output)
        self.assertIn("Kademe", csv_output)

    def test_server_handlers_direct_invocation(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO dealer_applications (
                tracking_code, applicant_title, investment_budget, store_area, store_frontage,
                experience_years, collateral_capacity, vkn_verified, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "BAYI-TEST-SRV", "Server Test A.Ş.", "5.000.000 TL ve üzeri", 180, 8.5,
            "10 Yıl ve Üzeri", "Banka Teminat Mektubu", 1, "Başvuru Alındı"
        ))
        self.conn.commit()

        handler = server.DealerHandler.__new__(server.DealerHandler)
        handler.wfile = BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        from urllib.parse import urlparse
        # Test protocol HTML
        handler.handle_protocol_html(urlparse("/api/bayi-protokol-html?code=BAYI-TEST-SRV"))
        self.assertIn(b"BAYI-TEST-SRV", handler.wfile.getvalue())

        # Test score GET
        handler.wfile = BytesIO()
        handler.handle_score_get(urlparse("/api/bayi-skorla?code=BAYI-TEST-SRV"))
        res_json = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(res_json["tracking_code"], "BAYI-TEST-SRV")
        self.assertGreaterEqual(res_json["scoring"]["total_score"], 80)

        # Test report JSON
        handler.wfile = BytesIO()
        handler.handle_network_report_json()
        report_data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertGreater(report_data["total_applications"], 0)

        # Test export CSV
        handler.wfile = BytesIO()
        handler.handle_export_csv()
        csv_bytes = handler.wfile.getvalue().decode("utf-8")
        self.assertTrue(csv_bytes.startswith("\ufeff"))
        self.assertIn("BAYI-TEST-SRV", csv_bytes)

    def test_files_exist(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "index.html")), "index.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "admin.html")), "admin.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "server.py")), "server.py bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "api.php")), "api.php bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "scripts", "bayi_vkn_validator.py")), "bayi_vkn_validator.py bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "scripts", "bayi_scoring_protocol.py")), "bayi_scoring_protocol.py bulunamadı")

if __name__ == "__main__":
    unittest.main()
