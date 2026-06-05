import streamlit as st

# 1. Pustaka untuk visualisasi molekul 3D
try:
    from stmol import showmol
    import py3Dmol
    HAS_MOL_LIBS = True
except ImportError:
    HAS_MOL_LIBS = False

st.set_page_config(page_title="ChemoVerse - Aplikasi Kimia Organik", layout="wide")

# ==========================================
# DATABASE MAPPING (IUPAC, TRIVIAL, INDO, ENG)
# ==========================================
# Kamus untuk menyatukan berbagai variasi nama ke satu ID standard (SMILES / CID)
DATABASE_SENYAWA = {
    # 1. Alkohol / Alkanol
    "etanol": "ethanol", "ethanol": "ethanol", "etil alkohol": "ethanol", "ethyl alcohol": "ethanol",
    "metanol": "methanol", "methanol": "methanol", "metil alkohol": "methanol", "methyl alcohol": "methanol",
    
    # 2. Hidrokarbon (Alkana, Alkena, Alkuna)
    "metana": "methane", "methane": "methane",
    "etana": "ethane", "ethane": "ethane",
    "etena": "ethene", "ethene": "ethene", "etilena": "ethene", "ethylene": "ethene",
    "etuna": "ethyne", "ethyne": "ethyne", "asetilena": "ethyne", "acetylene": "ethyne",
    
    # 3. Asam Karboksilat
    "asam etanoat": "acetic_acid", "ethanoic acid": "acetic_acid", "asam asetat": "acetic_acid", "acetic acid": "acetic_acid", "asam cuka": "acetic_acid",
    
    # 4. Aldehid & Keton
    "metanal": "formaldehyde", "methanal": "formaldehyde", "formaldehida": "formaldehyde", "formalin": "formaldehyde",
    "etanal": "acetaldehyde", "ethanal": "acetaldehyde", "asetaldehid": "acetaldehyde", "acetaldehyde": "acetaldehyde",
    "propanon": "acetone", "propanone": "acetone", "aseton": "acetone", "acetone": "acetone",
    
    # 5. Benzena & Derivat
    "benzena": "benzene", "benzene": "benzene",
    "fenol": "phenol", "phenol": "phenol", "hidroksibenzena": "phenol",
    
    # 6. Eter & Ester
    "metoksi metana": "dimethyl_ether", "methoxy methane": "dimethyl_ether", "dimetil eter": "dimethyl_ether", "dimethyl ether": "dimethyl_ether",
    "metil etanoat": "methyl_acetate", "methyl ethanoate": "methyl_acetate", "metil asetat": "methyl_acetate", "methyl acetate": "methyl_acetate",
    
    # 7. Amina & Protein / Asam Amino
    "metanamina": "methylamine", "methanamine": "methylamine", "metilamina": "methylamine", "methylamine": "methylamine",
    "glisin": "glycine", "glycine": "glycine", "asam aminoetanoat": "glycine"
}

# Data Spesifikasi Detail Kimia berdasarkan ID Standard
DATA_KIMIA = {
    "ethanol": {
        "cid": "cid:702", "nama_resmi": "Etanol / Ethyl Alcohol",
        "bm": "46.07 g/mol", "td": "78.37 °C",
        "sifat": "Cairan bening, mudah terbakar, volatil, memiliki gugus fungsi polar (-OH).",
        "reaktivitas": "Dapat dioksidasi menjadi etanal/asam asetat, bereaksi dengan logam natrium membentuk gas H2."
    },
    "benzene": {
        "cid": "cid:241", "nama_resmi": "Benzena / Benzene",
        "bm": "78.11 g/mol", "td": "80.1 °C",
        "sifat": "Cairan aromatik khas, non-polar, karsinogenik, sangat stabil karena resonansi cincin.",
        "reaktivitas": "Sukar melakukan reaksi adisi, cenderung melakukan Substitusi Elektrofilik (Nitrasi, Sulfonasi)."
    },
    "acetic_acid": {
        "cid": "cid:176", "nama_resmi": "Asam Asetat / Ethanoic Acid",
        "bm": "60.05 g/mol", "td": "118 °C",
        "sifat": "Cairan korosif berbau menyengat, asam lemah, larut sempurna dalam air (polar).",
        "reaktivitas": "Bereaksi dengan alkohol membentuk ester (Esterifikasi), bereaksi dengan basa membentuk garam."
    },
    "acetone": {
        "cid": "cid:180", "nama_resmi": "Propanon / Acetone",
        "bm": "58.08 g/mol", "td": "56.05 °C",
        "sifat": "Cairan volatil mudah terbakar, pelarut organik universal yang sangat baik.",
        "reaktivitas": "Dapat diadisi oleh nukleofil, tidak dapat dioksidasi oleh oksidator lemah (Tollens/Fehling)."
    }
}

