import streamlit as st

# Proteksi impor pustaka agar aplikasi tidak crash jika pustaka belum terinstal di server
HAS_LIBS = True
try:
    import pubchempy as pcp
    from stmol import showmol
    import py3Dmol
except ImportError:
    HAS_LIBS = False

# Pengaturan dasar halaman Streamlit
st.set_page_config(
    page_title="ChemoVerse 3D - Analisis Senyawa Organik",
    page_icon="🧪",
    layout="wide"
)

# ==========================================
# 1. HEADER & IDENTITAS APLIKASI
# ==========================================
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>PROJEK APLIKASI KIMIA ORGANIK</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #7ED321;'>Visualisator Struktur 3D & Data Properti Senyawa</h3>", unsafe_allow_html=True)
st.write("---")

# Validasi instalasi library
if not HAS_LIBS:
    st.error("🚨 Pustaka pendukung (`pubchempy`, `stmol`, `py3Dmol`) belum terpasang. Pastikan file `requirements.txt` sudah benar di GitHub Anda.")
    st.stop()

# ==========================================
# 2. DICTIONARY PENERJEMAH (INDONESIA -> INGGRIS)
# ==========================================
# Membantu API PubChem mengenali nama trivial/IUPAC khas Bahasa Indonesia
KAMUS_BAHASA = {
    "etanol": "ethanol", "metanol": "methanol", "propanol": "propanol", "butanol": "butanol",
    "etil alkohol": "ethyl alcohol", "metil alkohol": "methyl alcohol", 
    "benzena": "benzene", "fenol": "phenol", "toluena": "toluene", 
    "asam asetat": "acetic acid", "asam cuka": "acetic acid", "asam format": "formic acid", 
    "asam semut": "formic acid", "asam propanoat": "propanoic acid", 
    "aseton": "acetone", "propanon": "propanone", "etanal": "ethanal", "asetaldehid": "acetaldehyde",
    "metana": "methane", "etana": "ethane", "propana": "propane", "butana": "butane",
    "etena": "ethene", "etilena": "ethylene", "etuna": "ethyne", "asetilena": "acetylene",
    "dimetil eter": "dimethyl ether", "metoksi metana": "methoxymethane", 
    "kloroform": "chloroform", "anilin": "aniline", "glisin": "glycine"
}

def bersihkan_dan_terjemahkan(nama):
    nama_clean = nama.strip().lower()
    # Jika ada di kamus Indonesia, gunakan terjemahan Inggrisnya untuk query API PubChem
    return KAMUS_BAHASA.get(nama_clean, nama_clean)

# ==========================================
# 3. INTERFACE UTAMA & LOGIKA PENCARIAN
# ==========================================
st.subheader("🧪 Pencarian & Analisis Senyawa Organik")
st.write("Masukkan nama senyawa organik (Contoh: *Etanol*, *Acid Asetat*, *Benzena*, *Acetone*, *Propana*).")

# Input pengguna (Mendukung IUPAC/Trivial, Indo/Inggris)
input_senyawa = st.text_input("Nama Senyawa:", value="Etanol")

