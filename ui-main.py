import subprocess
import streamlit as st
from datetime import date
import sys
import pandas as pd
import os
import glob
import time
from pathlib import Path

st.set_page_config(page_title="FENALTI: Fenomena Multi-Fungsi", page_icon="📰", layout="centered")

# Header Section
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
        font-size: 2 rem;
        font-weight: 500;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div class="header-title">📰 FENALTI</div>
    <div class="header-subtitle">Fenomena Multi-Fungsi</div>
</div>
""", unsafe_allow_html=True)

# st.title("📰 Web Scraper Berita 2100")
# st.write("Isi form berikut untuk menjalankan scraper berita.")

# Available scrapers
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
        # Create search pattern based on keywords
        keywords_list = keywords.split(",")
        keywords_short = ".".join(keywords_list[:2]) + ("..." if len(keywords_list) > 2 else "")
        pattern = f"news-watch-{keywords_short}-*.{output_format}"
    else:
        pattern = f"news-watch-*.{output_format}"
    
    files = list(output_dir.glob(pattern))
    if not files:
        # Fallback: look for any files with the format
        files = list(output_dir.glob(f"*.{output_format}"))
    
    if files:
        # Return the most recent file
        return max(files, key=os.path.getctime)
    return None

def show_output_preview(file_path, output_format):
    """Show preview of the output file"""
    try:
        if output_format == "csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        st.write("### 📊 File Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rows", len(df))
        with col2:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            st.metric("File Size", f"{file_size_mb:.2f} MB")
        with col3:
            if duration is not None:
                st.metric("Scraping Time", f"{duration:.2f} s")
        
        st.write("### 🔍 Preview Hasil")
        st.dataframe(df.set_index(pd.Index(range(1, len(df)+1))))
        
        # Download button
        with open(file_path, "rb") as f:
            mime_type = "text/csv" if output_format == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            st.download_button(
                label=f"📥 Download hasil ({output_format.upper()})",
                data=f,
                file_name=file_path.name,
                mime=mime_type
            )
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error membaca file: {e}")
        return None

# Show existing output files at the top

st.write("---")
st.write("### 📁 Recent Output Files")

output_dir = Path("output")
if output_dir.exists():
    csv_files = list(output_dir.glob("*.csv"))
    xlsx_files = list(output_dir.glob("*.xlsx"))
    
    if csv_files or xlsx_files:
        col1, col2 = st.columns(2)
        
        with col1:
            if csv_files:
                st.write("**CSV Files:**")
                for file in sorted(csv_files, key=os.path.getctime, reverse=True)[:3]:
                    file_time = pd.Timestamp(os.path.getctime(file), unit='s').strftime('%Y-%m-%d %H:%M')
                    st.write(f"• {file.name} ({file_time})")
            
        with col2:
            if xlsx_files:
                st.write("**XLSX Files:**")
                for file in sorted(xlsx_files, key=os.path.getctime, reverse=True)[:3]:
                    file_time = pd.Timestamp(os.path.getctime(file), unit='s').strftime('%Y-%m-%d %H:%M')
                    st.write(f"• {file.name} ({file_time})")
    else:
        st.info("Belum ada file output. Jalankan scraper untuk membuat file baru.")
else:
    st.info("Folder output belum ada. Akan dibuat saat menjalankan scraper.")

st.write("---")

# Main form
with st.form("scraper_form"):
    st.write("### ⚙️ Scraper Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        keywords = st.text_input("Keywords (comma-separated)", "Harga Cabe, prabowo, BPS")
        start_date = st.date_input("Start Date", date.today())
        
    with col2:
        scrapers = st.multiselect("Pilih Scrapers", available_scrapers, default=["auto"])
        output_format = st.selectbox("Output Format", ["csv", "xlsx"])

    submitted = st.form_submit_button("🚀 Run Scraper", type="primary")

# Handle form submission
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

    st.write("---")
    st.write("### 🔄 Execution")
    st.code(" ".join(cmd), language="bash")

    # Progress indicator
    with st.spinner("🔄 Menjalankan scraper..."):
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=600)
            duration = time.time() - start_time
            st.success("✅ Scraping selesai!")
            
            # Show command output
            if result.stdout:
                with st.expander("📄 Command Output", expanded=False):
                    st.code(result.stdout)
            
            # Find and display the output file
            output_file = find_latest_output_file(output_format, keywords)
            
            if output_file and output_file.exists():
                st.write("---")
                st.write(f"### 📈 Results from: `{output_file.name}`")
                show_output_preview(output_file, output_format)
            else:
                st.warning("⚠️ Output file not found. Check if scraping was successful.")
                
        except subprocess.TimeoutExpired:
            st.error("❌ Scraper timed out after 10 minutes")
        except subprocess.CalledProcessError as e:
            st.error("❌ Error saat menjalankan scraper")
            st.code(e.stderr)
            
            # Still try to show any partial results
            output_file = find_latest_output_file(output_format, keywords)
            if output_file and output_file.exists():
                st.write("---")
                st.write("### 📈 Partial Results (if any)")
                show_output_preview(output_file, output_format)

# Footer
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
""")