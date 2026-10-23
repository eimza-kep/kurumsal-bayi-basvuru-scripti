import unittest
import os
import sys
import sqlite3

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
            "2.500.000 TL - 5.000.000 TL",
            "1.000.000 TL ve üzeri teminat sağlayabilirim",
            "5-10 Yıl",
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

    def test_files_exist(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "index.html")), "index.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "admin.html")), "admin.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "server.py")), "server.py bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "api.php")), "api.php bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "scripts", "bayi_vkn_validator.py")), "bayi_vkn_validator.py bulunamadı")

if __name__ == "__main__":
    unittest.main()