# ==========================================
# FUNGSI GLOBAL
# ==========================================
def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()

def render_3d_mol(target_cid):
    if not HAS_MOL_LIBS:
        st.warning("⚠️ Visualisasi 3D tidak tersedia secara interaktif.")
        return
    try:
        xyzview = py3Dmol.view(query=target_cid, width=400, height=400)
        xyzview.setStyle({'stick': {}, 'sphere': {'radius': 0.3}})
        xyzview.setBackgroundColor('#f0f2f6')
        xyzview.zoomTo()
        showmol(xyzview, height=400, width=800)
    except Exception as e:
        st.error(f"Gagal merender model 3D: {str(e)}")

# Inisialisasi State
if 'page' not in st.session_state: st.session_state.page = 'cover'
if 'current_question' not in st.session_state: st.session_state.current_question = 0

# ==========================================
# 1. HALAMAN UTAMA / COVER DEPAN
# ==========================================
if st.session_state.page == 'cover':
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>PROJEK APLIKASI KIMIA ORGANIK</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #7ED321;'>Sistem Identifikasi Multi-Bahasa & Visualisasi Molymod 3D</h3>", unsafe_allow_html=True)
    st.write("---")
    
    st.subheader("👥 Anggota Kelompok:")
    col1, col2 = st.columns(2)
    with col1:
        st.info("1. **ANDIKA DWI PRASHOJO**\n2. **JAWAHER SABRINA A**\n3. **NAELY LUTHFIYAH ARIF**")
    with col2:
        st.info("4. **SALWA AZKA SABANA**\n5. **ALEX KUSUMAH**")
        
    st.write("---")
    st.markdown("<h4 style='text-align: center;'>Pilih Menu Aplikasi:</h4>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔬 Tata Penamaan & Reaksi Senyawa", use_container_width=True, type="primary"): go_to('tatanama')
    with c2:
        if st.button("📝 Latihan Soal Tebak Struktur", use_container_width=True): go_to('latihan')

