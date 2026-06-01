import streamlit as st
import requests
import py3Dmol
import streamlit.components.v1 as components
import re

# ==========================================
# 1. ENGINE TRANSLASI OTOMATIS (>1000 SENYAWA)
# ==========================================

def translate_organic_id_to_en(nama_id):
    """
    Mentranslasikan nomenklatur IUPAC/Trivial Indonesia ke Inggris menggunakan pola adaptif.
    Mendukung ribuan kombinasi senyawa organik secara otomatis.
    """
    nama = nama_id.lower().strip()
    
    # Kamus substitusi sufiks & prefiks tata nama organik standar
    replacements = {
        "asam ": "acid ",      "asetat": "acetate",    "formiat": "formate",
        "propionat": "propionate", "butirat": "butyrate",  "oksalat": "oxalate",
        "metil": "methyl",      "etil": "ethyl",        "propil": "propyl",
        "butil": "butyl",        "pentil": "pentyl",      "heksil": "hexyl",
        "heptil": "heptyl",      "oktil": "octyl",        "nonil": "nonyl",
        "dekil": "decyl",        "isopropil": "isopropyl", "isobutil": "isobutyl",
        "fenil": "phenyl",      "benzil": "benzyl",
        "alkohol": "alcohol",    "eter": "ether",        "keton": "ketone",
        "klorida": "chloride",  "bromida": "bromide",   "iodida": "iodide",
        # Sufiks Hidrokarbon & Gugus Fungsi
        "ana$": "ane",          "ena$": "ene",          "una$": "yne",
        "anol$": "anol",        "anal$": "anal",        "anon$": "anone",
        "anoat$": "anoate",     "amina$": "amine",      "amida$": "amide",
        "benzena": "benzene",    "fenol": "phenol",      "anilin": "aniline"
    }
    
    for pattern, repl in replacements.items():
        if pattern.endswith('$'):
            nama = re.sub(pattern[:-1] + "$", repl, nama)
        else:
            nama = re.sub(pattern, repl, nama)
            
    # Kasus khusus Asam Karboksilat (Asam ... anoat -> ...anoic acid)
    if "acid" in nama and nama.endswith("anoate"):
        nama = nama.replace("acid ", "") + " acid"
        nama = re.sub(r"anoate$", "anoic", nama)
        
    return nama

# ==========================================
# 2. DETEKSI & PREDIKSI REAKSI BERBASIS TEORI
# ==========================================

