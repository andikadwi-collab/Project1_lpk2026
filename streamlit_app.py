import streamlit as st

# 1. Pustaka untuk visualisasi molekul 3D (Definisikan fallback agar tidak crash)
try:
    from stmol import showmol
    import py3Dmol
    HAS_MOL_LIBS = True
except ImportError:
    HAS_MOL_LIBS = False

st.set_page_config(page_title="ChemoVerse - Aplikasi Kimia Organik", layout="wide")

# ==========================================
# FUNGSI GLOBAL (Didefinisikan di paling atas agar bisa diakses di mana saja)
# ==========================================
def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()

def render_3d_mol(smiles_or_name):
    if not HAS_MOL_LIBS:
        st.warning("⚠️ Visualisasi 3D tidak tersedia. Pastikan `stmol` dan `py3Dmol` sudah terinstal di requirements.txt")
        return
        
    try:
        # Simulasi pencarian CID berdasarkan nama populer untuk kebutuhan Molymod 3D
        query_mapping = {
            'etanol': 'cid:702',
            'ethanol': 'cid:702',
            'alkohol': 'cid:702',
            'benzena': 'cid:241',
            'benzene': 'cid:241',
            'asam asetat': 'cid:176',
            'aseton': 'cid:180',
            'propanon': 'cid:180'
        }
        
        target = query_mapping.get(smiles_or_name.lower(), 'cid:241') # Default ke benzena jika tidak terdaftar
        
        xyzview = py3Dmol.view(query=target, width=400, height=400)
        xyzview.setStyle({'stick': {}, 'sphere': {'radius': 0.3}})
        xyzview.setBackgroundColor('#f0f2f6')
        xyzview.zoomTo()
        showmol(xyzview, height=400, width=800)
    except Exception as e:
        st.error(f"Gagal memuat struktur 3D: {str(e)}")

# Inisialisasi Session State
if 'page' not in st.session_state:
    st.session_state.page = 'cover'
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'score' not in st.session_state:
    st.session_state.score = 0

# Tampilkan error di bagian atas jika pustaka belum terinstal di cloud
if not HAS_MOL_LIBS:
    st.error("🚨 Pustaka pendukung mendesak belum terinstal! Jalankan: pip install stmol py3Dmol")

# ==========================================
# 1. HALAMAN UTAMA / COVER DEPAN
# ==========================================
if st.session_state.page == 'cover':
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>PROJEK APLIKASI KIMIA ORGANIK</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #7ED321;'>Visualisator Molekul 3D & Sistem Prediksi Reaksi</h3>", unsafe_allow_html=True)
    st.write("---")
    
    st.subheader("👥 Anggota Kelompok:")
    col1, col2 = st.columns(2)
    with col1:
        st.info("1. **ANDIKA DWI PRASHOJO**")
        st.info("2. **JAWAHER SABRINA A**")
        st.info("3. **NAELY LUTHFIYAH ARIF**")
    with col2:
        st.info("4. **SALWA AZKA SABANA**")
        st.info("5. **ALEX KUSUMAH**")
        
    st.write("---")
    st.markdown("<h4 style='text-align: center;'>Pilih Menu Aplikasi:</h4>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔬 Tata Penamaan & Reaksi Senyawa", use_container_width=True, type="primary"):
            go_to('tatanama')
    with c2:
        if st.button("📝 Latihan Soal Tebak Struktur", use_container_width=True):
            go_to('latihan')

