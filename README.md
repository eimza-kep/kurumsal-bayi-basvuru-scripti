# Kurumsal Bayilik ve Franchise Başvuru Portalı

[![CI Test Suite](https://github.com/eimza-kep/kurumsal-bayi-basvuru-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kurumsal-bayi-basvuru-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/kurumsal-bayi-basvuru-scripti/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![PHP: 7.4+](https://img.shields.io/badge/PHP-7.4%2B-purple.svg)](https://php.net)
[![Docker Support](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](Dockerfile)

Üretici markalar, zincir mağazalar, franchise sistemleri, distribütörlük ağları ve B2B toptan satış firmaları için; harici kütüphane bağımlılığı olmaksızın (zero-dependency) çalışan, **Leaflet / OpenStreetMap İnteraktif Mağaza Pinleme**, **GİB Vergi Levhası ve MERSİS VKN Doğrulama Motoru**, **A4 Resmi Bayilik Ön Protokolü**, **Aday Puanlama/Skorlama Motoru** ve **İcra Kurulu Bayilik Ağı Analitik Raporu** barındıran açık kaynaklı kurumsal bayi geliştirme ve acente yönetim yazılımı.

---

## 🎯 Temel Yetenekler ve Özellikler

- **🏢 Kapsamlı Bayi & Franchise Başvuru Formu (`index.html`):**
  - **Başvuru Türleri:** Münhasır Bayilik (Tek Yetkili), Franchise Şube Ortaklığı, Mevcut Mağazaya Bayilik Ekleme (Shop-in-Shop), Bölge Dağıtıcı Distribütörlük.
  - **🔍 GİB & MERSİS Otomatik VKN / TCKN Doğrulama:** 10 haneli tüzel kişi Vergi Kimlik Numarası (VKN) ve 11 haneli şahıs şirketi TCKN kontrol haneleri algoritmik olarak anlık doğrulanır. Şirket unvanı, vergi dairesi ve MERSİS sicil numarası otomatik sorgulanarak onaylanır.
- **📍 İnteraktif Mağaza Lokasyonu Harita Pinleme (Leaflet & OpenStreetMap):**
  - API anahtarı gerektirmeyen hafif Leaflet.js ve OpenStreetMap entegrasyonu.
  - Aday bayi, açmayı planladığı mağaza/şube lokasyonunu haritada tıklayarak veya sürükleyerek işaretler.
  - Enlem (`latitude`), boylam (`longitude`) ve harita koordinatları otomatik kaydedilir.
  - Tek tıkla "Konumumu Bul" (HTML5 Geolocation) desteği.
- **⭐ Bayi Skorlama ve Aday Yeterlilik Motoru (`bayi_scoring_protocol.py`):**
  - Sermaye ve Bütçe Yeterliliği (%35), Mağaza Alanı ve Vitrin Cephesi (%25), Sektörel Deneyim (%20), Teminat Kapasitesi ve VKN Doğrulanmışlık (%20) parametreleriyle 100 üzerinden ağırlıklı yeterlilik puanı hesaplama.
  - **A+ / A / B / C / D Segmentasyonu:** Adayın münhasır bayilik, standart franchise veya şartlı onay durumunu anında sınıflandırma.
- **📄 A4 Resmi Bayilik & Franchise Ön Protokolü ve Uygunluk Belgesi:**
  - 6102 sayılı TTK ve 6769 sayılı Sınai Mülkiyet Kanunu mevzuatına uygun tanzim edilen kurumsal antetli, bölge koruması (münhasırlık), ciro primi, teminat ve e-imza/kaşe bloklu resmi A4 belge motoru (`/api/bayi-protokol-html`).
- **📊 İcra Kurulu Bayilik Ağı & Analitik Raporu:**
  - Kümülatif yatırım hacmi, ortalama mağaza metrekareleri, il/bölge dağılımları ve dönüşüm oranlarını görselleştiren A4 formatında yönetim kurulu raporu (`/api/bayi-raporu-html` & `/api/bayi-raporu-json`).
- **🤝 Bayi Ağı Yönetim Paneli (`admin.html`):**
  - **🗺️ Harita Önizleme & Google Maps Entegrasyonu:** İnceleme detayında pinlenen mağaza konumunu Leaflet haritası üzerinde gösterir ve tek tıkla `Google Haritalar'da Aç` köprüsü sunar.
  - **✅ GİB/MERSİS ve Skor Rozetleri:** Vergi dairesi onaylı şirketlerin ve yeterlilik puanlarının tabloda ve detay modalında özel rozetlerle listelenmesi.
  - **6 Aşamalı Statü Yönetimi:** *Başvuru Alındı*, *Ön İncelemeden Geçti*, *Lokasyon & Fizibilite İncelemesinde*, *Sözleşme Aşaması*, *Onaylandı (Bayilik Verildi)*, *Reddedildi*.
  - **Excel / CSV Dışa Aktarımı:** UTF-8 BOM destekli, Türkçe karakter sorunu yaşatmayan tam kapsamlı koordinat, skor ve VKN detaylı veri dökümü (`/api/export-csv`).
- **Sıfır Bağımlılık (Zero-Dependency) Çift Motorlu Mimari:**
  - **Python Motoru:** Dahili SQLite veritabanı ile tek tıkla lokalde veya sunucuda çalışır (`server.py`).
  - **PHP Motoru:** Paylaşımlı hosting ve cPanel için hazır JSON REST backend (`api.php`).
  - **Offline Mod:** İnternetsiz çalışma ve tarayıcı yerel hafızası (`localStorage`) desteği.

---

## 🚀 Hızlı Başlangıç ve Kurulum Rehberi

### Seçenek 1: Windows (Tek Tıkla Çalıştır)
1. Repoyu klonlayın veya indirin:
   ```bash
   git clone https://github.com/eimza-kep/kurumsal-bayi-basvuru-scripti.git
   cd kurumsal-bayi-basvuru-scripti
   ```
2. `Baslat.bat` dosyasına çift tıklayın.
3. Tarayıcınızda otomatik olarak açılır:
   - Bayi Başvuru Formu: `http://localhost:8093`
   - Bayi Yönetim Paneli: `http://localhost:8093/admin`
   - İcra Kurulu Raporu: `http://localhost:8093/api/bayi-raporu-html`

### Seçenek 2: Linux & macOS
```bash
git clone https://github.com/eimza-kep/kurumsal-bayi-basvuru-scripti.git
cd kurumsal-bayi-basvuru-scripti
chmod +x baslat.sh
./baslat.sh
```

### Seçenek 3: Docker ile Çalıştırma
```bash
# Docker imajını derleyin ve başlatın
docker build -t kurumsal-bayi-scripti .
docker run -d -p 8093:8093 --name kurumsal-bayi kurumsal-bayi-scripti

# Tarayıcıdan erişin:
# http://localhost:8093
```

### Seçenek 4: PHP / Paylaşımlı Hosting (cPanel / Plesk)
Dosyaları sunucunuzdaki `/bayi/` veya `/franchise/` ana dizinine yükleyin. `api.php` otomatik olarak JSON veritabanını (`bayi_basvurular.json`) oluşturup yönetecektir.

---

## 🔌 REST API Referansı

| Metot | Uç Nokta (Endpoint) | Açıklama |
| :--- | :--- | :--- |
| `POST` | `/api/bayi-basvuru` | Yeni bayi başvurusu kaydeder (`latitude`, `longitude`, `vkn_verified` destekli). |
| `GET` | `/api/bayiler` | Tüm bayi başvuru listesini yeterlilik skorları ve kademeleriyle döndürür. |
| `POST` | `/api/durum-guncelle` | Başvuru sürecini günceller (`tracking_code`, `status`). |
| `GET` | `/api/bayi-protokol-html?code=...` | Resmi TTK & 6769 SMK uyumlu A4 ön protokol belgesini HTML olarak döndürür. |
| `GET` | `/api/bayi-skorla?code=...` | Belirtilen bayi başvurusunun puanlama ve kademe analizini JSON olarak döndürür. |
| `POST` | `/api/bayi-skorla` | Gönderilen JSON başvuru parametrelerine göre anlık yeterlilik skorunu hesaplar. |
| `GET` | `/api/bayi-raporu-html` | İcra Kurulu & Satış Direktörlüğü A4 Bayilik Ağı Yönetim Raporu'nu üretir. |
| `GET` | `/api/bayi-raporu-json` | Bayi başvuru havuzu ve dağılım analitiklerini JSON olarak döndürür. |
| `GET` | `/api/export-csv` | Excel uyumlu UTF-8 BOM CSV formatında tüm veriyi dışa aktarır. |
| `GET` | `/api/vkn-sorgula?vkn=...` | VKN/TCKN kontrol hanesi, vergi dairesi ve MERSİS sicilini doğrular. |
| `POST` | `/api/vkn-dogrula` | JSON gövdesi ile kurumsal VKN doğrulama servisini tetikler. |
| `GET` | `/health` | Servis sağlık durumunu ve port bilgisini döndürür. |

---

## 📊 Mimari ve Dosya Yapısı

```
kurumsal-bayi-basvuru-scripti/
├── index.html                    # Bayi başvuru formu, Leaflet harita pinleme ve başvuru çıktısı
├── admin.html                    # Bayilik geliştirme paneli (Harita, skorlama ve protokol bağlantılı)
├── server.py                     # Standalone Python SQLite HTTP sunucusu (Port 8093)
├── api.php                       # PHP tabanlı REST backend
├── Baslat.bat                    # Windows tek tıkla başlatıcı
├── baslat.sh                     # Linux / macOS başlatıcı
├── Dockerfile                    # Docker konteyner konfigürasyonu
├── scripts/
│   ├── bayi_vkn_validator.py     # GİB VKN, TCKN ve MERSİS doğrulama motoru
│   ├── bayi_scoring_protocol.py  # A4 Ön protokol üretici, puanlama motoru ve ağ analitikleri
│   └── test_bayi.py              # Otomatik birim test paketi (13/13 test)
├── .github/
│   └── workflows/ci.yml          # GitHub Actions CI testi
└── README.md                     # Kapsamlı dokümantasyon
```

---

## 🧪 Testleri Çalıştırma

Tüm doğrulama motoru, puanlama algoritmaları, protokol üretimi ve veri tabanı akışları birim testlerle korunmaktadır:

```bash
python scripts/test_bayi.py
```

---

## 🌐 Kurumsal & E-Dönüşüm Açık Kaynak Ekosistemi

Bu bayilik ve franchise başvuru portali, [@eimza-kep](https://github.com/eimza-kep) açık kaynak ekosisteminin B2B kanal yönetimi bileşenidir. İlgili diğer araçlar:

* 🏢 [kobi-finans-yonetim-excel-sablonlari](https://github.com/eimza-kep/kobi-finans-yonetim-excel-sablonlari) - Bayi cari hesap takibi, teminat mektubu ve vade yaşlandırma şablonları.
* 📨 [kep-adresi-dogrulayici](https://github.com/eimza-kep/kep-adresi-dogrulayici) - Aday bayilerin resmi kurumsal KEP adresi sözdizim ve KEPHS kontrolü.
* 📄 [python-pdf-eimza-dogrulayici](https://github.com/eimza-kep/python-pdf-eimza-dogrulayici) - Karşılıklı imzalanan dijital bayilik ve gizlilik (NDA) sözleşmelerini doğrulama aracı.
* 🔒 [kurumsal-kvkk-basvuru-scripti](https://github.com/eimza-kep/kurumsal-kvkk-basvuru-scripti) - Bayi yetkilisi kişisel verileri aydınlatma ve açık rıza portali.
* 🌟 [awesome-turkiye-e-donusum](https://github.com/eimza-kep/awesome-turkiye-e-donusum) - Türkiye e-Dönüşüm açık kaynak araçları ve kütüphaneleri kürasyonu.

---

## ⚖️ Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynak olarak sunulmuştur.