def analisis_prediksi_reaksi(senyawa1, senyawa2):
    """
    Menganalisis jenis reaksi (Adisi, Substitusi, Eliminasi, dll) berdasarkan 
    karakteristik struktur/gugus fungsi dari kedua reaktan.
    """
    s1 = senyawa1.lower().strip()
    s2 = senyawa2.lower().strip()
    
    # 1. REAKSI ADISI (Alkena/Alkuna + Halogen/Asam Halida/Air)
    if any(x in s1 for x in ["ena", "una"]) or any(x in s2 for x in ["ena", "una"]):
        alkena = s1 if any(x in s1 for x in ["ena", "una"]) else s2
        pereaksi = s2 if alkena == s1 else s1
        
        if any(x in pereaksi for x in ["klor", "brom", "iod", "hcl", "hbr", "hi", "h2o", "hidrogen"]):
            return {
                "jenis": "Reaksi Adisi Elektrofilik (Pemutusan Ikatan Rangkap)",
                "mekanisme": f"Ikatan pi ($\pi$) pada `{alkena}` yang kaya elektron diserang oleh agen elektrofilik dari `{pereaksi}`. Ikatan rangkap dua/tiga terbuka menjadi ikatan tunggal (jenuh) mengikuti aturan Markovnikov.",
                "produk_estimasi": "Haloalkana / Alkanol (tergantung jenis pereaksi halogen/asam yang dimasukkan)."
            }
            
    # 2. REAKSI ESTERIFIKASI (Asam Karboksilat + Alkohol)
    is_asam = lambda s: "asam" in s or "anoate acid" in translate_organic_id_to_en(s)
    is_alkohol = lambda s: s.endswith("nol") or "alkohol" in s
    
    if (is_asam(s1) and is_alkohol(s2)) or (is_asam(s2) and is_alkohol(s1)):
        asam_sub = s1 if is_asam(s1) else s2
        alk_sub = s2 if asam_sub == s1 else s1
        return {
            "jenis": "Reaksi Esterifikasi / Kondensasi (Substitusi Nukleofil Asil)",
            "mekanisme": f"Gugus -OH dari `{asam_sub}` berikatan dengan atom H dari gugus hidroksil `{alk_sub}` menghasilkan molekul sampingan $H_2O$. Gugus alkoksi dari alkohol kemudian mensubstitusi posisi -OH pada asam untuk membentuk senyawa Ester.",
            "produk_estimasi": "Alkil Alkanoat (Ester) + Air ($H_2O$)."
        }

    # 3. REAKSI SUBSTITUSI (Alkana + Halogen dengan bantuan UV/Cahaya)
    is_alkana = lambda s: s.endswith("ana") and not "asam" in s
    if (is_alkana(s1) and any(x in s2 for x in ["klor", "brom", "fluor"])) or \
       (is_alkana(s2) and any(x in s1 for x in ["klor", "brom", "fluor"])):
        alk_sub = s1 if is_alkana(s1) else s2
        hal_sub = s2 if alk_sub == s1 else s1
        return {
            "jenis": "Reaksi Substitusi Radikal Bebas (Halogenasi Alkana)",
            "mekanisme": f"Sinar UV memicu homolisis molekul `{hal_sub}` menjadi radikal bebas halogen yang sangat reaktif. Radikal ini menyerang ikatan C-H pada `{alk_sub}`, menggantikan posisi atom H dengan atom halogen secara bertahap.",
            "produk_estimasi": "Haloalkana (Alkil Halida) + Asam Halida (seperti $HCl$ / $HBr$)."
        }

    # 4. REAKSI ELIMINASI (Alkil Halida / Alkohol + Basa Kuat / Asam Pekat Panas)
    if is_alkohol(s1) or is_alkohol(s2) or "kloro" in s1 or "bromo" in s1 or "kloro" in s2 or "bromo" in s2:
        if any(x in s1 or x in s2 for x in ["naoh", "koh", "h2so4", "basa", "asam pekat"]):
            return {
                "jenis": "Reaksi Eliminasi (Pembentukan Ikatan Rangkap / Dehidrasi / Dehidrohalogenasi)",
                "mekanisme": "Pelepasan dua gugus atau atom dari dua atom karbon yang berdekatan ($C_\alpha$ dan $C_\beta$) membentuk ikatan rangkap baru ($\pi$). Mengikuti aturan Zaitsev, di mana hidrogen dilepaskan dari karbon yang mengikat lebih sedikit hidrogen.",
                "produk_estimasi": "Senyawa Hidrokarbon Tak Jenuh (Alkena) + Air/Garam."
            }

    # 5. REAKSI OKSIDASI (Alkohol + Oksidator seperti KMnO4 / K2Cr2O7)
    if is_alkohol(s1) or is_alkohol(s2):
        if any(x in s1 or x in s2 for x in ["kmno4", "k2cr2o7", "oksidator", "oksigen", "o2"]):
            return {
                "jenis": "Reaksi Oksidasi Organik",
                "mekanisme": "Pengurangan ikatan C-H dan peningkatan ikatan C-O pada atom karbon hidroksil. Alkohol primer akan dioksidasi menjadi Alkanal (Aldehida) lalu menjadi Asam Karboksilat. Alkohol sekunder dioksidasi menjadi Alkanon (Keton).",
                "produk_estimasi": "Alkanal / Alkanon / Asam Karboksilat."
            }

    return None

# ==========================================
# 3. KONEKSI DATA API PUBCHEM REST
# ==========================================

