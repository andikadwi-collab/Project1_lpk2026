import streamlit as st
import requests
import py3Dmol
import streamlit.components.v1 as components

# ==========================================
# 1. KAMUS TRANSLASI & ENGINE DATABASE LOKAL
# ==========================================

def translate_id_to_en(nama_senyawa):
    """Translasi nama Indonesia (IUPAC/Trivial) ke Inggris untuk pencarian PubChem API"""
    kamus = {
        "etanol": "ethanol", "alkohol": "ethanol",
        "metanol": "methanol",
        "metana": "methane", "etana": "ethane", "propana": "propane", "butana": "butane",
        "asam asetat": "acetic acid", "asam cuka": "acetic acid",
        "aseton": "acetone", "propanon": "acetone",
        "benzena": "benzene", "fenol": "phenol",
        "etil asetat": "ethyl acetate", "kloroform": "chloroform",
        "kloroetana": "chloroethane", "etil klorida": "chloroethane",
        "etena": "ethene", "etilena": "ethene",
        "asetilena": "acetylene", "etuna": "acetylene",
        "bromana": "bromomethane", "bromometana": "bromomethane",
        "butil asetat": "butyl acetate", "n-butanol": "1-butanol", "butanol": "1-butanol"
    }
    nama_clean = nama_senyawa.lower().strip()
    return kamus.get(nama_clean, nama_clean)

def cek_reaksi_kimia(senyawa1, senyawa2):
    """
    Database simulasi reaksi organik komprehensif berdasarkan literatur teori utama.
    Mengembalikan nama produk (EN), nama produk (ID), jenis reaksi, dan penjelasan mendalam.
    """
    s1 = senyawa1.lower().strip()
    s2 = senyawa2.lower().strip()
    
    # Kumpulan kondisi reaksi pasang-memasang
    # 1. Esterifikasi (Asam Karboksilat + Alkohol)
    if ((s1 == "asam asetat" or s1 == "asam cuka") and s2 in ["etanol", "alkohol"]) or \
       (s1 in ["etanol", "alkohol"] and (s2 == "asam asetat" or s2 == "asam cuka")):
        return {
            "hasil_en": "ethyl acetate", "hasil_id": "Etil Asetat (Ester)",
            "jenis": "Reaksi Esterifikasi (Kondensasi)",
            "mekanisme": "Reaksi substitusi nukleofil asil senyawa asam karboksilat dengan alkohol. Gugus -OH dari asam asetat lepas bersama atom H dari alkohol membentuk H2O, menyisakan ikatan ester baru.",
            "sifat_kimia": "Mudah terbakar, kurang reaktif terhadap oksidator, mengalami hidrolisis kembali jika dipanaskan dengan asam/basa kuat.",
            "sifat_fisika": "Cairan bening, aroma buah khas (fruity), titik didih ~77°C, kelarutan sedang dalam air."
        }
    
    if ((s1 == "asam asetat" or s1 == "asam cuka") and s2 in ["butanol", "n-butanol"]) or \
       (s1 in ["butanol", "n-butanol"] and (s2 == "asam asetat" or s2 == "asam cuka")):
        return {
            "hasil_en": "butyl acetate", "hasil_id": "Butil Asetat (Ester)",
            "jenis": "Reaksi Esterifikasi Fischer",
            "mekanisme": "Alkohol rantai menengah (butanol) menyerang karbon karbonil terprotonasi dari asam asetat menghasilkan ester beraroma pisang.",
            "sifat_kimia": "Stabil pada kondisi normal, terhidrolisis menjadi penyusunnya lewat katalis asam/basa.",
            "sifat_fisika": "Cairan berbau harum buah pisang, titik didih ~126°C, densitas lebih ringan dari air."
        }

    # 2. Substitusi Radikal Klorinasi Alkana (Metana + Klorin/Kloroform fiktif pereaksi)
    if (s1 == "metana" and "klor" in s2) or ("klor" in s1 and s2 == "metana"):
        return {
            "hasil_en": "chloromethane", "hasil_id": "Klorometana (Metil Klorida)",
            "jenis": "Reaksi Substitusi Radikal Bebas",
            "mekanisme": "Melalui tiga tahapan: Inisiasi (pembentukan radikal Cl• oleh UV), Propagasi (penyerangan rantai alkana), dan Terminasi. Satu atom H digantikan oleh atom Cl.",
            "sifat_kimia": "Dapat mengalami klorinasi lebih lanjut menjadi diklorometana, kloroform, hingga karbon tetraklorida.",
            "sifat_fisika": "Gas tidak berwarna pada suhu kamar, berbau manis, mudah terbakar."
        }

    # 3. Reaksi Adisi Elektrofilik (Etena + Asam/Halogen)
    if (s1 in ["etena", "etilena"] and "asam asetat" in s2) or ("asam asetat" in s1 and s2 in ["etena", "etilena"]):
        return {
            "hasil_en": "ethyl acetate", "hasil_id": "Etil Asetat",
            "jenis": "Reaksi Adisi Karboksilasi",
            "mekanisme": "Ikatan pi (π) yang kaya elektron pada etena menyerang proton asam, membentuk karbokation zat antara yang kemudian diserang oleh anion asetat.",
            "sifat_kimia": "Merupakan pelarut polar aprotik yang umum digunakan industri.",
            "sifat_fisika": "Sama seperti sifat etil asetat dari jalur esterifikasi."
        }

    return None