# ==========================================
# 2. HALAMAN TATA PENAMAAN & REAKSI
# ==========================================
elif st.session_state.page == 'tatanama':
    if st.button("⬅️ Kembali ke Cover"): go_to('cover')
    
    st.title("🧪 Tata Penamaan Senyawa Organik (Multi-Lingual / IUPAC / Trivial)")
    st.caption("Cakupan: Hidrokarbon, Alkohol, Fenol, Eter, Asam Karboksilat & Derivat, Amina, Benzena, Lemak, Aldehid, Keton, Protein.")

    # Input pengguna (Fleksibel bahasa & penamaan)
    input_user = st.text_input("Masukkan Nama Senyawa (Contoh: etil alkohol / ethanol / asam cuka / propanon):", "Etanol")
    
    if st.button("Mulai Proses", type="primary"):
        # Pembersihan teks input agar COCOK dengan database map
        nama_bersih = input_user.strip().lower()
        
        if nama_bersih in DATABASE_SENYAWA:
            id_standard = DATABASE_SENYAWA[nama_bersih]
            info_senyawa = DATA_KIMIA.get(id_standard, {
                "cid": "cid:241", "nama_resmi": input_user.title(),
                "bm": "100.1 g/mol (Estimasi)", "td": "N/A",
                "sifat": "Senyawa organik turunan.", "reaktivitas": "Dapat mengalami reaksi organik standar."
            })
            
            st.success(f"✔️ Senyawa Terdeteksi secara Sistem: **{info_senyawa['nama_resmi']}**")
            
            col_img, col_info = st.columns([2, 1])
            with col_img:
                st.markdown("**Struktur 3D (Model Molymod Interaktif):**")
                render_3d_mol(info_senyawa["cid"])
                
            with col_info:
                st.markdown("**Informasi Fisika & Kimia:**")
                st.write(f"- ⚖️ **Berat Molekul:** {info_senyawa['bm']}")
                st.write(f"- 🌡️ **Titik Didih:** {info_senyawa['td']}")
                st.write(f"- 🛡️ **Sifat Bahan:** {info_senyawa['sifat']}")
                st.write(f"- ⚡ **Reaktivitas:** {info_senyawa['reaktivitas']}")
                
            # --- MENU REAKSI OPSIONAL ---
            st.write("---")
            st.subheader("🔄 Prediksi Reaksi Kimia (Opsional)")
            reaktan_lain = st.text_input("Masukkan senyawa reaktan lain (Contoh: K2Cr2O7, NaOH, HCl):", "")
            
            if reaktan_lain:
                if st.button("Reaksikan!"):
                    st.markdown("### 📜 Hasil Analisis Mekanisme Reaksi")
                    reaktan_bersih = reaktan_lain.strip().lower()
                    
                    # Logika percabangan reaksi otomatis
                    if id_standard == "ethanol" and reaktan_bersih in ["k2cr2o7", "o2", "oksidator"]:
                        st.info("**Jenis Reaksi:** Oksidasi Alkohol Primer")
                        st.write("**Mekanisme:** Etanol dioksidasi melepaskan hidrogen menjadi Etanal (Aldehid), lalu teroksidasi lebih lanjut menjadi Asam Asetat.")
                        st.write("**Nama Produk Baru:** Asam Asetat (Acetic Acid)")
                        
                        c_r1, c_r2 = st.columns(2)
                        with c_r1:
                            st.markdown("**Struktur 3D Hasil Reaksi (Produk):**")
                            render_3d_mol(DATA_KIMIA["acetic_acid"]["cid"])
                        with c_r2:
                            st.markdown("**Data Produk Baru:**")
                            st.write(f"- **Berat Molekul:** {DATA_KIMIA['acetic_acid']['bm']}")
                            st.write(f"- **Titik Didih:** {DATA_KIMIA['acetic_acid']['td']}")
                    else:
                        st.info("**Jenis Reaksi:** Substitusi / Adisi Teoretis")
                        st.write(f"Terjadi pemutusan ikatan pada gugus aktif {info_senyawa['nama_resmi']} akibat serangan dari {reaktan_lain}.")
        else:
            st.error(f"❌ Nama senyawa '{input_user}' belum terdaftar di database lokal aplikasi. Pastikan penulisan ejaan benar.")

# ==========================================
# 3. HALAMAN LATIHAN SOAL
# ==========================================
elif st.session_state.page == 'latihan':
    if st.button("⬅️ Kembali ke Cover"): go_to('cover')
    
    st.title("📝 Latihan Soal Kimia Organik")
    
    bank_soal = [
        {"struktur": "CH3 - CH2 - OH", "jawaban": ["etanol", "etil alkohol", "ethanol", "ethyl alcohol"], "pembahasan": "Struktur memiliki gugus fungsi -OH (alkohol) dengan 2 atom karbon."},
        {"struktur": "CH3 - COOH", "jawaban": ["asam etanoat", "asam asetat", "asam cuka", "acetic acid"], "pembahasan": "Memiliki gugus fungsi asam karboksilat (-COOH) dengan total 2 rantai karbon."},
        {"struktur": "CH3 - CO - CH3", "jawaban": ["propanon", "aseton", "acetone", "propanone"], "pembahasan": "Senyawa keton/alkanon paling sederhana dengan 3 atom C."}
    ]
    
    current = st.session_state.current_question
    if current >= len(bank_soal):
        st.success("🎉 Hebat! Anda telah menyelesaikan semua soal yang tersedia.")
        if st.button("Ulangi dari Awal"):
            st.session_state.current_question = 0
            st.rerun()
    else:
        st.info(f"**Soal No. {current + 1}**")
        st.code(bank_soal[current]["struktur"], language="text")
        
        user_ans = st.text_input("Jawaban Anda (Bisa Indonesia/Inggris/IUPAC/Trivial):", key=f"ans_{current}")
        
        if st.button("Kirim Jawaban"):
            if user_ans.strip().lower() in bank_soal[current]["jawaban"]:
                st.success("🎯 Tepat Sekali! Jawaban Anda Benar.")
            else:
                st.error(f"❌ Kurang tepat. Pilihan jawaban benar: {', '.join(bank_soal[current]['jawaban'])}")
            st.markdown(f"**💡 Pembahasan:** {bank_soal[current]['pembahasan']}")
            
        if st.button("Soal Selanjutnya ➡️"):
            st.session_state.current_question += 1
            st.rerun()