@st.cache_data(show_spinner=False)
def ambil_data_pubchem(nama_inggris):
    """Mengambil properti fisis, kimia, dan koordinat 3D terverifikasi dari PubChem"""
    base_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{nama_inggris}"
    try:
        prop_url = f"{base_url}/property/MolecularFormula,MolecularWeight,IUPACName,XLogP,CanonicalSMILES/JSON"
        res = requests.get(prop_url, timeout=5).json()
        if "PropertyTable" not in res:
            return None
        
        properties = res["PropertyTable"]["Properties"][0]
        cid = properties.get("CID")
        
        # Ambil file koordinat model 3D (SDF)
        sdf_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d"
        sdf_res = requests.get(sdf_url, timeout=5)
        sdf_data = sdf_res.text if sdf_res.status_code == 200 else None
        
        return {"properties": properties, "sdf": sdf_data}
    except Exception:
        return None

def render_molymod_3d(sdf_data):
    """Menampilkan penampil molekul 3D interaktif bergaya Molymod"""
    if not sdf_data:
        st.warning("⚠️ Model koordinat ruang 3D tidak tersedia untuk senyawa ini di PubChem.")
        return
    view = py3Dmol.view(width=600, height=400)
    view.addModel(sdf_data, 'sdf')
    # Gaya Molymod: Bola (Sphere-atom) dan Batang (Stick-ikatan)
    view.setStyle({'sphere': {'scale': 0.3}, 'stick': {'radius': 0.2}})
    view.zoomTo()
    components.html(view._make_html(), height=410)

# ==========================================
# 4. ANTARMUKA UTAMA (STREAMLIT APP)
# ==========================================

st.set_page_config(page_title="Tata Penamaan Senyawa Organik", layout="wide")

st.sidebar.title("📌 Menu Utama")
pilihan_menu = st.sidebar.radio("Silakan Pilih Modul:", ["Ensiklopedi & Prediksi Reaksi", "Latihan Soal Mandiri"])

