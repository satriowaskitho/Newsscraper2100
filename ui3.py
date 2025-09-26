import subprocess
import streamlit as st
from datetime import date
import sys
import pandas as pd
import os
import io
from pathlib import Path

st.set_page_config(page_title="FAKTA: Fenomena Aktual Terkini", page_icon="📰", layout="centered")

# =========================
# Header Section
# =========================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 0;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
        text-align: center;
        color: white;
    }
    .header-title {
        font-size: 3.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .header-subtitle {
        font-size: 2rem;
        font-weight: 500;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div class="header-title">📰 FAKTA</div>
    <div class="header-subtitle">Fenomena Aktual Terkini 2100</div>
</div>
""", unsafe_allow_html=True)


# =========================
# Available scrapers
# =========================
available_scrapers = [
    "auto", "all", "antaranews", "bisnis", "bloombergtechnoz",
    "cnbcindonesia", "detik", "jawapos", "katadata", "kepriantaranews", "kompas",
    "kontan", "mediaindonesia", "metrotvnews", "okezone", "tempo", "viva"
]

def find_latest_output_file(output_format, keywords=None):
    """Find the most recent output file in the output directory"""
    output_dir = Path("output")
    if not output_dir.exists():
        return None
    
    if keywords:
        keywords_list = keywords.split(",")
        keywords_short = ".".join(keywords_list[:2]) + ("..." if len(keywords_list) > 2 else "")
        pattern = f"news-watch-{keywords_short}-*.{output_format}"
    else:
        pattern = f"news-watch-*.{output_format}"
    
    files = list(output_dir.glob(pattern))
    if not files:
        files = list(output_dir.glob(f"*.{output_format}"))
    
    if files:
        return max(files, key=os.path.getctime)
    return None


# =========================
# Main Form
# =========================
with st.form("scraper_form"):
    st.write("### ⚙️ Scraper Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        keywords = st.text_input("Keywords (comma-separated)", "Harga Cabe, prabowo, BPS")
        start_date = st.date_input("Start Date", date.today())
    with col2:
        scrapers = st.multiselect("Pilih Scrapers", available_scrapers, default=["auto"])
        output_format = st.selectbox("Output Format", ["csv", "xlsx"])
    
    col3, col4 = st.columns(2)
    with col3:
        verbose = st.checkbox("Verbose logging")
    with col4:
        list_scrapers = st.checkbox("List available scrapers only")

    submitted = st.form_submit_button("🚀 Run Scraper", type="primary")


# =========================
# Handle Form Submission
# =========================
if submitted:
    cmd = [sys.executable, "-m", "newswatch.cli"]

    if keywords:
        cmd += ["--keywords", keywords]
    if start_date:
        cmd += ["--start_date", str(start_date)]
    if scrapers:
        cmd += ["--scrapers", ",".join(scrapers)]
    if output_format:
        cmd += ["--output_format", output_format]
    if verbose:
        cmd.append("--verbose")
    if list_scrapers:
        cmd.append("--list_scrapers")

    st.write("### 🔄 Execution")
    st.code(" ".join(cmd), language="bash")

    with st.spinner("🔄 Menjalankan scraper..."):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=600)
            st.success("✅ Scraping selesai!")

            # Cari file hasil terbaru
            output_file = find_latest_output_file(output_format, keywords)
            if output_file and output_file.exists():
                # Baca ke DataFrame
                if output_format == "csv":
                    df = pd.read_csv(output_file)
                else:
                    df = pd.read_excel(output_file)

                # Tampilkan hasil
                st.write("### 📊 Preview Hasil Scraping")
                st.dataframe(df)

                # Download CSV
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_buffer.getvalue(),
                    file_name="scraping_results.csv",
                    mime="text/csv",
                )

                # Download XLSX
                xlsx_buffer = io.BytesIO()
                with pd.ExcelWriter(xlsx_buffer, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name="Results")
                st.download_button(
                    label="📥 Download XLSX",
                    data=xlsx_buffer.getvalue(),
                    file_name="scraping_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

                # 🔥 Hapus file setelah dibaca
                os.remove(output_file)

            else:
                st.warning("⚠️ Output file tidak ditemukan.")

        except subprocess.TimeoutExpired:
            st.error("❌ Scraper timeout (10 menit).")
        except subprocess.CalledProcessError as e:
            st.error("❌ Error saat menjalankan scraper")
            st.code(e.stderr)


# =========================
# Footer Info
# =========================
st.write("---")
st.write("### ℹ️ Information")
st.write("""
**Expected output columns:**
1. `title` - Article title  
2. `publish_date` - Publication date  
3. `author` - Article author  
4. `content` - Article content  
5. `keyword` - Search keyword used  
6. `category` - Article category  
7. `source` - News source website  
8. `link` - Original article URL  
9. `sentiment` - Sentiment classification (positif, negatif, netral)
""")
