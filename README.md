# Kurumsal Bayilik ve Franchise Başvuru Portalı

[![CI Test Suite](https://github.com/eimza-kep/kurumsal-bayi-basvuru-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kurumsal-bayi-basvuru-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/kurumsal-bayi-basvuru-scripti/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![PHP: 7.4+](https://img.shields.io/badge/PHP-7.4%2B-purple.svg)](https://php.net)

Üretici markalar, zincir mağazalar, franchise sistemleri, distribütörlük ağları ve B2B toptan satış firmaları için; harici kütüphane bağımlılığı olmaksızın (zero-dependency) çalışan, **girişimci bayilik taleplerini toplayan**, **mağaza m² ve teminat kapasitesini analiz eden** ve **resmi başvuru ön protokolü basan** açık kaynaklı kurumsal bayi geliştirme yazılımı.

---

## 🎯 Temel Yetenekler

- **Kapsamlı Bayi & Franchise Başvuru Formu:** Başvuru türü (Münhasır, Franchise Şube, Shop-in-Shop, Bölge Distribütörü), firma unvanı, VKN, yetkili iletişim bilgileri.
- **Lokasyon ve Mağaza Kriterleri:** Hedef il/ilçe, mülkiyet durumu, mağaza alanı (m²), cadde cephe genişliği ve lokasyon trafik analizi.
- **Finansal Kapasite ve Teminat Analizi:** Yatırım bütçesi aralığı, banka teminat mektubu kapasitesi, sektörel tecrübe yılı ve hedeflenen ilk yıl cirosu.
- **Resmi Bayi Başvuru Formu Çıktısı:** Takip numaralı (`BAYI-2026-XXXX`) ve imza bloklu yazdırılabilir veya PDF olarak saklanabilir kurumsal başvuru özeti üretir.
- **Bayi Ağı Yönetim Paneli (`/admin`):**
  - Gelen bayi başvurularının bütçeye, şehre ve mağaza m²'sine göre filtrelenmesi.
  - Başvuru statü yönetimi: "Başvuru Alındı", "Ön İncelemeden Geçti", "Lokasyon & Fizibilite İncelemesinde", "Sözleşme Aşaması", "Onaylandı (Bayilik Verildi)", "Reddedildi".
  - Analitik metrikler ve başvuru havuzu yönetimi.
  - Excel uyumlu UTF-8 BOM destekli tek tıkla **CSV Dışa Aktarımı**.
- **Sıfır Bağımlılık (Zero-Dependency):**
  - **Python Motoru:** Dahili SQLite veritabanı ile tek tıkla lokalde veya sunucuda çalışır (`server.py`).
  - **PHP Motoru:** Paylaşımlı hosting ve cPanel için hazır JSON REST backend (`api.php`).
  - **Offline Mod:** İnternetsiz çalışma ve tarayıcı yerel hafızası (`localStorage`) desteği.

---

## 🚀 Hızlı Başlangıç

### Windows (Tek Tıkla Çalıştır)
1. Repoyu klonlayın veya indirin.
2. `Baslat.bat` dosyasına çift tıklayın.
3. Otomatik olarak açılır:
   - Bayi Başvuru Formu: `http://localhost:8093`
   - Bayi Yönetim Paneli: `http://localhost:8093/admin`

### Linux & macOS
```bash
git clone https://github.com/eimza-kep/kurumsal-bayi-basvuru-scripti.git
cd kurumsal-bayi-basvuru-scripti
chmod +x baslat.sh
./baslat.sh
```

### PHP / Paylaşımlı Hosting
Dosyaları sunucunuzdaki `/bayi/` veya `/franchise/` dizinine yükleyin. `api.php` otomatik olarak JSON veritabanını oluşturup yönetecektir.

---

## 📊 Mimari ve Dosya Yapısı

```
kurumsal-bayi-basvuru-scripti/
├── index.html              # Bayi başvuru formu ve başvuru evrakı çıktısı
├── admin.html              # Bayilik geliştirme ve inceleme takip paneli
├── server.py               # Standalone Python SQLite HTTP sunucusu (Port 8093)
├── api.php                 # PHP tabanlı REST backend
├── Baslat.bat              # Windows tek tıkla başlatıcı
├── baslat.sh               # Linux / macOS başlatıcı
├── scripts/
│   └── test_bayi.py        # Otomatik test paketi
├── .github/
│   └── workflows/ci.yml    # GitHub Actions CI testi
└── README.md               # Dokümantasyon
```

---

## 🧪 Testleri Çalıştırma

```bash
python scripts/test_bayi.py
```

---

## ⚖️ Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynak olarak sunulmuştur.
