# 📰 NewsScraper2100

**NewsScraper2100** adalah pengembangan dari proyek [okkymabruri/news-watch](https://github.com/okkymabruri/news-watch), dengan tambahan antarmuka web interaktif menggunakan **Streamlit**, serta scraping berita yang difokuskan untuk wilayah **Kepulauan Riau**.

---

## 📸 Preview Antarmuka

<div align="center">
  <img src="assets/preview.png" alt="NewsScraper2100 UI Preview" width="80%">
  <p><i>Tampilan antarmuka NewsScraper2100</i></p>
</div>

> 💡 Ganti `assets/preview.png` dengan path gambar sesuai dengan struktur repo kamu.

---

## 🚀 Fitur Utama

- ✅ Web antarmuka berbasis **Streamlit**
- ✅ Scraping berita online dari berbagai sumber nasional & lokal
- ✅ Filter fokus untuk berita wilayah **Kepulauan Riau**
- ✅ Visualisasi data seperti wordcloud & grafik
- ✅ Ekspor data hasil scraping ke file `.csv`
- ✅ Input kata kunci pencarian berita

---

## 🧰 Teknologi yang Digunakan

- Python 3.10+
- Streamlit
- Requests & BeautifulSoup
- Pandas
- Wordcloud & Matplotlib
- Regex & DateTime

---

## 📦 Instalasi

1. **Clone repositori ini:**
```bash
git clone https://github.com/username/newsscraper2100.git
cd newsscraper2100
```

2. **(Opsional) Buat virtual environment:**
```bash
python -m venv env
.\env\Scripts\activate
```

3. **Install dependensi:**
```bash
pip install -r requirements.txt
```

4. **Jalankan aplikasi:**
```bash
streamlit run app.py
```

## 🗺️ Target Sumber & Wilayah

Proyek ini secara khusus menargetkan scraping berita dari:
Media nasional: Antaranews, Kompas, Detik, dll.
Media lokal: Batamnews, Tribun Batam, dll.
Dengan filter berita yang relevan terhadap wilayah Kepulauan Riau

## 📁 Struktur Folder
newsscraper2100/
├── app.py                # Streamlit app utama
├── scraper/              # Modul scraper
│   └── kpi_scraper.py    # Scraper untuk berita Kepri
├── assets/               # Gambar UI, wordcloud, dll
├── data/                 # Data hasil scraping
├── requirements.txt
└── README.md

## 🙏 Kredit

🔗 Original project: okkymabruri/news-watch
🚀 Dikembangkan oleh: Muhammad Rizki

## 📫 Kontak

✉️ Email: muhammad.rizki@email.com
🌐 LinkedIn: linkedin.com/in/namakamu