if st.button("Mulai Proses Analisis", type="primary"):
    nama_query = bersihkan_dan_terjemahkan(input_senyawa)
    
    with st.spinner(f"Mencari data untuk '{input_senyawa}' di database PubChem..."):
        try:
            # Mencari senyawa berdasarkan nama via PubChem API
            hasil_pencarian = pcp.get_compounds(nama_query, 'name')
            
            if hasil_pencarian:
                senyawa = hasil_pencarian[0]
                cid = senyawa.cid
                rumus_molekul = senyawa.molecular_formula
                berat_molekul = senyawa.molecular_weight
                
                st.success(f"🎉 Senyawa ditemukan! **{input_senyawa.title()}** (PubChem CID: {cid})")
                st.write("---")
                
                # Layout Kolom: Kiri untuk Struktur 3D, Kanan untuk Informasi Kimia
                kolom_kiri, kolom_kanan = st.columns([3, 2])
                
                with kolom_kiri:
                    st.markdown("#### 🌐 Struktur Rantai 3D (Model Molymod Interaktif)")
                    st.caption("Anda dapat memutar molekul dengan klik-drag, dan melakukan zoom dengan scroll mouse.")
                    
                    # Logika render menggunakan py3Dmol
                    viewer = py3Dmol.view(query=f'cid:{cid}', width=500, height=450)
                    # Mengatur gaya visualisasi agar menyerupai Molymod asli (Stick & Sphere)
                    viewer.setStyle({
                        'stick': {'colorscheme': 'Jmol', 'radius': 0.2},
                        'sphere': {'colorscheme': 'Jmol', 'radius': 0.4}
                    })
                    viewer.setBackgroundColor('#ffffff')
                    viewer.zoomTo()
                    
                    # Tampilkan di halaman web Streamlit
                    showmol(viewer, height=450, width=650)
                
                with kolom_kanan:
                    st.markdown("#### 📊 Informasi Properti Senyawa")
                    
                    # Data Resmi dari API
                    st.metric(label="🧪 Rumus Molekul", value=rumus_molekul)
                    st.metric(label="⚖️ Berat Molekul", value=f"{berat_molekul} g/mol")
                    
                    # Estimasi Titik Didih berdasarkan data kelompok senyawa umum
                    st.markdown("**🌡️ Titik Didih (Estimasi/Prediksi):**")
                    nama_lowercase = input_senyawa.lower()
                    
                    if "ol" in nama_lowercase or "alkohol" in nama_lowercase:
                        st.write("- Berkisar antara **78°C s.d. 150°C** (tergantung panjang rantai karbon). Memiliki titik didih relatif tinggi karena adanya ikatan hidrogen antar gugus fungsi `-OH`.")
                    elif "asam" in nama_lowercase or "acid" in nama_lowercase:
                        st.write("- Berkisar antara **118°C s.d. 200°C** (mengalami asosiasi membentuk dimer melalui ikatan hidrogen yang sangat kuat).")
                    elif "benzena" in nama_lowercase or "benzene" in nama_lowercase or "fenol" in nama_lowercase:
                        st.write("- Berkisar di atas **80°C**. Struktur cincin aromatik yang stabil meningkatkan energi yang dibutuhkan untuk fase penguapan.")
                    elif "metana" in nama_lowercase or "etana" in nama_lowercase or "propana" in nama_lowercase or "butana" in nama_lowercase:
                        st.write("- Berkisar antara **-161°C s.d. -0.5°C** (berwujud gas pada suhu ruang karena hanya memiliki gaya London/Van der Waals yang lemah).")
                    else:
                        st.write("- Berdasarkan tren struktur umum, senyawa volatil ini memiliki titik didih menengah tergantung pada interaksi dipol-dipol molekulnya.")
                    
                    # Deskripsi Teoretis Reaktivitas Senyawa Organik
                    st.markdown("**⚡ Karakteristik Reaktivitas:**")
                    if "ol" in nama_lowercase or "alkohol" in nama_lowercase:
                        st.info("Dapat mengalami reaksi **Oksidasi** (alkohol primer menjadi aldehid/asam karboksilat), reaksi **Substitusi** nukleofilik dengan asam halida, serta reaksi **Eliminasi** (dehidrasi) membentuk alkena.")
                    elif "asam" in nama_lowercase or "acid" in nama_lowercase:
                        st.info("Dapat mengalami reaksi **Esterifikasi** jika direaksikan dengan alkohol, bersifat asam lemah, dan dapat berikatan dengan basa membentuk garam organik.")
                    elif "benzena" in nama_lowercase or "benzene" in nama_lowercase:
                        st.info("Sangat stabil terhadap reaksi adisi karena resonansi aromatik. Cenderung mudah mengalami reaksi **Substitusi Elektrofilik Aromatik** seperti Nitrasi, Sulfonasi, dan Halogenasi.")
                    elif "ena" in nama_lowercase or "una" in nama_lowercase:
                        st.info("Memiliki ikatan tak jenuh (rangkap), membuatnya sangat reaktif terhadap reaksi **Adisi** (Adisi hidrogen, halogen, atau asam halida mengikuti aturan Markovnikov).")
                    else:
                        st.info("Cenderung kurang reaktif (alkana jenuh). Dapat mengalami reaksi **Substitusi Radikal** jika dipicu oleh sinar UV atau reaksi pembakaran (Oksidasi penuh dengan gas oksigen).")
            else:
                st.error("❌ Nama senyawa tidak dikenali oleh database PubChem. Periksa kembali ejaan IUPAC atau Trivial Anda.")
        except Exception as e:
            st.error(f"Terjadi kesalahan koneksi atau pencarian data: {str(e)}")
