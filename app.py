import streamlit as st
import pandas as pd
import PyPDF2
import os
import re
from groq import Groq

# Konfigurasi Halaman
st.set_page_config(page_title="PayrollAudit AI", page_icon="🤖", layout="wide")

# ==========================================
# CUSTOM CSS UNTUK TAMPILAN MODERN & ELEGAN
# ==========================================
def apply_custom_style():
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
            color: #102a43;
        }
        header[data-testid="stHeader"] {
            background-color: rgba(240, 244, 248, 0.8);
            backdrop-filter: blur(8px);
        }
        /* Styling Sidebar */
        [data-testid="stSidebar"] {
            background-color: #0a2540;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: #f8fafc !important;
        }
        /* Perbaikan Kontras Kotak Alert (Data Aktif / Belum Unggah) di Sidebar */
        [data-testid="stSidebar"] [data-testid="stAlert"] {
            background-color: rgba(255, 255, 255, 0.12) !important;
            border: 1px solid rgba(255, 255, 255, 0.25) !important;
            border-radius: 10px !important;
        }
        [data-testid="stSidebar"] [data-testid="stAlert"] p {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        /* Perbaikan Kontras Tombol Logout di Sidebar */
        [data-testid="stSidebar"] .stButton > button {
            background-color: #dc2626 !important;
            color: #ffffff !important;
            border: 1px solid #ef4444 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #b91c1c !important;
            border-color: #fca5a5 !important;
        }
        [data-testid="stSidebar"] .stButton > button p {
            color: #ffffff !important;
        }
        /* Banner Utama */
        .main-banner {
            background: linear-gradient(90deg, #0a2540 0%, #103c68 100%);
            padding: 1.8rem 2.2rem;
            border-radius: 16px;
            color: white;
            box-shadow: 0 10px 25px rgba(10, 37, 64, 0.15);
            margin-bottom: 1.5rem;
            border-left: 6px solid #f59e0b;
        }
        .main-banner h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 800;
            color: #ffffff;
        }
        .main-banner span.ai-accent {
            color: #fbbf24;
        }
        .main-banner p {
            margin: 0.4rem 0 0 0;
            font-size: 0.95rem;
            color: #cbd5e1;
        }
        .card-box {
            background-color: #ffffff;
            padding: 1.4rem;
            border-radius: 14px;
            box-shadow: 0 4px 15px rgba(16, 42, 67, 0.06);
            border: 1px solid #e2e8f0;
            margin-bottom: 1rem;
        }
        [data-testid="stFileUploader"] {
            background-color: #ffffff;
            padding: 1.2rem;
            border-radius: 12px;
            border: 1.5px dashed #3b82f6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #0284c7 0%, #1d4ed8 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.6rem 1.8rem;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(29, 78, 216, 0.25);
        }
        [data-testid="stForm"] {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(10, 37, 64, 0.1);
            border: 1px solid #e2e8f0;
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# ==========================================
# TAHAP 1: MULAI & LOGIN PENGGUNA
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    col_l, col_center, col_r = st.columns([1, 2, 1])
    with col_center:
        st.markdown("""
            <div class="main-banner" style="text-align: center; border-left: none; border-bottom: 5px solid #f59e0b;">
                <h1>🤖 PayrollAudit <span class="ai-accent">AI</span></h1>
                <p>Sistem Audit Gaji, Tunjangan, Lembur & Potongan Karyawan</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("### 🔐 Akses Sistem Auditor")
            st.caption("Silakan masukkan kredensial Anda untuk memulai sesi audit.")
            username = st.text_input("Username Auditor", placeholder="Masukkan username (admin)")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            st.write("")
            submit = st.form_submit_button("Masuk ke Sistem", type="primary", use_container_width=True)
            
            if submit:
                if username == "admin" and password == "audit123":
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Username atau password salah! (Gunakan: admin / audit123)")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ==========================================
# INISIALISASI GROQ CLIENT & SESSION STATE
# ==========================================
try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    api_key = os.environ.get("GROQ_API_KEY", "")

if not api_key:
    st.error("⚠️ GROQ_API_KEY belum diatur di Streamlit Secrets!")
    st.stop()

client = Groq(api_key=api_key)

if "df_payroll" not in st.session_state:
    st.session_state.df_payroll = None
if "policy_text" not in st.session_state:
    st.session_state.policy_text = "Gunakan standar peraturan ketenagakerjaan & akuntansi penggajian umum di Indonesia."
if "param_aturan" not in st.session_state:
    st.session_state.param_aturan = {
        "tarif_lembur": 25000,
        "persen_potongan_wajib": 3.0,
        "batas_gaji_maks": 50000000,
        "toleransi_selisih": 1000
    }

# ==========================================
# SIDEBAR MENU NAVIGASI SISTEM AUDIT
# ==========================================
with st.sidebar:
    st.markdown("## 🤖 PayrollAudit AI")
    st.caption(f"Auditor: **{st.session_state.username}**")
    st.divider()
    
    menu_pilihan = st.radio(
        "📌 MENU SISTEM AUDIT:",
        [
            "1. Input Data & Audit Menyeluruh",
            "2. Audit Perhitungan (Gaji, Tunjangan, Lembur & Potongan)",
            "3. Deteksi Pembayaran Tidak Sesuai & Anomali",
            "4. Pengaturan Parameter & Kebijakan Audit"
        ]
    )
    
    st.divider()
    if st.session_state.df_payroll is not None:
        st.success(f"📂 Data Aktif: {len(st.session_state.df_payroll)} baris")
    else:
        st.warning("📂 Belum ada data gaji diunggah")
        
    st.write("")
    if st.button("🚪 Logout Sistem", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# ==========================================
# HEADER BANNER UTAMA
# ==========================================
st.markdown("""
    <div class="main-banner">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <h1>🤖 PayrollAudit <span class="ai-accent">AI</span></h1>
                <p>Sistem Audit Gaji, Tunjangan, Lembur, Potongan & Deteksi Pembayaran Tidak Sesuai</p>
            </div>
            <div style="background: rgba(255,255,255,0.12); padding: 8px 16px; border-radius: 20px; font-size: 0.85rem; color: #fbbf24; font-weight: 600;">
                ● Groq Engine: Aktif
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# FUNGSI HELPER PEMBACA FILE & PARSER AMAN
# ==========================================
def extract_payroll_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)

def extract_policy_text(file):
    if file is None:
        return st.session_state.policy_text
    if file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages])
    return file.read().decode("utf-8")

