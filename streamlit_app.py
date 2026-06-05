import streamlit as st
import requests

# Integrasi pustaka kimia & visualisasi 3D
HAS_LIBS = True
try:
    from stmol import showmol
    import py3Dmol
    import pubchempy as pcp
    from rdkit import Chem
except ImportError:
    HAS_LIBS = False

st.set_page_config(page_title="ChemoVerse - Kimia Organik 3D", layout="wide")

# ==========================================
# FUNGSI PEMBANTU (CHEMICAL ENGINE)
# ==========================================
def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()

def terjemahkan_ke_inggris(nama_indo):
    """Membantu menerjemahkan beberapa istilah trivial/IUPAC Indonesia ke Inggris agar ramah API PubChem"""
    kamus = {
        "etanol": "ethanol", "metanol": "methanol", "benzena": "benzene",
        "asam asetat": "acetic acid", "asam cuka": "acetic acid", "aseton": "acetone",
        "propanon": "propanone", "fenol": "phenol", "etena": "ethene", "etilena": "ethylene",
        "etuna": "ethyne", "asetilena": "acetylene", "glisin": "glycine", "glukosa": "glucose"
    }
    nama_clean = nama_indo.strip().lower()
    return kamus.get(nama_clean, nama_indo)

def dapatkan_data_pubchem(nama_senyawa):
    """Mencari data berat molekul dan CID dari PubChem secara real-time"""
    nama_query = terjemahkan_ke_inggris(nama_senyawa)
    try:
        results = pcp.get_compounds(nama_query, 'name')
        if results:
            comp = results[0]
            return {
                "cid": comp.cid,
                "smiles": comp.isomeric_smiles,
                "mw": f"{comp.molecular_weight} g/mol",
                "formula": comp.molecular_formula
            }
    except Exception:
        pass
    return None

def render_3d_by_cid(cid):
    """Merender struktur 3D interaktif ala Molymod menggunakan py3Dmol via PubChem CID"""
    if not HAS_LIBS:
        st.warning("Visualisasi 3D tidak tersedia. Pustaka belum terpasang.")
        return
    try:
        xyzview = py3Dmol.view(query=f'cid:{cid}', width=400, height=400)
        xyzview.setStyle({'stick': {}, 'sphere': {'radius': 0.3}})
        xyzview.setBackgroundColor('#f0f2f6')
        xyzview.zoomTo()
        showmol(xyzview, height=400, width=800)
    except Exception as e:
        st.error("Gagal memuat model 3D senyawa ini.")

# Inisialisasi Session State
if 'page' not in st.session_state: st.session_state.page = 'cover'
if 'current_question' not in st.session_state: st.session_state.current_question = 0
if 'score' not in st.session_state: st.session_state.score = 0

if not HAS_LIBS:
    st.error("🚨 Pustaka pendukung belum terinstal di environment Anda! Pastikan requirements.txt sudah sesuai.")