# ==========================================
# 2. PENGAMBILAN DATA API PUBCHEM
# ==========================================

@st.cache_data(show_spinner=False)
def get_pubchem_data(compound_name):
    """Mengambil properti fisis, kimia, dan data SDF 3D langsung dari PubChem API"""
    base_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}"
    try:
        prop_url = f"{base_url}/property/MolecularFormula,MolecularWeight,IUPACName,XLogP,CanonicalSMILES/JSON"
        res = requests.get(prop_url, timeout=5).json()
        if "PropertyTable" not in res:
            return None
        
        properties = res["PropertyTable"]["Properties"][0]
        cid = properties.get("CID")
        
        # Ambil struktur koordinat 3D konformers
        sdf_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d"
        sdf_res = requests.get(sdf_url, timeout=5)
        sdf_data = sdf_res.text if sdf_res.status_code == 200 else None
        
        return {"properties": properties, "sdf": sdf_data}
    except Exception:
        return None

def tampilkan_molymod_3d(sdf_data):
    """Merender objek 3D molekul bergaya Molymod menggunakan py3Dmol"""
    if not sdf_data:
        st.warning("⚠️ Model 3D koordinat tidak ditemukan di repositori PubChem.")
        return
    
    view = py3Dmol.view(width=500, height=350)
    view.addModel(sdf_data, 'sdf')
    # Konfigurasi gaya visualisasi Molymod (Sphere-Stick Campuran)
    view.setStyle({'sphere': {'scale': 0.3}, 'stick': {'radius': 0.18}})
    view.zoomTo()
    html_content = view._make_html()
    components.html(html_content, height=360)

# ==========================================
# 3. INTERFASI APLIKASI STREAMLIT
# ==========================================

st.set_page_config(page_title="Aplikasi Tata Penamaan Organik", layout="wide")

# Sidebar Menu Navigasi
st.sidebar.title("📚 Navigasi")
menu = st.sidebar.radio("Pilih Modul:", ["Visualisasi & Prediksi Reaksi", "Latihan Soal Mandiri (10 Soal)"])

