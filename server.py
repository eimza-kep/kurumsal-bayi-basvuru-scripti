import http.server
import socketserver
import json
import sqlite3
import os
import sys
import random
from urllib.parse import urlparse

PORT = 8093
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bayi_basvurular.db")

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
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/bayi-basvuru":
            self.handle_create_dealer()
        elif path == "/api/durum-guncelle":
            self.handle_update_status()
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

    def handle_create_dealer(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code") or f"BAYI-2026-{random.randint(1000, 9999)}"

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO dealer_applications (
                    tracking_code, application_type, applicant_title, contact_name,
                    tax_id, contact_phone, contact_email, target_location,
                    property_status, store_area, store_frontage, location_details,
                    investment_budget, collateral_capacity, experience_years,
                    target_annual_revenue, business_vision, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                data.get("created_at", "")
            ))
            conn.commit()
            conn.close()

            self.send_json({"status": "success", "tracking_code": tracking_code})
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
