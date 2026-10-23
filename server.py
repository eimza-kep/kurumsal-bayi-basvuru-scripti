# -*- coding: utf-8 -*-
import http.server
import socketserver
import json
import sqlite3
import os
import sys
import random
from urllib.parse import urlparse, parse_qs

# Ensure UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
try:
    from bayi_vkn_validator import verify_company_vkn, validate_vkn_checksum, validate_tckn_checksum
except ImportError:
    verify_company_vkn = None

try:
    from bayi_scoring_protocol import (
        calculate_dealer_score,
        generate_dealership_protocol_html,
        calculate_network_analytics,
        generate_dealer_network_report_html,
        generate_dealer_csv_export
    )
except ImportError:
    calculate_dealer_score = None
    generate_dealership_protocol_html = None
    calculate_network_analytics = None
    generate_dealer_network_report_html = None
    generate_dealer_csv_export = None

PORT = int(os.environ.get("PORT", 8093))
DB_FILE = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "bayi_basvurular.db"))

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dealer_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_code TEXT UNIQUE,
            application_type TEXT,
            applicant_title TEXT,
            contact_name TEXT,
            tax_id TEXT,
            contact_phone TEXT,
            contact_email TEXT,
            target_location TEXT,
            property_status TEXT,
            store_area INTEGER,
            store_frontage REAL,
            location_details TEXT,
            investment_budget TEXT,
            collateral_capacity TEXT,
            experience_years TEXT,
            target_annual_revenue TEXT,
            business_vision TEXT,
            status TEXT DEFAULT 'Başvuru Alındı',
            created_at TEXT
        )
    """)
    conn.commit()

    # Dynamic migrations for Map Pinning (Issue #1) and VKN / MERSIS (Issue #2)
    cur.execute("PRAGMA table_info(dealer_applications)")
    existing_cols = [row[1] for row in cur.fetchall()]

    new_columns = [
        ("latitude", "REAL DEFAULT 0.0"),
        ("longitude", "REAL DEFAULT 0.0"),
        ("map_address", "TEXT DEFAULT ''"),
        ("vkn_verified", "INTEGER DEFAULT 0"),
        ("tax_office", "TEXT DEFAULT ''"),
        ("mersis_no", "TEXT DEFAULT ''"),
        ("company_status", "TEXT DEFAULT 'FAAL'")
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            try:
                cur.execute(f"ALTER TABLE dealer_applications ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass

    conn.commit()
    conn.close()

class DealerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self.send_file("index.html", "text/html; charset=utf-8")
        elif path in ("/admin", "/admin.html"):
            self.send_file("admin.html", "text/html; charset=utf-8")
        elif path == "/health":
            self.send_json({"status": "ok", "app": "kurumsal-bayi-basvuru-scripti", "port": PORT})
        elif path == "/api/bayiler":
            self.handle_get_dealers()
        elif path == "/api/vkn-sorgula":
            self.handle_vkn_lookup(parsed)
        elif path == "/api/bayi-protokol-html":
            self.handle_protocol_html(parsed)
        elif path == "/api/bayi-skorla":
            self.handle_score_get(parsed)
        elif path == "/api/bayi-raporu-json":
            self.handle_network_report_json()
        elif path == "/api/bayi-raporu-html":
            self.handle_network_report_html()
        elif path == "/api/export-csv":
            self.handle_export_csv()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/bayi-basvuru":
            self.handle_create_dealer()
        elif path == "/api/durum-guncelle":
            self.handle_update_status()
        elif path == "/api/vkn-dogrula":
            self.handle_vkn_post_validate()
        elif path == "/api/bayi-skorla":
            self.handle_score_post()
        else:
            self.send_error(404, "Endpoint not found")

    def send_file(self, filename, content_type):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if not os.path.exists(filepath):
            self.send_error(404, f"File {filename} not found")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, content_str, status=200):
        body = content_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_csv(self, csv_str, filename="bayi_basvurulari.csv", status=200):
        body = csv_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def handle_vkn_lookup(self, parsed):
        qs = parse_qs(parsed.query)
        vkn = qs.get("vkn", [""])[0].strip()
        title = qs.get("title", [""])[0].strip()
        if not vkn:
            self.send_json({"valid": False, "error": "VKN veya TCKN parametresi eksik."}, status=400)
            return

        if verify_company_vkn:
            res = verify_company_vkn(vkn, title)
            self.send_json(res)
        else:
            self.send_json({"valid": True, "tax_id": vkn, "status": "FAAL", "tax_office": "GİB Vergi Dairesi"})

    def handle_vkn_post_validate(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            vkn = data.get("tax_id") or data.get("vkn") or ""
            title = data.get("applicant_title") or data.get("company_title") or ""
            if verify_company_vkn:
                res = verify_company_vkn(vkn, title)
                self.send_json(res)
            else:
                self.send_json({"valid": True, "tax_id": vkn, "status": "FAAL", "tax_office": "GİB Vergi Dairesi"})
        except Exception as e:
            self.send_json({"valid": False, "error": str(e)}, status=500)

    def handle_create_dealer(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code") or f"BAYI-2026-{random.randint(1000, 9999)}"

            lat = float(data.get("latitude") or 0.0)
            lng = float(data.get("longitude") or 0.0)
            map_addr = data.get("map_address") or ""
            vkn_ver = 1 if data.get("vkn_verified") else 0
            tax_off = data.get("tax_office") or ""
            mersis = data.get("mersis_no") or ""
            c_status = data.get("company_status") or "FAAL"

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
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
                tracking_code,
                data.get("application_type", ""),
                data.get("applicant_title", ""),
                data.get("contact_name", ""),
                data.get("tax_id", ""),
                data.get("contact_phone", ""),
                data.get("contact_email", ""),
                data.get("target_location", ""),
                data.get("property_status", ""),
                int(data.get("store_area", 0)),
                float(data.get("store_frontage", 0)),
                data.get("location_details", ""),
                data.get("investment_budget", ""),
                data.get("collateral_capacity", ""),
                data.get("experience_years", ""),
                data.get("target_annual_revenue", ""),
                data.get("business_vision", ""),
                data.get("status", "Başvuru Alındı"),
                data.get("created_at", ""),
                lat,
                lng,
                map_addr,
                vkn_ver,
                tax_off,
                mersis,
                c_status
            ))
            conn.commit()
            conn.close()

            self.send_json({
                "status": "success",
                "tracking_code": tracking_code,
                "vkn_verified": bool(vkn_ver),
                "map_pinned": bool(lat != 0.0 and lng != 0.0)
            })
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_get_dealers(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM dealer_applications ORDER BY id DESC")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

            # Attach scoring summary if calculate_dealer_score is available
            if calculate_dealer_score:
                for r in rows:
                    sc = calculate_dealer_score(r)
                    r["score"] = sc["total_score"]
                    r["tier"] = sc["tier"]
                    r["tier_title"] = sc["tier_title"]

            self.send_json(rows)
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_update_status(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code")
            new_status = data.get("status")

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("UPDATE dealer_applications SET status = ? WHERE tracking_code = ?", (new_status, tracking_code))
            conn.commit()
            conn.close()

            self.send_json({"status": "success", "updated": tracking_code})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_protocol_html(self, parsed):
        if not generate_dealership_protocol_html:
            self.send_html("<h3>Protokol motoru yüklenemedi.</h3>", status=500)
            return

        qs = parse_qs(parsed.query)
        code = qs.get("code", [""])[0].strip()
        app_id = qs.get("id", [""])[0].strip()

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if code:
            cur.execute("SELECT * FROM dealer_applications WHERE tracking_code = ?", (code,))
        elif app_id:
            cur.execute("SELECT * FROM dealer_applications WHERE id = ?", (app_id,))
        else:
            cur.execute("SELECT * FROM dealer_applications ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()

        if not row:
            self.send_html("<h3>Kayıt bulunamadı.</h3>", status=404)
            return

        app_data = dict(row)
        html_content = generate_dealership_protocol_html(app_data)
        self.send_html(html_content)

    def handle_score_get(self, parsed):
        if not calculate_dealer_score:
            self.send_json({"error": "Skorlama motoru yüklenemedi"}, status=500)
            return

        qs = parse_qs(parsed.query)
        code = qs.get("code", [""])[0].strip()
        app_id = qs.get("id", [""])[0].strip()

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if code:
            cur.execute("SELECT * FROM dealer_applications WHERE tracking_code = ?", (code,))
        elif app_id:
            cur.execute("SELECT * FROM dealer_applications WHERE id = ?", (app_id,))
        else:
            cur.execute("SELECT * FROM dealer_applications ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()

        if not row:
            self.send_json({"error": "Kayıt bulunamadı"}, status=404)
            return

        score_res = calculate_dealer_score(dict(row))
        self.send_json({
            "tracking_code": row["tracking_code"],
            "applicant_title": row["applicant_title"],
            "scoring": score_res
        })

    def handle_score_post(self):
        if not calculate_dealer_score:
            self.send_json({"error": "Skorlama motoru yüklenemedi"}, status=500)
            return

        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            score_res = calculate_dealer_score(data)
            self.send_json(score_res)
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def handle_network_report_json(self):
        if not calculate_network_analytics:
            self.send_json({"error": "Analitik motoru yüklenemedi"}, status=500)
            return

        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM dealer_applications ORDER BY id DESC")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

            analytics = calculate_network_analytics(rows)
            self.send_json(analytics)
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def handle_network_report_html(self):
        if not generate_dealer_network_report_html:
            self.send_html("<h3>Rapor motoru yüklenemedi.</h3>", status=500)
            return

        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM dealer_applications ORDER BY id DESC")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

            analytics = calculate_network_analytics(rows)
            html_content = generate_dealer_network_report_html(analytics)
            self.send_html(html_content)
        except Exception as e:
            self.send_html(f"<h3>Rapor üretilirken hata oluştu: {str(e)}</h3>", status=500)

    def handle_export_csv(self):
        if not generate_dealer_csv_export:
            self.send_json({"error": "CSV motoru yüklenemedi"}, status=500)
            return

        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM dealer_applications ORDER BY id DESC")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

            csv_content = generate_dealer_csv_export(rows)
            self.send_csv(csv_content, filename="bayi_basvurulari.csv")
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", PORT))
    print(f"🚀 Kurumsal Bayi Portali Baslatildi: http://localhost:{port}")
    print(f"🤝 Bayilik Yonetim Paneli: http://localhost:{port}/admin")
    with socketserver.TCPServer(("", port), DealerHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu kapatildi.")