# ------------------------------------------
# MODUL 1: VISUALISASI & REAKSI
# ------------------------------------------
if menu == "Visualisasi & Prediksi Reaksi":
    st.title("🧪 Modul Visualisasi 3D & Ensiklopedia Senyawa Organik")
    st.write("Masukkan nama IUPAC atau trivial Indonesia. Sistem akan mencari struktur kimia dan memetakan sifat fisis-kimia berdasar literatur.")
    
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        senyawa_1 = st.text_input("Nama Senyawa Utama (Bahasa Indonesia/Inggris):", placeholder="Contoh: etanol, metana, etena")
    with col_in2:
        senyawa_2 = st.text_input("Senyawa Pereaksi Tambahan (Opsional):", placeholder="Contoh: asam asetat")
        
    if st.button("Mulai Analisis Kimia", type="primary"):
        if senyawa_1:
            nama_en_1 = translate_id_to_en(senyawa_1)
            with st.spinner("Sedang mengunduh dan menganalisis struktur data dari PubChem..."):
                data_1 = get_pubchem_data(nama_en_1)
                
            if data_1:
                st.success(f"🔍 Senyawa Ditemukan: {senyawa_1.title()}")
                c1, c2 = st.columns([1.2, 1])
                
                with c1:
                    st.markdown("#### 🗼 Struktur Geometri 3D (Gaya Molymod)")
                    tampilkan_molymod_3d(data_1['sdf'])
                    st.caption("Gunakan mouse Anda untuk memutar, menggeser, atau memperbesar struktur molekul di atas.")
                    
                with c2:
                    st.markdown("#### 📖 Sifat Fisika & Karakteristik Dasar")
                    p = data_1['properties']
                    st.markdown(f"""
                    * **Nama IUPAC Resmi (EN):** `{p.get('IUPACName', 'N/A')}`
                    * **Rumus Molekul:** {p.get('MolecularFormula', 'N/A')}
                    * **Berat Molekul:** {p.get('MolecularWeight', 'N/A')} g/mol
                    * **LogP (Koefisien Partisi Oktanol/Air):** `{p.get('XLogP', 'N/A')}` *(Menunjukkan tingkat hidrofobisitas/lipofisitas senyawa)*
                    * **Canonical SMILES:** `{p.get('CanonicalSMILES', 'N/A')}`
                    """)
                    
                    # Tambahan literatur statis sekunder teoretis
                    st.markdown("#### ⚗️ Sifat Kimia & Reaktivitas Umum (Teori)")
                    if "ol" in nama_en_1:
                        st.info("💡 **Gugus Alkohol (-OH):** Memiliki ikatan hidrogen antarmolekul yang kuat menyebabkan titik didih tinggi, bersifat polar, dapat dioksidasi menjadi aldehida/keton atau asam karboksilat, serta dapat mengalami esterifikasi.")
                    elif "acid" in nama_en_1 or "asam" in senyawa_1.lower():
                        st.info("💡 **Gugus Asam Karboksilat (-COOH):** Bersifat asam lemah, larut baik dalam pelarut polar, dapat bereaksi dengan alkohol membentuk senyawa ester aromatik melalui reaksi dehidrasi.")
                    elif "ane" in nama_en_1 or "ana" in senyawa_1.lower():
                        st.info("💡 **Golongan Alkana (Hidrokarbon Jenuh):** Bersifat non-polar, relatif tidak reaktif (inersia kimia tinggi) karena ikatan tunggal C-C dan C-H yang kuat. Reaksi utama adalah pembakaran (oksidasi) dan substitusi radikal bebas dengan halogen di bawah sinar UV.")
                    else:
                        st.info("💡 Senyawa ini memiliki kestabilan struktur fungsional organik spesifik sesuai orientasi kerapatan elektron hibridisasinya.")

                # JIKA SENYAWA 2 DIISI (SIMULASI REAKSI)
                if senyawa_2:
                    st.markdown("---")
                    st.header("⚡ Analisis Prediksi Reaksi Kimia")
                    hasil_reaksi = cek_reaksi_kimia(senyawa_1, senyawa_2)
                    
                    if hasil_reaksi:
                        st.success(f"✅ **Terjadi {hasil_reaksi['jenis']}**")
                        
                        rc1, rc2 = st.columns([1, 1.2])
                        with rc1:
                            st.markdown(f"**Mekanisme Reaksi:**\n{hasil_reaksi['mekanisme']}")
                            st.markdown(f"**Sifat Fisika Produk ({hasil_reaksi['hasil_id']}):**\n{hasil_reaksi['sifat_fisika']}")
                            st.markdown(f"**Sifat Kimia Produk:**\n{hasil_reaksi['sifat_kimia']}")
                            
                        with rc2:
                            st.markdown(f"#### 🧬 Struktur 3D Produk: {hasil_reaksi['hasil_id']}")
                            data_produk = get_pubchem_data(hasil_reaksi['hasil_en'])
                            if data_produk:
                                tampilkan_molymod_3d(data_produk['sdf'])
                            else:
                                st.warning("Gagal mengambil model 3D untuk produk reaksi.")
                    else:
                        st.warning("⚠️ Berdasarkan basis data teoretis standar, kombinasi kedua senyawa ini tidak bereaksi secara langsung atau memerlukan kondisi katalis ekstrem di luar jangkauan modul ini.")
            else:
                st.error("❌ Nama senyawa tidak dikenali oleh kamus lokal maupun database PubChem. Periksa kembali ejaan IUPAC/Trivial Anda.")
        else:
            st.warning("Silakan masukkan nama senyawa utama terlebih dahulu.")