def parse_hasil_audit_aman(teks):
    def ambil_bagian(tag_awal, tag_berikutnya, default_teks):
        pola = rf"\[{tag_awal}\](.*?)(?=\[{tag_berikutnya}\]|$)"
        m = re.search(pola, teks, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m and m.group(1).strip() else default_teks

    ringkasan_gaji = ambil_bagian("RINGKASAN_GAJI", "RINGKASAN_LEMBUR", "Audit komponen gaji pokok & tunjangan selesai.")
    ringkasan_lembur = ambil_bagian("RINGKASAN_LEMBUR", "RINGKASAN_POTONGAN", "Audit komponen jam & upah lembur selesai.")
    ringkasan_potongan = ambil_bagian("RINGKASAN_POTONGAN", "RINGKASAN_ANOMALI", "Audit komponen potongan & gaji bersih selesai.")
    ringkasan_anomali = ambil_bagian("RINGKASAN_ANOMALI", "DAFTAR_TEMUAN", "Pemindaian pembayaran tidak sesuai & anomali selesai.")
    blok_temuan = ambil_bagian("DAFTAR_TEMUAN", "LAPORAN_FINAL", "TIDAK_ADA")
    laporan_final = ambil_bagian("LAPORAN_FINAL", "SELESAI", "Proses audit selesai dilaksanakan.")

    daftar_temuan = []
    if "TIDAK_ADA" not in blok_temuan.upper():
        for baris in blok_temuan.splitlines():
            baris = baris.strip().lstrip("-*• ")
            if "|" in baris:
                bagian = [b.strip() for b in baris.split("|")]
                if len(bagian) >= 4:
                    daftar_temuan.append({
                        "karyawan_atau_id": bagian[0],
                        "kategori_kesalahan": bagian[1],
                        "detail_temuan": bagian[2],
                        "rekomendasi": bagian[3]
                    })
                elif len(bagian) >= 2:
                    daftar_temuan.append({
                        "karyawan_atau_id": bagian[0],
                        "kategori_kesalahan": "Temuan Audit",
                        "detail_temuan": " - ".join(bagian[1:]),
                        "rekomendasi": "Lakukan verifikasi dan penyesuaian pada sistem payroll."
                    })

    return {
        "ringkasan_gaji_tunjangan": ringkasan_gaji,
        "ringkasan_lembur": ringkasan_lembur,
        "ringkasan_potongan": ringkasan_potongan,
        "ringkasan_pembayaran_tidak_sesuai": ringkasan_anomali,
        "terdapat_temuan": len(daftar_temuan) > 0,
        "daftar_temuan": daftar_temuan,
        "laporan_audit_final": laporan_final
    }

def jalankan_audit_ai(fokus_audit):
    df = st.session_state.df_payroll
    payroll_csv_str = df.to_csv(index=False)
    param = st.session_state.param_aturan
    
    aturan_tambahan = f"""
    PARAMETER & STANDAR AUDIT PERUSAHAAN YANG BERLAKU:
    - Tarif Lembur Standar per Jam: Rp {param['tarif_lembur']:,}
    - Persentase Potongan Wajib (BPJS/PPh/Iuran): {param['persen_potongan_wajib']}% dari Gaji Pokok
    - Batas Wajar Gaji Maksimal per Karyawan: Rp {param['batas_gaji_maks']:,}
    - Toleransi Selisih Pembulatan Perhitungan: Rp {param['toleransi_selisih']:,}
    - Kebijakan / Dokumen Pendukung: {st.session_state.policy_text}
    """

    system_prompt = f"""
    Anda adalah PayrollAudit AI, auditor internal ahli forensik penggajian.
    FOKUS AUDIT SAAT INI: {fokus_audit}
    
    Periksa SETIAP BARIS data karyawan secara teliti terhadap:
    1. Gaji Pokok & Tunjangan (kewajaran tunjangan & penjumlahan bruto).
    2. Lembur (jam lembur x tarif lembur dibandingkan upah lembur dibayar, serta batas jam lembur).
    3. Potongan (potongan wajib %, potongan absensi, dan perhitungan Total Gaji Bersih Dibayar).
    4. Pembayaran Tidak Sesuai (duplikasi baris/NIK/rekening, karyawan non-aktif/resign/cuti luar tanggungan yang tetap dibayar, atau gaji melebihi batas wajar).

    Tulis hasil audit Anda PERSIS mengikuti struktur tag berikut (jangan gunakan JSON):

    [RINGKASAN_GAJI]
    Tulis ringkasan hasil pemeriksaan gaji pokok dan tunjangan di sini.

    [RINGKASAN_LEMBUR]
    Tulis ringkasan hasil pemeriksaan jam lembur dan upah lembur di sini.

    [RINGKASAN_POTONGAN]
    Tulis ringkasan hasil pemeriksaan potongan wajib, absensi, dan gaji bersih di sini.

    [RINGKASAN_ANOMALI]
    Tulis ringkasan hasil deteksi duplikasi rekening/NIK, status non-aktif, dan kewajaran gaji di sini.

    [DAFTAR_TEMUAN]
    Tulis setiap temuan kesalahan dalam 1 baris dengan format pemisah tanda garis tegak (|):
    NIK - Nama Karyawan | Kategori Kesalahan | Penjelasan detail angka seharusnya vs dibayarkan beserta selisihnya | Rekomendasi perbaikan
    (Jika tidak ada kesalahan sama sekali, tulis: TIDAK_ADA)

    [LAPORAN_FINAL]
    Tulis kesimpulan menyeluruh laporan audit final di sini.
    """

    user_prompt = f"{aturan_tambahan}\n\nDATA PAYROLL KARYAWAN:\n{payroll_csv_str}"

    daftar_model = [
        "llama-3.1-8b-instant",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "qwen/qwen3-32b",
        "openai/gpt-oss-120b"
    ]
    
    try:
        model_tersedia = [m.id for m in client.models.list().data]
        kandidat = [m for m in daftar_model if m in model_tersedia]
        if not kandidat and model_tersedia:
            kandidat = [m for m in model_tersedia if "whisper" not in m and "guard" not in m and "tts" not in m]
    except Exception:
        kandidat = daftar_model

    hasil_parsed = None
    error_terakhir = None
    for nama_model in kandidat:
        try:
            response = client.chat.completions.create(
                model=nama_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4096
            )
            konten = response.choices[0].message.content
            hasil_parsed = parse_hasil_audit_aman(konten)
            break
        except Exception as err:
            error_terakhir = err
            continue

    if hasil_parsed is None:
        raise Exception(f"Semua model gagal dipanggil. Detail: {error_terakhir}")

    return hasil_parsed

def tampilkan_hasil_audit(hasil, judul_laporan):
    st.divider()
    st.markdown("### ⚙️ Hasil Proses Analisis Audit AI")
    
    ringkasan_gaji = hasil.get("ringkasan_gaji_tunjangan", "")
    ringkasan_lembur = hasil.get("ringkasan_lembur", "")
    ringkasan_potongan = hasil.get("ringkasan_potongan", "")
    ringkasan_anomali = hasil.get("ringkasan_pembayaran_tidak_sesuai", "")
    daftar_temuan = hasil.get("daftar_temuan", [])
    laporan_final = hasil.get("laporan_audit_final", "")

    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**💰 Audit Gaji Pokok & Tunjangan:**\n\n{ringkasan_gaji}")
        st.info(f"**✂️ Audit Potongan & Gaji Bersih:**\n\n{ringkasan_potongan}")
    with c2:
        st.info(f"**⏱️ Audit Perhitungan Lembur:**\n\n{ringkasan_lembur}")
        st.info(f"**🚨 Deteksi Pembayaran Tidak Sesuai:**\n\n{ringkasan_anomali}")

    st.divider()
    st.markdown("### 📋 Keputusan Audit & Laporan Final")

    if len(daftar_temuan) > 0:
        st.warning(f"⚠️ **Status Percabangan: TERDAPAT TEMUAN ({len(daftar_temuan)} Temuan Terdeteksi)**")
        st.subheader("📌 Rincian Temuan Kesalahan & Rekomendasi")
        for idx, item in enumerate(daftar_temuan, 1):
            st.markdown(f"""
                <div class="card-box" style="border-left: 5px solid #ef4444;">
                    <span style="background:#fee2e2; color:#b91c1c; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:700;">
                        {item['kategori_kesalahan']}
                    </span>
                    <h4 style="margin:8px 0 6px 0; color:#102a43;">Temuan #{idx} — {item['karyawan_atau_id']}</h4>
                    <p style="margin-bottom:6px;"><b>Detail Kesalahan / Selisih:</b> {item['detail_temuan']}</p>
                    <p style="margin-bottom:0; color:#047857;"><b>Rekomendasi Perbaikan:</b> {item['rekomendasi']}</p>
                </div>
            """, unsafe_allow_html=True)

        st.subheader("📄 Laporan Audit Final (Disertai Rekomendasi)")
        st.error(laporan_final)
        status_teks = f"TERDAPAT {len(daftar_temuan)} TEMUAN KESALAHAN / PEMBAYARAN TIDAK SESUAI"
    else:
        st.success("✅ **Status Percabangan: DATA DINYATAKAN SESUAI (Tidak Ada Masalah)**")
        st.subheader("📄 Laporan Audit Final (Status: Aman)")
        st.success(laporan_final)
        status_teks =