# ==========================================
# 1. COVRER DEPAN / HALAMAN UTAMA
# ==========================================
if st.session_state.page == 'cover':
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>PROJEK APLIKASI KIMIA ORGANIK</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #7ED321;'>Visualisator Molekul 3D & Prediktor Reaksi Teoretis</h3>", unsafe_allow_html=True)
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
# 2. TATA PENAMAAN & PREDIKSI REAKSI
# ==========================================
elif st.session_state.page == 'tatanama':
    if st.button("⬅️ Kembali ke Cover"): go_to('cover')
    
    st.title("🧪 Tata Penamaan Senyawa Organik")
    st.caption("Mendukung: Hidrokarbon, Alkohol, Fenol, Eter, Asam Karboksilat & Derivat, Amina, Benzena, Lemak/Minyak, Aldehid, Keton, Protein.")

    # Input Fleksibel (IUPAC / Trivial / Indo / Inggris)
    nama_input = st.text_input("Masukkan nama senyawa organik:", "Etanol")
    
    if st.button("Mulai Proses", type="primary"):
        with st.spinner("Mencari data senyawa dari basis data kimia..."):
            data = dapatkan_data_pubchem(nama_input)
            
            if data:
                st.session_state['current_compound'] = data
                st.session_state['current_name'] = nama_input
                st.success(f"✔️ Senyawa Ditemukan: **{nama_input.title()}** ({data['formula']})")
            else:
                st.error("❌ Senyawa tidak ditemukan atau ejaan salah. Coba gunakan nama IUPAC standard.")

    # Jika senyawa berhasil di-load, tampilkan informasinya
    if 'current_compound' in st.session_state:
        data = st.session_state['current_compound']
        nama_aktif = st.session_state['current_name']
        
        col_img, col_info = st.columns([2, 1])
        with col_img:
            st.markdown("**Struktur 3D (Model Molymod Interaktif):**")
            render_3d_by_cid(data['cid'])
        with col_info:
            st.markdown("**Informasi Senyawa:**")
            st.write(f"- ⚖️ **Berat Molekul:** {data['mw']}")
            
            # Data statis tambahan untuk estimasi sifat fisik berdasarkan pola umum
            if "ol" in nama_aktif.lower():
                st.write("- 🌡️ **Titik Didih:** ~60 - 100 °C (Tergantung panjang rantai)")
                st.write("- 🛡️ **Sifat Bahan:** Polar, volatil, dapat bercampur air pada rantai pendek.")
                st.write("- ⚡ **Reaktivitas:** Dapat mengalami dehidrasi, oksidasi, atau substitusi gugus -OH.")
            elif "asam" in nama_aktif.lower() or "acid" in nama_aktif.lower():
                st.write("- 🌡️ **Titik Didih:** >100 °C (Ikatan hidrogen kuat)")
                st.write("- 🛡️ **Sifat Bahan:** Asam lemah, korosif ringan, berbau menyengat.")
                st.write("- ⚡ **Reaktivitas:** Reaksi esterifikasi dengan alkohol, netralisasi dengan basa.")
            else:
                st.write("- 🌡️ **Titik Didih:** Bervariasi berdasarkan struktur molekul.")
                st.write("- 🛡️ **Sifat Bahan:** Senyawa organik umum.")
                st.write("- ⚡ **Reaktivitas:** Reaktivitas ditentukan oleh gugus fungsi bawaan.")

        # --- FITUR REAKSI OPSIONAL ---
        st.write("---")
        st.subheader("🔄 Reaksi Kimia Teoretis (Opsional)")
        reaktan = st.text_input("Masukkan reaktan kedua untuk direaksikan (Contoh: HCl, NaOH, O2, K2Cr2O7):", "")
        
        if reaktan and st.button("Mulai Reaksi"):
            st.markdown("### 📜 Hasil Analisis Mekanisme Reaksi")
            r_clean = reaktan.strip().lower()
            n_clean = nama_aktif.strip().lower()
            
            # Pohon Keputusan Reaksi Organik Teoretis
            if ("etanol" in n_clean or "ethanol" in n_clean) and r_clean in ["k2cr2o7", "o2", "oksidator"]:
                st.info("**Jenis Reaksi:** Oksidasi Alkohol Primer")
                st.write("**Mekanisme:** Alkohol primer diserang oksidator menghasilkan senyawa Aldehid (Etanal), kemudian teroksidasi total menjadi Asam Karboksilat.")
                st.write("**Nama Produk Baru:** Asam Asetat (Ethanoic Acid)")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Struktur 3D Produk Akhir:**")
                    render_3d_by_cid(176) # CID Asam Asetat
                with c2:
                    st.write("- **Berat Molekul:** 60.05 g/mol")
                    st.write("- **Titik Didih:** 118 °C")
                    st.write("- **Sifat:** Asam lemah, polar.")
            
            elif ("etena" in n_clean or "ethene" in n_clean) and "hcl" in r_clean:
                st.info("**Jenis Reaksi:** Adisi Elektrofilik (Aturan Markovnikov)")
                st.write("**Mekanisme:** Ikatan rangkap dua (alkena) pecah mengikat atom H dan Cl dari asam halida.")
                st.write("**Nama Produk Baru:** Kloroetana (Ethyl Chloride)")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Struktur 3D Produk Akhir:**")
                    render_3d_by_cid(6337) # CID Kloroetana
                with c2:
                    st.write("- **Berat Molekul:** 64.51 g/mol")
                    st.write("- **Titik Didih:** 12.3 °C")
                    st.write("- **Sifat:** Gas volatil/cairan dingin, anestetik lokal.")
                    
            else:
                st.warning("⚠️ Jenis reaksi spesifik untuk kombinasi ini belum masuk bagan teori otomatis, namun secara konsep teoritis akan terjadi pemutusan atau penataan ulang senyawa berdasarkan hukum termodinamika gugus fungsi terkait.")