# ------------------------------------------
# MODUL 2: LATIHAN SOAL MANDIRI
# ------------------------------------------
elif menu == "Latihan Soal Mandiri (10 Soal)":
    st.title("📝 Latihan Soal Evaluasi Tata Penamaan Senyawa Organik")
    st.write("Uji kemampuan pemahaman nomenklatur IUPAC dan Trivial Indonesia Anda berdasarkan visualisasi rantai karbon berikut.")

    # 10 Soal Komprehensif
    bank_soal = [
        {
            "struktur": "CH3 - CH2 - OH",
            "kunci": ["etanol", "etil alkohol"],
            "pembahasan": "Senyawa ini memiliki 2 atom karbon (et-) dan mengandung gugus hidroksil (-OH) yang merupakan ciri khas alkohol. Nama IUPAC: Etanol; Nama Trivial: Etil Alkohol."
        },
        {
            "struktur": "CH3 - CO - CH3",
            "kunci": ["propanon", "aseton", "dimetil keton"],
            "pembahasan": "Memiliki rantai 3 atom karbon dengan gugus karbonil (=O) non-terminal (di tengah). Nama IUPAC: Propanon; Nama Trivial: Aseton."
        },
        {
            "struktur": "CH3 - COOH",
            "kunci": ["asam asetat", "asam etanoat", "asam cuka"],
            "pembahasan": "Mengandung gugus karboksil (-COOH) dengan total 2 karbon. Nama IUPAC: Asam Etanoat; Nama Trivial: Asam Asetat atau Asam Cuka."
        },
        {
            "struktur": "CH2 = CH - CH3",
            "kunci": ["propena", "propilena"],
            "pembahasan": "Hidrokarbon tak jenuh dengan satu ikatan rangkap dua pada rantai 3 karbon. Nama IUPAC: Propena; Nama Trivial: Propilena."
        },
        {
            "struktur": "CH3 - O - CH3",
            "kunci": ["dimetil eter", "metoksi metana"],
            "pembahasan": "Gugus fungsi eter (-O-) yang menjembatani dua gugus metil (-CH3). Nama IUPAC: Metoksi Metana; Nama Trivial: Dimetil Eter."
        },
        {
            "struktur": "CH3 - CH2 - CHO",
            "kunci": ["propanal", "propionaldehida"],
            "pembahasan": "Gugus formil/aldehida (-CHO) di ujung rantai yang memiliki total 3 atom karbon. Nama IUPAC: Propanal; Nama Trivial: Propionaldehida."
        },
        {
            "struktur": "CH ≡ C - CH3",
            "kunci": ["propuna", "metil asetilena"],
            "pembahasan": "Mengandung ikatan rangkap tiga (alkuna) pada rantai 3 karbon. Nama IUPAC: Propuna; Nama Trivial: Metil Asetilena."
        },
        {
            "struktur": "CH3 - CH2 - CH2 - Cl",
            "kunci": ["1-kloropropana", "propil klorida"],
            "pembahasan": "Senyawa haloalkana di mana atom klorin terikat pada karbon nomor 1 dari rantai propana. Nama IUPAC: 1-Kloropropana; Nama Trivial: Propil Klorida."
        },
        {
            "struktur": "CH3 - COO - CH2 - CH3",
            "kunci": ["etil etanoat", "etil asetat"],
            "pembahasan": "Senyawa ester hasil reaksi asam asetat dan etanol. Bagian alkil adalah etil, gugus alkanoatnya adalah asetat. Nama IUPAC: Etil Etanoat; Nama Trivial: Etil Asetat."
        },
        {
            "strong_title": "Soal Bonus Tantangan",
            "struktur": "CH3 - CH(OH) - CH3",
            "kunci": ["2-propanol", "isopropanol", "isopropil alkohol"],
            "pembahasan": "Gugus alkohol terikat pada atom karbon nomor 2 (karbon sekunder) dari 3 total rantai karbon utama. Nama IUPAC: 2-Propanol; Nama Trivial: Isopropanol / Isopropil Alkohol."
        }
    ]

    # Inisialisasi Session State Indeks Soal agar tidak reset saat klik tombol
    if 'idx_soal' not in st.session_state:
        st.session_state.idx_soal = 0
    if 'skor' not in st.session_state:
        st.session_state.skor = 0

    cur_idx = st.session_state.idx_soal

    if cur_idx < len(bank_soal):
        soal = bank_soal[cur_idx]
        st.info(f"### 📌 Soal Ke-{cur_idx + 1} dari {len(bank_soal)}")
        
        # Penampilan Soal
        st.markdown(f"""
        Identifikasi dan tebak nama senyawa dengan struktur rantai berikut:
        ### `` {soal['struktur']} ``
        """)
        
        jawaban = st.text_input("Ketik Jawaban Anda di sini (IUPAC / Trivial Indonesia):", key=f"ans_{cur_idx}").strip().lower()
        
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            tombol_cek = st.button("Kirim Jawaban")
            
        if tombol_cek:
            if jawaban:
                # Validasi jawaban
                cocok = any(kunci_jwb in jawaban for kunci_jwb in soal['kunci'])
                if cocok:
                    st.success("🎉 **Benar Sekali!** Jawaban Anda tepat secara nomenklatur.")
                else:
                    st.error(f"❌ **Kurang Tepat.** Jawaban yang benar bisa berupa: {', '.join([k.title() for k in soal['kunci']])}")
                
                # Tampilkan Pembahasan
                with st.expander("📖 Lihat Penjelasan Pembahasan Teori"):
                    st.markdown(soal['pembahasan'])
            else:
                st.warning("Silakan isi jawaban terlebih dahulu sebelum menekan tombol cek.")
                
        st.markdown("---")
        if st.button("Lanjut ke Soal Berikutnya ➡️"):
            st.session_state.idx_soal += 1
            st.columns(1) # trigger refresh halaman streamlit kuno
            st.rerun()
            
    else:
        st.balloons()
        st.success("🌟 **Luar Biasa! Anda telah menyelesaikan seluruh 10 soal latihan tata nama organik.**")
        if st.button("🔄 Ulangi Latihan dari Awal"):
            st.session_state.idx_soal = 0
            st.rerun()