# ------------------------------------------
# MODUL 1: VISUALISASI & PREDIKSI REAKSI
# ------------------------------------------
if pilihan_menu == "Ensiklopedi & Prediksi Reaksi":
    st.title("🧪 Ensiklopedi Kimia Organik & Prediktor Reaksi Teoretis")
    st.write("Mendukung >1000 senyawa lewat translasi otomatis sistem database tervalidasi PubChem NIH.")
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        input_senyawa1 = st.text_input("Nama Senyawa Utama (Bahasa Indonesia):", placeholder="Contoh: heksana, butanol, asam propionat")
    with col_input2:
        input_senyawa2 = st.text_input("Senyawa Pereaksi Tambahan (Opsional):", placeholder="Contoh: bromin, NaOH, etanol")
        
    if st.button("Mulai Analisis Kimia", type="primary"):
        if input_senyawa1:
            nama_en_1 = translate_organic_id_to_en(input_senyawa1)
            
            with st.spinner(f"Mencari data tervalidasi untuk '{nama_en_1}' di PubChem..."):
                data_senyawa1 = ambil_data_pubchem(nama_en_1)
                
            if data_senyawa1:
                st.success(f"✓ Data Berhasil Ditemukan: {input_senyawa1.upper()}")
                
                c1, c2 = st.columns([1.2, 1])
                with c1:
                    st.markdown("### 🧬 Visualisasi 3D (Model Molymod)")
                    render_molymod_3d(data_senyawa1['sdf'])
                
                with c2:
                    st.markdown("### 📘 Sifat Fisika & Karakteristik")
                    props = data_senyawa1['properties']
                    st.markdown(f"""
                    * **Nama Resmi IUPAC (Inggris):** `{props.get('IUPACName', 'N/A')}`
                    * **Rumus Molekul:** **{props.get('MolecularFormula', 'N/A')}**
                    * **Berat Molekul:** `{props.get('MolecularWeight', 'N/A')} g/mol`
                    * **Sifat Lipofilik (LogP):** `{props.get('XLogP', 'N/A')}`
                    * **SMILES Notasi:** `{props.get('CanonicalSMILES', 'N/A')}`
                    """)
                    
                    st.markdown("### ⚗️ Deskripsi Reaktivitas Sifat Kimia")
                    # Klasifikasi Teoretis Otomatis
                    if any(x in nama_en_1 for x in ["ol", "alcohol"]):
                        st.info("💡 **Gugus Alkohol (-OH):** Memiliki sifat polar karena ikatan hidrogen, titik didih cenderung tinggi, dan dapat mengalami reaksi substitusi nukleofil, eliminasi (dehidrasi) menjadi alkena, atau esterifikasi jika direaksikan dengan asam karboksilat.")
                    elif "acid" in nama_en_1:
                        st.info("💡 **Gugus Asam Karboksilat (-COOH):** Bersifat asam lemah, larut dalam pelarut polar, senyawa ini reaktif terhadap alkohol dalam pembentukan senyawa ester berbau harum melalui reaksi kondensasi.")
                    elif "ene" in nama_en_1 or "yne" in nama_en_1:
                        st.info("💡 **Hidrokarbon Tak Jenuh (Alkena/Alkuna):** Sangat reaktif pada ikatan rangkapnya. Reaksi utama yang dominan adalah **Adisi** (pemutusan ikatan rangkap) oleh reagen elektrofilik seperti halogen atau asam halida.")
                    else:
                        st.info("💡 **Karakteristik Umum:** Senyawa ini memiliki tingkat stabilitas fungsional organik hidrokarbon normal sesuai susunan hibridisasi orbital atomnya.")
                
                # JIKA INPUT OPSIONAL DIISI
                if input_senyawa2:
                    st.markdown("---")
                    st.header("⚡ Analisis Mekanisme & Prediksi Jenis Reaksi")
                    
                    info_reaksi = analisis_prediksi_reaksi(input_senyawa1, input_senyawa2)
                    if info_reaksi:
                        st.markdown(f"#### Jenis Klasifikasi: **{info_reaksi['jenis']}**")
                        
                        col_r1, col_r2 = st.columns(2)
                        with col_r1:
                            st.markdown(f"""
                            **Penjelasan Mekanisme Berdasarkan Teori:**
                            {info_reaksi['mekanisme']}
                            """)
                        with col_r2:
                            st.markdown(f"""
                            **Estimasi Sifat & Hasil Produk:**
                            * **Prediksi Utama Produk:** `{info_reaksi['produk_estimasi']}`
                            * **Kondisi Umum:** Reaksi organik jenis ini kerap memerlukan pengaruh lingkungan luar seperti katalis asam ($H^+$), basa kuat, atau paparan energi foton (Sinar UV/Panas).
                            """)
                    else:
                        st.warning("⚠️ Kombinasi kedua senyawa belum terpetakan dalam database aturan reaksi lokal, atau kedua senyawa tidak bereaksi secara spontan pada kondisi standar menurut teori.")
            else:
                st.error("❌ Nama senyawa tidak terdeteksi oleh sistem pencarian PubChem. Pastikan ejaan tata nama IUPAC/Trivial Indonesia Anda sudah tepat.")
        else:
            st.warning("Harap masukkan nama senyawa organik utama.")

