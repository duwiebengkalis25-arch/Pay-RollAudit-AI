import streamlit as st
import pandas as pd
import PyPDF2
import json
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
        [data-testid="stSidebar"] {
            background-color: #0a2540;
            color: #ffffff;
        }
        [data-testid="stSidebar"] * {
            color: #f8fafc !important;
        }
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
# FUNGSI HELPER PEMBACA FILE & PROSES AI
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

def ekstrak_json_aman(teks_mentah):
    # Membersihkan blok markdown ```json ... ``` jika ada
    teks_bersih = re.sub(r"```json\s*|```", "", teks_mentah).strip()
    match = re.search(r"\{.*\}", teks_bersih, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return json.loads(teks_bersih)

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
    
    Tugas Anda mendeteksi secara teliti dan presisi seluruh baris data:
    1. Kesalahan perhitungan Gaji Pokok & Tunjangan (penjumlahan komponen penghasilan bruto & kewajaran tunjangan).
    2. Kesalahan perhitungan Lembur (jam lembur x tarif lembur dibandingkan dengan upah lembur dibayarkan, serta batas jam lembur).
    3. Kesalahan perhitungan Potongan (potongan wajib %, potongan absensi, dan selisih pada Total Gaji Bersih Dibayar).
    4. Kemungkinan Pembayaran Gaji yang Tidak Sesuai (duplikasi baris karyawan/NIK/nomor rekening, karyawan berstatus non-aktif/resign/cuti luar tanggungan yang tetap dibayar, atau gaji di atas batas wajar).

    PENTING: Keluarkan HANYA objek JSON valid (tanpa teks pembuka atau penutup di luar kurung kurawal) dengan format persis:
    {{
        "ringkasan_gaji_tunjangan": "Ringkasan hasil audit komponen gaji pokok & tunjangan",
        "ringkasan_lembur": "Ringkasan hasil audit perhitungan jam & upah lembur",
        "ringkasan_potongan": "Ringkasan hasil audit komponen potongan & gaji bersih",
        "ringkasan_pembayaran_tidak_sesuai": "Ringkasan hasil deteksi anomali, duplikasi, atau pembayaran tidak wajar",
        "terdapat_temuan": true,
        "daftar_temuan": [
            {{
                "karyawan_atau_id": "NIK - Nama Karyawan",
                "kategori_kesalahan": "Salah Hitung Gaji / Salah Tunjangan / Salah Lembur / Salah Potongan / Pembayaran Tidak Sesuai",
                "detail_temuan": "Penjelasan ringkas angka seharusnya vs dibayarkan beserta selisihnya",
                "rekomendasi": "Tindakan koreksi yang disarankan"
            }}
        ],
        "laporan_audit_final": "Kesimpulan menyeluruh laporan audit"
    }}
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

    hasil_json = None
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
            hasil_json = ekstrak_json_aman(konten)
            break
        except Exception as err:
            error_terakhir = err
            continue

    if hasil_json is None:
        raise Exception(f"Semua model gagal dipanggil. Detail: {error_terakhir}")

    return hasil_json

def tampilkan_hasil_audit(hasil, judul_laporan):
    st.divider()
    st.markdown("### ⚙️ Hasil Proses Analisis Audit AI")
    
    ringkasan_gaji = hasil.get("ringkasan_gaji_tunjangan", "Data gaji pokok dan tunjangan telah diperiksa.")
    ringkasan_lembur = hasil.get("ringkasan_lembur", "Perhitungan jam dan upah lembur telah diperiksa.")
    ringkasan_potongan = hasil.get("ringkasan_potongan", "Komponen potongan wajib, absensi, dan gaji bersih telah diperiksa.")
    ringkasan_anomali = hasil.get("ringkasan_pembayaran_tidak_sesuai", "Pemindaian duplikasi dan kewajaran pembayaran telah dijalankan.")
    terdapat_temuan = hasil.get("terdapat_temuan", False)
    daftar_temuan = hasil.get("daftar_temuan") or hasil.get("daftar_temuan_rekomendasi") or []
    laporan_final = (
        hasil.get("laporan_audit_final")
        or hasil.get("kesimpulan_laporan_final")
        or hasil.get("kesimpulan")
        or "Audit telah selesai dijalankan. Silakan tinjau rincian temuan di atas untuk tindakan koreksi lebih lanjut."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**💰 Audit Gaji Pokok & Tunjangan:**\n\n{ringkasan_gaji}")
        st.info(f"**✂️ Audit Potongan & Gaji Bersih:**\n\n{ringkasan_potongan}")
    with c2:
        st.info(f"**⏱️ Audit Perhitungan Lembur:**\n\n{ringkasan_lembur}")
        st.info(f"**🚨 Deteksi Pembayaran Tidak Sesuai:**\n\n{ringkasan_anomali}")

    st.divider()
    st.markdown("### 📋 Keputusan Audit & Laporan Final")

    if terdapat_temuan or len(daftar_temuan) > 0:
        st.warning(f"⚠️ **Status Percabangan: TERDAPAT TEMUAN ({len(daftar_temuan)} Temuan Terdeteksi)**")
        st.subheader("📌 Rincian Temuan Kesalahan & Rekomendasi")
        for idx, item in enumerate(daftar_temuan, 1):
            kategori = item.get("kategori_kesalahan", "Temuan Audit")
            karyawan = item.get("karyawan_atau_id") or item.get("karyawan_atau_item") or f"Item #{idx}"
            detail = item.get("detail_temuan") or item.get("jenis_kesalahan_risiko") or "-"
            rekom = item.get("rekomendasi", "Lakukan verifikasi dan penyesuaian nominal pada sistem payroll.")

            st.markdown(f"""
                <div class="card-box" style="border-left: 5px solid #ef4444;">
                    <span style="background:#fee2e2; color:#b91c1c; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:700;">
                        {kategori}
                    </span>
                    <h4 style="margin:8px 0 6px 0; color:#102a43;">Temuan #{idx} — {karyawan}</h4>
                    <p style="margin-bottom:6px;"><b>Detail Kesalahan / Selisih:</b> {detail}</p>
                    <p style="margin-bottom:0; color:#047857;"><b>Rekomendasi Perbaikan:</b> {rekom}</p>
                </div>
            """, unsafe_allow_html=True)

        st.subheader("📄 Laporan Audit Final (Disertai Rekomendasi)")
        st.error(laporan_final)
        status_teks = "TERDAPAT TEMUAN KESALAHAN / PEMBAYARAN TIDAK SESUAI"
    else:
        st.success("✅ **Status Percabangan: DATA DINYATAKAN SESUAI (Tidak Ada Masalah)**")
        st.subheader("📄 Laporan Audit Final (Status: Aman)")
        st.success(laporan_final)
        status_teks = "AMAN / DATA DINYATAKAN SESUAI"

    laporan_txt = f"""====================================================
{judul_laporan.upper()} - PAYROLLAUDIT AI
====================================================
Auditor       : {st.session_state.username}
Status Akhir  : {status_teks}

1. AUDIT GAJI POKOK & TUNJANGAN
{ringkasan_gaji}

2. AUDIT PERHITUNGAN LEMBUR
{ringkasan_lembur}

3. AUDIT POTONGAN & GAJI BERSIH
{ringkasan_potongan}

4. DETEKSI PEMBAYARAN TIDAK SESUAI
{ringkasan_anomali}

5. KESIMPULAN LAPORAN AUDIT FINAL
{laporan_final}
====================================================
"""
    st.download_button(
        label="📥 Unduh Laporan Audit Final (.txt)",
        data=laporan_txt,
        file_name="Laporan_Audit_Payroll_Final.txt",
        mime="text/plain"
    )

# ==========================================
# KONTEN HALAMAN BERDASARKAN MENU SIDEBAR
# ==========================================

if menu_pilihan == "1. Input Data & Audit Menyeluruh":
    st.markdown("### 📂 Input Data & Audit Menyeluruh (Sesuai Bagan Alur)")
    col1, col2 = st.columns(2)
    with col1:
        payroll_file = st.file_uploader("📊 Unggah Data Gaji, Tunjangan, Lembur & Potongan (Excel / CSV)", type=["xlsx", "xls", "csv"])
    with col2:
        policy_file = st.file_uploader("📑 Unggah Dokumen Kebijakan HR / Aturan Penggajian (PDF / TXT)", type=["pdf", "txt"])

    if payroll_file is not None:
        st.session_state.df_payroll = extract_payroll_data(payroll_file)
    if policy_file is not None:
        st.session_state.policy_text = extract_policy_text(policy_file)

    if st.session_state.df_payroll is not None:
        with st.expander("👁️ Preview Data Penggajian Aktif", expanded=True):
            st.dataframe(st.session_state.df_payroll, use_container_width=True)

        if st.button("🚀 Mulai Proses Audit Menyeluruh", type="primary"):
            with st.spinner("PayrollAudit AI sedang memeriksa seluruh komponen gaji, tunjangan, lembur, potongan & anomali..."):
                try:
                    hasil = jalankan_audit_ai("Audit menyeluruh seluruh komponen gaji, tunjangan, lembur, potongan, dan kepatuhan pembayaran.")
                    st.session_state.hasil_menyeluruh = hasil
                except Exception as e:
                    st.error(f"Terjadi kesalahan koneksi AI: {e}")

        if "hasil_menyeluruh" in st.session_state:
            tampilkan_hasil_audit(st.session_state.hasil_menyeluruh, "Laporan Audit Menyeluruh")

elif menu_pilihan == "2. Audit Perhitungan (Gaji, Tunjangan, Lembur & Potongan)":
    st.markdown("### 🧮 Audit Akurasi Perhitungan Gaji, Tunjangan, Lembur & Potongan")
    st.caption("Menu ini memfokuskan pemeriksaan pada rumus matematika dan selisih nominal setiap komponen penghasilan dan pengurang gaji.")
    
    if st.session_state.df_payroll is None:
        st.warning("⚠️ Silakan unggah terlebih dahulu file data gaji pada **Menu 1 (Input Data & Audit Menyeluruh)**.")
    else:
        komponen_fokus = st.multiselect(
            "Pilih komponen spesifik yang ingin diaudit secara mendalam:",
            ["Gaji Pokok", "Tunjangan (Jabatan/Makan/Transport)", "Perhitungan Jam & Upah Lembur", "Potongan (BPJS, PPh 21, Absensi, Kasbon)", "Total Gaji Bersih (Take Home Pay)"],
            default=["Gaji Pokok", "Tunjangan (Jabatan/Makan/Transport)", "Perhitungan Jam & Upah Lembur", "Potongan (BPJS, PPh 21, Absensi, Kasbon)", "Total Gaji Bersih (Take Home Pay)"]
        )
        
        if st.button("🔍 Jalankan Audit Perhitungan Komponen", type="primary"):
            with st.spinner("Mengaudit rumus perhitungan gaji, tunjangan, lembur, dan potongan..."):
                try:
                    fokus = f"Audit presisi matematis khusus pada komponen: {', '.join(komponen_fokus)}. Hitung ulang baris demi baris dan temukan selisih sekecil apa pun."
                    hasil = jalankan_audit_ai(fokus)
                    st.session_state.hasil_komponen = hasil
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

        if "hasil_komponen" in st.session_state:
            tampilkan_hasil_audit(st.session_state.hasil_komponen, "Laporan Audit Perhitungan Komponen")

elif menu_pilihan == "3. Deteksi Pembayaran Tidak Sesuai & Anomali":
    st.markdown("### 🚨 Deteksi Kemungkinan Pembayaran Gaji Tidak Sesuai & Anomali")
    st.caption("Mendeteksi duplikasi data karyawan, nomor rekening ganda, pembayaran karyawan non-aktif/resign, serta nominal di luar kewajaran jabatan.")
    
    if st.session_state.df_payroll is None:
        st.warning("⚠️ Silakan unggah terlebih dahulu file data gaji pada **Menu 1 (Input Data & Audit Menyeluruh)**.")
    else:
        cek_anomali = st.multiselect(
            "Pilih jenis indikator pembayaran tidak sesuai yang akan dipindai:",
            [
                "Duplikasi Nama / NIK / Nomor Rekening (Gaji Ganda)",
                "Pembayaran pada Karyawan Berstatus Non-Aktif / Resign / Cuti di Luar Tanggungan",
                "Lonjakan Gaji / Tunjangan Tidak Wajar (Outlier)",
                "Ketidaksesuaian Gaji dengan Golongan / Jabatan / Kehadiran"
            ],
            default=[
                "Duplikasi Nama / NIK / Nomor Rekening (Gaji Ganda)",
                "Pembayaran pada Karyawan Berstatus Non-Aktif / Resign / Cuti di Luar Tanggungan",
                "Lonjakan Gaji / Tunjangan Tidak Wajar (Outlier)",
                "Ketidaksesuaian Gaji dengan Golongan / Jabatan / Kehadiran"
            ]
        )

        if st.button("🛡️ Pindai Pembayaran Tidak Sesuai", type="primary"):
            with st.spinner("Memindai indikasi anomali, duplikasi, dan pembayaran gaji tidak sesuai..."):
                try:
                    fokus = f"Audit forensik deteksi pembayaran tidak sesuai untuk indikator: {', '.join(cek_anomali)}."
                    hasil = jalankan_audit_ai(fokus)
                    st.session_state.hasil_anomali = hasil
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

        if "hasil_anomali" in st.session_state:
            tampilkan_hasil_audit(st.session_state.hasil_anomali, "Laporan Deteksi Pembayaran Tidak Sesuai")

elif menu_pilihan == "4. Pengaturan Parameter & Kebijakan Audit":
    st.markdown("### ⚙️ Pengaturan Parameter & Standar Aturan Audit")
    st.caption("Tentukan acuan tarif lembur, persentase potongan, dan batas kewajaran gaji yang akan digunakan AI sebagai dasar pemeriksaan.")
    
    with st.form("form_parameter"):
        c1, c2 = st.columns(2)
        with c1:
            tarif_lembur = st.number_input("Tarif Lembur Standar per Jam (Rp)", min_value=0, value=st.session_state.param_aturan["tarif_lembur"], step=5000)
            batas_gaji = st.number_input("Batas Kewajaran Gaji Maksimal per Bulan (Rp)", min_value=0, value=st.session_state.param_aturan["batas_gaji_maks"], step=1000000)
        with c2:
            persen_potongan = st.number_input("Standar Persentase Potongan Wajib (%)", min_value=0.0, max_value=100.0, value=st.session_state.param_aturan["persen_potongan_wajib"], step=0.5)
            toleransi = st.number_input("Batas Toleransi Selisih Pembulatan (Rp)", min_value=0, value=st.session_state.param_aturan["toleransi_selisih"], step=500)
            
        catatan_kebijakan = st.text_area(
            "Aturan / Kebijakan Khusus Perusahaan (Opsional)", 
            value=st.session_state.policy_text,
            height=120
        )
        
        if st.form_submit_button("💾 Simpan Parameter Audit", type="primary"):
            st.session_state.param_aturan = {
                "tarif_lembur": tarif_lembur,
                "persen_potongan_wajib": persen_potongan,
                "batas_gaji_maks": batas_gaji,
                "toleransi_selisih": toleransi
            }
            st.session_state.policy_text = catatan_kebijakan
            st.success("✅ Parameter dan aturan audit berhasil diperbarui! Silakan jalankan proses audit di menu 1, 2, atau 3.")