# ==========================================
# 3. MENU LATIHAN SOAL (LOOP 10 SOAL BERKELANJUTAN)
# ==========================================
elif st.session_state.page == 'latihan':
    if st.button("⬅️ Kembali ke Cover"): go_to('cover')
    
    st.title("📝 Latihan Soal Kimia Organik")
    st.write("Tebak nama IUPAC atau Trivial dari rumus struktur rantai di bawah ini menggunakan Bahasa Indonesia.")

    # Bank Soal Dinamis (Menggunakan indeks modular untuk mendukung set berikutnya tanpa batas)
    bank_soal = [
        # SET 1 (Soal 1-10)
        {"struktur": "CH3 - CH2 - OH", "jawaban": ["etanol", "etil alkohol"], "pembahasan": "Memiliki rantai karbon 2 (etan-) dengan gugus hidroksil (-OH) yang menandakan senyawa alkohol."},
        {"struktur": "CH3 - COOH", "jawaban": ["asam etanoat", "asam asetat", "asam cuka"], "pembahasan": "Memiliki gugus fungsi karboksil (-COOH) dengan total 2 karbon."},
        {"struktur": "CH3 - CO - CH3", "jawaban": ["propanon", "aseton"], "pembahasan": "Senyawa keton/alkanon paling sederhana yang memiliki 3 atom karbon."},
        {"struktur": "CH3 - CHO", "jawaban": ["etanal", "asetaldehid"], "pembahasan": "Gugus fungsi aldehid (-CHO) dengan rantai karbon utama berjumlah 2."},
        {"struktur": "CH3 - O - CH3", "jawaban": ["metoksi metana", "dimetil eter"], "pembahasan": "Senyawa eter (alkoksi alkana) dengan dua gugus metil di sisi oksigen."},
        {"struktur": "CH3 - CH2 - CH3", "jawaban": ["propana"], "pembahasan": "Hidrokarbon jenuh (alkana) dengan rantai lurus 3 atom karbon."},
        {"struktur": "CH2 = CH2", "jawaban": ["etena", "etilena"], "pembahasan": "Hidrokarbon tidak jenuh dengan satu ikatan rangkap dua (alkena)."},
        {"struktur": "CH ≡ CH", "jawaban": ["etuna", "asetilena"], "pembahasan": "Hidrokarbon alkuna terkecil yang memiliki ikatan rangkap tiga."},
        {"struktur": "CH3 - COO - CH3", "jawaban": ["metil etanoat", "metil asetat"], "pembahasan": "Senyawa ester (alkil alkanoat). Alkil berupa metil, alkanoat berupa etanoat."},
        {"struktur": "CH3 - CH2 - NH2", "jawaban": ["etanamina", "etil amina"], "pembahasan": "Senyawa amina primer yang mengikat gugus etil pada atom nitrogen."},
        
        # SET 2 (Soal 11-20, dst)
        {"struktur": "CH3 - CH2 - CH2 - OH", "jawaban": ["1-propanol", "propil alkohol", "propanol"], "pembahasan": "Alkohol primer dengan rantai lurus 3 atom karbon."},
        {"struktur": "CH3 - CH2 - COOH", "jawaban": ["asam propanoat", "asam propionat"], "pembahasan": "Asam karboksilat dengan total 3 rantai karbon."},
        {"struktur": "CH3 - CH2 - CHO", "jawaban": ["propanal", "propionaldehid"], "pembahasan": "Aldehid dengan total panjang rantai karbon 3."},
        {"struktur": "CH3 - CO - CH2 - CH3", "jawaban": ["butanon", "metil etil keton"], "pembahasan": "Keton dengan total 4 atom karbon, gugus karbonil ada di C nomor 2."},
        {"struktur": "CH3 - O - CH2 - CH3", "jawaban": ["metoksi etana", "metil etil eter"], "pembahasan": "Eter asimetris yang mengikat gugus metil dan etil."},
        {"struktur": "CH3 - CH2 - CH2 - CH3", "jawaban": ["butana", "n-butana"], "pembahasan": "Alkana rantai lurus yang memiliki 4 atom karbon."},
        {"struktur": "CH3 - CH = CH - CH3", "jawaban": ["2-butena"], "pembahasan": "Alkena dengan 4 rantai karbon, posisi ikatan rangkap berada pada nomor 2."},
        {"struktur": "CH3 - C ≡ C - CH3", "jawaban": ["2-butuna"], "pembahasan": "Alkuna dengan ikatan rangkap tiga tepat di tengah rantai C-4."},
        {"struktur": "CH3 - CH2 - COO - CH3", "jawaban": ["metil propanoat"], "pembahasan": "Ester dengan gugus alkil metil dan gugus asam propanoat."},
        {"struktur": "CH3 - CH2 - CH2 - NH2", "jawaban": ["1-propanamina", "propil amina"], "pembahasan": "Amina dengan gugus propil rantai lurus terikat pada gugus amina."}
    ]

    total_soal_tersedia = len(bank_soal)
    idx = st.session_state.current_question % total_soal_tersedia
    
    # Deteksi pergantian set kelipatan 10 soal
    nomor_tampilan = st.session_state.current_question + 1
    set_ke = (st.session_state.current_question // 10) + 1
    
    st.info(f"📋 **Soal No. {nomor_tampilan}** | 🟢 **Skor Benar: {st.session_state.score}**")
    st.subheader(f"Set Latihan ke-{set_ke}")
    
    st.markdown("**Identifikasi rumus struktur di bawah ini:**")
    st.code(bank_soal[idx]["struktur"], language="text")
    
    # Kunci input teks unik per soal agar tidak tumpang tindih
    user_ans = st.text_input("Ketik Jawaban Anda di sini:", key=f"quest_{st.session_state.current_question}")
    
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("Kirim Jawaban ✔️"):
            jawaban_bersih = user_ans.strip().lower()
            if jawaban_bersih in [j.lower() for j in bank_soal[idx]["jawaban"]]:
                st.success("🎯 LUAR BIASA! Jawaban Anda Benar!")
                st.session_state.score += 1
            else:
                st.error(f"❌ SALAH. Jawaban yang diterima: {', '.join(bank_soal[idx]['jawaban'])}")
            
            st.markdown(f"**💡 Pembahasan:** {bank_soal[idx]['pembahasan']}")
            
    with c_btn2:
        if st.button("Soal Selanjutnya ➡️"):
            st.session_state.current_question += 1
            # Notifikasi pergantian set soal setiap kelipatan 10
            if st.session_state.current_question % 10 == 0:
                st.toast(f"Memasuki 10 soal berikutnya pada Set Latihan baru!", icon="🎉")
            st.rerun()