# ------------------------------------------
# MODUL 2: LATIHAN SOAL (10 SOAL LENGKAP)
# ------------------------------------------
elif pilihan_menu == "Latihan Soal Mandiri":
    st.title("📝 Evaluasi Mandiri Tata Nama Organik (10 Soal)")
    st.write("Analisis struktur rantai di bawah ini lalu tentukan nama IUPAC atau Trivial Indonesianya!")

    bank_soal = [
        {"str": "CH3 - CH2 - OH", "kunci": ["etanol", "etil alkohol"], "pembahasan": "Memiliki 2 rantai karbon utama dan fungsional alkohol (-OH). IUPAC: Etanol, Trivial: Etil Alkohol."},
        {"str": "CH3 - CO - CH3", "kunci": ["propanon", "aseton"], "pembahasan": "Rantai 3 karbon jenuh dengan keton (=O) di bagian tengah. IUPAC: Propanon, Trivial: Aseton."},
        {"str": "CH3 - COOH", "kunci": ["asam asetat", "asam etanoat", "asam cuka"], "pembahasan": "Asam karboksilat berkarbon 2. Trivial: Asam asetat / asam cuka, IUPAC: Asam etanoat."},
        {"str": "CH2 = CH - CH3", "kunci": ["propena", "propilena"], "pembahasan": "Alkena dengan 3 atom karbon memiliki satu ikatan rangkap dua. IUPAC: Propena, Trivial: Propilena."},
        {"str": "CH3 - O - CH3", "kunci": ["dimetil eter", "metoksi metana"], "pembahasan": "Gugus eter (-O-) yang mengikat dua gugus metil di sisi kanan dan kiri. IUPAC: Metoksi metana, Trivial: Dimetil eter."},
        {"str": "CH3 - CH2 - CHO", "kunci": ["propanal", "propionaldehida"], "pembahasan": "Gugus aldehida (-CHO) di ujung rantai dengan total 3 atom karbon. IUPAC: Propanal, Trivial: Propionaldehida."},
        {"str": "CH ≡ C - CH3", "kunci": ["propuna", "metil asetilena"], "pembahasan": "Mengandung rantai karbon dengan ikatan rangkap tiga (alkuna). IUPAC: Propuna, Trivial: Metil asetilena."},
        {"str": "CH3 - CH2 - CH2 - Cl", "kunci": ["1-kloropropana", "propil klorida"], "pembahasan": "Haloalkana di mana atom klorin menggantikan hidrogen pada atom karbon nomor 1. IUPAC: 1-Kloropropana."},
        {"str": "CH3 - COO - CH2 - CH3", "kunci": ["etil etanoat", "etil asetat"], "pembahasan": "Senyawa ester. Rantai alkil pemutus adalah etil dan gugus utamanya asetat. Trivial: Etil asetat, IUPAC: Etil etanoat."},
        {"str": "CH3 - CH(OH) - CH3", "kunci": ["2-propanol", "isopropanol", "isopropil alkohol"], "pembahasan": "Alkohol sekunder di mana gugus hidroksil terikat di karbon nomor 2 dari total 3 rantai utama. IUPAC: 2-Propanol."}
    ]

    if 'id_soal' not in st.session_state:
        st.session_state.id_soal = 0

    idx = st.session_state.id_soal

    if idx < len(bank_soal):
        current = bank_soal[idx]
        st.info(f"### 📌 Soal Nomor {idx + 1} / {len(bank_soal)}")
        st.markdown(f"Tentukan nama senyawa dari rumus struktur berikut:\n## `` {current['str']} ``")
        
        user_ans = st.text_input("Jawaban Anda:", key=f"user_{idx}").strip().lower()
        
        if st.button("Kirim Jawaban"):
            if user_ans:
                is_correct = any(k in user_ans for k in current['kunci'])
                if is_correct:
                    st.success("🎉 **Luar Biasa, Benar!**")
                else:
                    st.error(f"❌ **Belum Tepat.** Jawaban benar: {', '.join([x.title() for x in current['kunci']])}")
                
                with st.expander("📖 Lihat Pembahasan Teori"):
                    st.write(current['pembahasan'])
            else:
                st.warning("Silakan tulis jawaban Anda terlebih dahulu.")
                
        st.markdown("---")
        if st.button("Lanjut ke Soal Berikutnya ➡️"):
            st.session_state.id_soal += 1
            st.rerun()
    else:
        st.balloons()
        st.success("🏆 **Selamat! Anda berhasil menyelesaikan seluruh 10 paket latihan soal tata nama organik.**")
        if st.button("Ulangi Dari Awal"):
            st.session_state.id_soal = 0
            st.rerun()
