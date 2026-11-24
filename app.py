import streamlit as st
import pandas as pd
import PyPDF2
import json
import os
from groq import Groq

# Konfigurasi Halaman
st.set_page_config(page_title="PayrollAudit AI", page_icon="🤖", layout="wide")

# ==========================================
# CUSTOM CSS UNTUK TAMPILAN MODERN & ELEGAN
# ==========================================
def apply_custom_style():
    st.markdown("""
        <style>
        /* Latar belakang utama dengan gradasi biru-abu lembut */
        .stApp {
            background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
            color: #102a43;
        }

        /* Menyembunyikan header default Streamlit yang kosong agar lebih bersih */
        header[data-testid="stHeader"] {
            background-color: rgba(240, 244, 248, 0.8);
            backdrop-filter: blur(8px);
        }

        /* Banner Header Utama (Selaras dengan bagan alur Navy Blue & Emas) */
        .main-banner {
            background: linear-gradient(90deg, #0a2540 0%, #103c68 100%);
            padding: 2rem 2.5rem;
            border-radius: 16px;
            color: white;
            box-shadow: 0 10px 25px rgba(10, 37, 64, 0.15);
            margin-bottom: 1.5rem;
            border-left: 6px solid #f59e0b;
        }
        .main-banner h1 {
            margin: 0;
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: #ffffff;
        }
        .main-banner span.ai-accent {
            color: #fbbf24;
        }
        .main-banner p {
            margin: 0.4rem 0 0 0;
            font-size: 1rem;
            color: #cbd5e1;
        }

        /* Kartu Kontainer Putih Bersih */
        .card-box {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 14px;
            box-shadow: 0 4px 15px rgba(16, 42, 67, 0.06);
            border: 1px solid #e2e8f0;
            margin-bottom: 1rem;
        }

        /* Styling Area File Uploader */
        [data-testid="stFileUploader"] {
            background-color: #ffffff;
            padding: 1.2rem;
            border-radius: 12px;
            border: 1.5px dashed #3b82f6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
            transition: all 0.3s ease;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: #1d4ed8;
            box-shadow: 0 6px 16px rgba(59, 130, 246, 0.15);
        }

        /* Styling Tombol Utama */
        .stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #0284c7 0%, #1d4ed8 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.6rem 1.8rem;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(29, 78, 216, 0.25);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(29, 78, 216, 0.35);
        }

        /* Styling Kotak Form Login */
        [data-testid="stForm"] {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(10, 37, 64, 0.1);
            border: 1px solid #e2e8f0;
        }

        /* Styling Kotak Alert / Info */
        [data-testid="stAlert"] {
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
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
                <p>Sistem Audit Gaji dan Tunjangan Karyawan</p>
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
# INISIALISASI GROQ CLIENT
# ==========================================
try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    api_key = os.environ.get("GROQ_API_KEY", "")

if not api_key:
    st.error("⚠️ GROQ_API_KEY belum diatur di Streamlit Secrets!")
    st.stop()

client = Groq(api_key=api_key)

# ==========================================
# HEADER DASHBOARD SETELAH LOGIN
# ==========================================
st.markdown(f"""
    <div class="main-banner">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <h1>🤖 PayrollAudit <span class="ai-accent">AI</span></h1>
                <p>Sistem Audit Gaji dan Tunjangan Karyawan • Auditor Aktif: <b>{st.session_state.username}</b></p>
            </div>
            <div style="background: rgba(255,255,255,0.12); padding: 8px 16px; border-radius: 20px; font-size: 0.85rem; color: #fbbf24; font-weight: 600;">
                ● Status Engine: Groq AI Aktif
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

col_space, col_logout = st.columns([9, 1])
with col_logout:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# ==========================================
# TAHAP 2: INPUT DATA (GAJI, TUNJANGAN & DOKUMEN PENDUKUNG)
# ==========================================
st.markdown("### 📂 1. Input Data Audit")
col1, col2 = st.columns(2)

with col1:
    payroll_file = st.file_uploader(
        "📊 Unggah Data Gaji & Tunjangan (Excel / CSV)", 
        type=["xlsx", "xls", "csv"]
    )

with col2:
    policy_file = st.file_uploader(
        "📑 Unggah Dokumen Pendukung / Kebijakan HR (PDF / TXT - Opsional)", 
        type=["pdf", "txt"]
    )

def extract_payroll_data(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    return df

def extract_policy_text(file):
    if file is None:
        return "Gunakan standar peraturan ketenagakerjaan & akuntansi penggajian umum yang berlaku di Indonesia."
    if file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    else:
        return file.read().decode("utf-8")

if payroll_file is not None:
    df_payroll = extract_payroll_data(payroll_file)
    with st.expander("👁️ Preview Data Gaji & Tunjangan yang Diunggah", expanded=True):
        st.dataframe(df_payroll, use_container_width=True)

    st.write("")
    # ==========================================
    # TAHAP 3: PAYROLLAUDIT AI (PROSES AUDIT OLEH AI)
    # ==========================================
    if st.button("🚀 Mulai Proses Audit AI", type="primary"):
        with st.spinner("PayrollAudit AI sedang menjalankan 4 tahapan analisis audit..."):
            policy_text = extract_policy_text(policy_file)
            payroll_csv_str = df_payroll.to_csv(index=False)

            system_prompt = """
            Anda adalah PayrollAudit AI, auditor internal profesional khusus penggajian dan tunjangan karyawan.
            Tugas Anda melakukan audit menyeluruh berdasarkan 4 tahapan berikut:
            1. Validasi Data (keakuratan & kelengkapan kolom/data karyawan).
            2. Analisis Perhitungan (cek penjumlahan gaji pokok, tunjangan, lembur, potongan, dan total gaji bersih).
            3. Deteksi Anomali (cek duplikasi nama/ID, gaji tidak wajar, salah hitung, atau ketidaksesuaian).
            4. Evaluasi Kepatuhan (kesesuaian terhadap dokumen pendukung/kebijakan yang diberikan).

            WAJIB merespons HANYA dalam format JSON murni dengan struktur persis seperti ini:
            {
                "validasi_data": "Ringkasan hasil validasi kelengkapan data",
                "analisis_perhitungan": "Ringkasan hasil pengecekan rumus & angka",
                "deteksi_anomali": "Ringkasan anomali atau kejanggalan yang ditemukan",
                "evaluasi_kepatuhan": "Ringkasan kepatuhan terhadap kebijakan",
                "terdapat_temuan": true atau false,
                "daftar_temuan_rekomendasi": [
                    {
                        "karyawan_atau_item": "Nama/ID Karyawan atau Komponen",
                        "jenis_kesalahan_risiko": "Deskripsi kesalahan/risiko",
                        "rekomendasi": "Langkah perbaikan yang disarankan"
                    }
                ],
                "kesimpulan_laporan_final": "Narasi lengkap Laporan Audit Final"
            }
            Catatan: Jika tidak ada kesalahan sama sekali, set "terdapat_temuan": false dan kosongkan array "daftar_temuan_rekomendasi": [].
            """

            user_prompt = f"""
            DATA GAJI DAN TUNJANGAN:
            {payroll_csv_str}

            DOKUMEN PENDUKUNG / KEBIJAKAN PERUSAHAAN:
            {policy_text}
            """

            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )

                hasil_audit = json.loads(response.choices[0].message.content)
                st.session_state.hasil_audit = hasil_audit

            except Exception as e:
                st.error(f"Terjadi kesalahan saat memproses dengan Groq AI: {e}")

# ==========================================
# TAHAP 4 & 5: HASIL PROSES AUDIT, PERCABANGAN TEMUAN & LAPORAN FINAL
# ==========================================
if "hasil_audit" in st.session_state:
    hasil = st.session_state.hasil_audit
    st.divider()
    st.markdown("### ⚙️ 2. Hasil Proses Audit oleh AI")

    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**✔️ Validasi Data (Keakuratan & Kelengkapan):**\n\n{hasil['validasi_data']}")
        st.info(f"**🔍 Deteksi Anomali (Kesalahan / Ketidaksesuaian):**\n\n{hasil['deteksi_anomali']}")
    with c2:
        st.info(f"**🧮 Analisis Perhitungan (Gaji & Tunjangan):**\n\n{hasil['analisis_perhitungan']}")
        st.info(f"**📊 Evaluasi Kepatuhan (Regulasi & Kebijakan):**\n\n{hasil['evaluasi_kepatuhan']}")

    st.divider()
    st.markdown("### 📋 3. Keputusan Audit & Laporan Final")

    if hasil["terdapat_temuan"]:
        st.warning("⚠️ **Status Percabangan: TERDAPAT TEMUAN (Ya)**")
        
        st.subheader("📌 Temuan & Rekomendasi (Kesalahan / Risiko)")
        for idx, item in enumerate(hasil["daftar_temuan_rekomendasi"], 1):
            st.markdown(f"""
                <div class="card-box" style="border-left: 5px solid #f59e0b;">
                    <h4 style="margin-top:0; color:#b45309;">Temuan #{idx} — {item['karyawan_atau_item']}</h4>
                    <p style="margin-bottom:6px;"><b>Kesalahan / Risiko:</b> {item['jenis_kesalahan_risiko']}</p>
                    <p style="margin-bottom:0;"><b>Rekomendasi Perbaikan:</b> {item['rekomendasi']}</p>
                </div>
            """, unsafe_allow_html=True)

        st.subheader("📄 Laporan Audit Final (Disertai Rekomendasi)")
        st.error(hasil["kesimpulan_laporan_final"])
        status_teks = "DITEMUKAN TEMUAN / RISIKO (DISERTAI REKOMENDASI)"

    else:
        st.success("✅ **Status Percabangan: DATA DINYATAKAN SESUAI (Tidak Ada Masalah)**")
        
        st.subheader("📄 Laporan Audit Final (Status: Aman)")
        st.success(hasil["kesimpulan_laporan_final"])
        status_teks = "AMAN / DATA DINYATAKAN SESUAI"

    # ==========================================
    # TAHAP AKHIR: SELESAI (UNDUH LAPORAN)
    # ==========================================
    laporan_txt = f"""====================================================
LAPORAN AUDIT FINAL - PAYROLLAUDIT AI
====================================================
Auditor       : {st.session_state.username}
Status Akhir  : {status_teks}

1. VALIDASI DATA
{hasil['validasi_data']}

2. ANALISIS PERHITUNGAN
{hasil['analisis_perhitungan']}

3. DETEKSI ANOMALI
{hasil['deteksi_anomali']}

4. EVALUASI KEPATUHAN
{hasil['evaluasi_kepatuhan']}

5. KESIMPULAN LAPORAN AUDIT FINAL
{hasil['kesimpulan_laporan_final']}
====================================================
"""
    st.download_button(
        label="📥 Unduh Laporan Audit Final (.txt)",
        data=laporan_txt,
        file_name="Laporan_Audit_Payroll_Final.txt",
        mime="text/plain"
    )
