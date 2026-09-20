import unittest
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

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

    def test_dealer_insert_and_retrieve(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO dealer_applications (
                tracking_code, application_type, applicant_title, contact_name,
                tax_id, contact_phone, contact_email, target_location,
                property_status, store_area, store_frontage, location_details,
                investment_budget, collateral_capacity, experience_years,
                target_annual_revenue, business_vision, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            "2026-09-20T10:00:00Z"
        ))
        self.conn.commit()

        cur.execute("SELECT * FROM dealer_applications WHERE tracking_code = 'BAYI-TEST-001'")
        record = cur.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record["applicant_title"], "Ege Perakende Ltd. Şti.")
        self.assertEqual(record["store_area"], 200)

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
        self.assertTrue(os.path.exists(os.path.join(base_dir, "api.php")), "api.php bulunamadı")

if __name__ == "__main__":
    unittest.main()
