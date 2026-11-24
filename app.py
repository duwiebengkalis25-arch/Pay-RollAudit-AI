import streamlit as st
import pandas as pd
import PyPDF2
import json
import os
from groq import Groq

# Konfigurasi Halaman
st.set_page_config(page_title="PayrollAudit AI", page_icon="🤖", layout="wide")

# ==========================================
# TAHAP 1: MULAI & LOGIN PENGGUNA
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    st.title("🤖 PayrollAudit AI")
    st.subheader("Sistem Audit Gaji dan Tunjangan Karyawan")
    st.info("Silakan login untuk mengakses sistem audit.")
    
    with st.form("login_form"):
        username = st.text_input("Username Auditor", placeholder="contoh: auditor_hr")
        password = st.text_input("Password", type="password", placeholder="contoh: admin123")
        submit = st.form_submit_button("Masuk ke Sistem")
        
        if submit:
            # Simulasi kredensial login (bisa disesuaikan)
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

# Header Dashboard setelah Login
col_header, col_logout = st.columns([8, 1])
with col_header:
    st.title("🤖 PayrollAudit AI")
    st.caption(f"Sistem Audit Gaji dan Tunjangan Karyawan | Auditor aktif: **{st.session_state.username}**")
with col_logout:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

st.divider()

# ==========================================
# TAHAP 2: INPUT DATA (GAJI, TUNJANGAN & DOKUMEN PENDUKUNG)
# ==========================================
st.header("1. Input Data Audit")
col1, col2 = st.columns(2)

with col1:
    payroll_file = st.file_uploader(
        "Unggah Data Gaji & Tunjangan (Excel / CSV)", 
        type=["xlsx", "xls", "csv"]
    )

with col2:
    policy_file = st.file_uploader(
        "Unggah Dokumen Pendukung / Kebijakan HR (PDF / TXT - Opsional)", 
        type=["pdf", "txt"]
    )

# Fungsi helper untuk membaca isi file
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
    with st.expander("Preview Data Gaji & Tunjangan yang Diunggah"):
        st.dataframe(df_payroll, use_container_width=True)

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
                    temperature=0.1, # Rendah agar analisis audit konsisten dan akurat
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
    st.header("2. Hasil Proses Audit oleh AI")

    # Menampilkan 4 Kotak Proses Audit di sisi kanan bagan alur
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**✔️ Validasi Data (Keakuratan & Kelengkapan):**\n\n{hasil['validasi_data']}")
        st.info(f"**🔍 Deteksi Anomali (Kesalahan / Ketidaksesuaian):**\n\n{hasil['deteksi_anomali']}")
    with c2:
        st.info(f"**🧮 Analisis Perhitungan (Gaji & Tunjangan):**\n\n{hasil['analisis_perhitungan']}")
        st.info(f"**📊 Evaluasi Kepatuhan (Regulasi & Kebijakan):**\n\n{hasil['evaluasi_kepatuhan']}")

    st.divider()
    st.header("3. Keputusan Audit & Laporan Final")

    # PERCABANGAN: TERDAPAT TEMUAN? (YA / TIDAK)
    if hasil["terdapat_temuan"]:
        # JALUR "YA" (Kanan pada bagan alur)
        st.warning("⚠️ **Status Percabangan: TERDAPAT TEMUAN (Ya)**")
        
        st.subheader("📌 Temuan & Rekomendasi (Kesalahan / Risiko)")
        for idx, item in enumerate(hasil["daftar_temuan_rekomendasi"], 1):
            with st.container(border=True):
                st.markdown(f"**Temuan #{idx} — {item['karyawan_atau_item']}**")
                st.markdown(f"- **Kesalahan / Risiko:** {item['jenis_kesalahan_risiko']}")
                st.markdown(f"- **Rekomendasi Perbaikan:** {item['rekomendasi']}")

        st.subheader("📄 Laporan Audit Final (Disertai Rekomendasi)")
        st.error(hasil["kesimpulan_laporan_final"])
        status_teks = "DITEMUKAN TEMUAN / RISIKO (DISERTAI REKOMENDASI)"

    else:
        # JALUR "TIDAK" (Kiri pada bagan alur)
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