# ==========================================
# 2. HALAMAN TATA PENAMAAN & REAKSI
# ==========================================
elif st.session_state.page == 'tatanama':
    if st.button("⬅️ Kembali ke Cover"): 
        go_to('cover')
    
    st.title("🧪 Tata Penamaan Senyawa Organik")
    st.write("Mendukung Hidrokarbon, Alkohol, Fenol, Eter, Asam Karboksilat & Derivat, Amina, Benzena, Lemak/Minyak, Aldehid, Keton, dan Protein.")

    nama_senyawa = st.text_input("Masukkan nama IUPAC atau Trivial (Contoh: Etanol, Benzena, Asam Asetat):", "Etanol")
    
    if st.button("Mulai Proses", type="primary"):
        st.subheader(f"Hasil Analisis: {nama_senyawa}")
        
        col_img, col_info = st.columns([2, 1])
        
        with col_img:
            st.markdown("**Struktur 3D (Model Molymod Interaktif):**")
            render_3d_mol(nama_senyawa)
            
        with col_info:
            st.markdown("**Informasi Senyawa:**")
            nama_clean = nama_senyawa.lower().strip()
            if nama_clean in ['etanol', 'ethanol', 'alkohol']:
                st.write("- **Berat Molekul:** 46.07 g/mol")
                st.write("- **Titik Didih:** 78.37 °C")
                st.write("- **Sifat Bahan:** Cairan mudah terbakar, volatil, polar.")
                st.write("- **Reaktivitas:** Dapat dioksidasi menjadi etanal/asam asetat, bereaksi dengan logam natrium.")
            elif nama_clean in ['benzena', 'benzene']:
                st.write("- **Berat Molekul:** 78.11 g/mol")
                st.write("- **Titik Didih:** 80.1 °C")
                st.write("- **Sifat Bahan:** Cairan aromatik, non-polar, karsinogenik.")
                st.write("- **Reaktivitas:** Substitusi Elektrofilik (Nitrasi, Sulfonasi).")
            else:
                st.write("- **Berat Molekul:** Data tidak tersedia otomatis (Mockup)")
                st.write("- **Sifat Bahan:** Perlu analisis laboratorium lebih lanjut.")

        st.write("---")
        st.subheader("🔄 Reaksi Kimia (Opsional)")
        senyawa_reaktan = st.text_input("Masukkan senyawa reaktan lain (Contoh: HCl, NaOH, O2, K2Cr2O7):", "")
        
        if senyawa_reaktan:
            if st.button("Reaksikan!"):
                st.markdown("### 📜 Hasil Reaksi Kimia")
                if nama_senyawa.lower() in ['etanol', 'ethanol'] and senyawa_reaktan.lower() in ['k2cr2o7', 'o2', 'oksidator']:
                    st.success("**Jenis Reaksi:** Oksidasi Parsial / Penuh")
                    st.write("**Penjelasan:** Alkohol primer dioksidasi oleh oksidator menghasilkan Aldehid (Etanal) lalu berlanjut menjadi Asam Karboksilat (Asam Asetat).")
                    st.write("**Nama Produk Baru:** Asam Asetat (Asam Etanoat)")
                    
                    c_res1, c_res2 = st.columns(2)
                    with c_res1:
                        st.markdown("**Struktur 3D Produk Baru:**")
                        render_3d_mol("Asam Asetat")
                    with c_res2:
                        st.markdown("**Sifat Produk Baru:**")
                        st.write("- **Berat Molekul:** 60.05 g/mol")
                        st.write("- **Titik Didih:** 118 °C")
                else:
                    st.success("**Jenis Reaksi:** Substitusi / Adisi / Eliminasi Umum")
                    st.write(f"**Penjelasan:** Reaksi teoretis terjadi antara gugus fungsi utama {nama_senyawa} dengan reaktan {senyawa_reaktan}.")

# ==========================================
# 3. HALAMAN LATIHAN SOAL
# ==========================================
elif st.session_state.page == 'latihan':
    if st.button("⬅️ Kembali ke Cover"): 
        go_to('cover')
    
    st.title("📝 Latihan Soal Kimia Organik")
    st.write("Tebak nama IUPAC/Trivial dari struktur rantai berikut (Gunakan Bahasa Indonesia).")

    bank_soal = [
        {"struktur": "CH3 - CH2 - OH", "jawaban": ["etanol", "etil alkohol"], "pembahasan": "Struktur memiliki 2 atom karbon dengan gugus fungsi -OH (alkohol), sehingga namanya adalah etanol."},
        {"struktur": "CH3 - COO - CH3", "jawaban": ["metil etanoat", "metil asetat"], "pembahasan": "Merupakan senyawa ester (alkil alkanoat). Gugus alkil adalah metil dan rantai utama alkanoatnya adalah etanoat."},
        {"struktur": "CH3 - CHO", "jawaban": ["etanal", "asetaldehid"], "pembahasan": "Memiliki gugus fungsi aldehid (-CHO) dengan total 2 atom C, dinamakan etanal."},
        {"struktur": "CH3 - CO - CH3", "jawaban": ["propanon", "aseton"], "pembahasan": "Senyawa keton dengan 3 atom C. Nama IUPAC-nya propanon dan trivialnya aseton."},
        {"struktur": "CH3 - COOH", "jawaban": ["asam etanoat", "asam asetat", "asam cuka"], "pembahasan": "Gugus -COOH menunjukkan asam karboksilat dengan 2 atom C."}
    ]
    
    for i in range(5, 25):
        bank_soal.append({
            "struktur": f"CH3 - (CH2){i-3} - COOH" if i%2==0 else f"CH3 - (CH2){i-4} - OH",
            "jawaban": [f"asam alkanoat {i}", "alkanol"],
            "pembahasan": f"Pembahasan otomatis untuk latihan soal struktur senyawa organik ke-{i+1}."
        })

    current = st.session_state.current_question
    
    st.info(f"**Soal No. {current + 1} / Total**")
    st.markdown(f"**Identifikasi Rumus Struktur Berikut:**")
    st.code(bank_soal[current]["struktur"], language="text")
    
    user_ans = st.text_input("Jawaban Anda (IUPAC / Trivial):", key=f"input_{current}")
    
    if st.button("Kirim Jawaban"):
        correct_answers = bank_soal[current]["jawaban"]
        if user_ans.strip().lower() in [ans.lower() for ans in correct_answers]:
            st.success("🎯 Benar!")
            st.session_state.score += 1
        else:
            st.error(f"❌ Salah! Jawaban yang benar bisa berupa: {', '.join(correct_answers)}")
            
        st.markdown(f"**💡 Pembahasan:** {bank_soal[current]['pembahasan']}")
        
    if st.button("Soal Selanjutnya ➡️"):
        st.session_state.current_question += 1
        if st.session_state.current_question == 10:
            st.warning("🎉 Anda telah menyelesaikan 10 Soal Pertama! Memuat 10 soal berikutnya...")
        st.rerun()
