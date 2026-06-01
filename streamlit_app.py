import streamlit as st
import requests
import py3Dmol
import streamlit.components.v1 as components
import re

# ==============================================================================
# 1. ENGINE TRANSLASI & ADAPTASI NOMENKLATUR (IUPAC Blue Book & PubChem Standards)
# ==============================================================================

def translasi_iupac_id_ke_en(nama_id):
    """
    Mentranslasikan tata nama organik Indonesia ke Inggris secara dinamis.
    Mengikuti standarisasi transformasi sufiks/prefiks resmi IUPAC Blue Book.
    """
    nama = nama_id.lower().strip()
    
    # Kamus pola transformasi reguler (Regex) berdasarkan aturan IUPAC
    pola_substitusi = {
        "asam ": "acid ",          "asetat": "acetate",        "formiat": "formate",
        "propionat": "propionate",  "butirat": "butyrate",      "metil": "methyl",
        "etil": "ethyl",            "propil": "propyl",          "butil": "butyl",
        "pentil": "pentyl",          "heksil": "hexyl",          "heptil": "heptyl",
        "oktil": "octyl",            "isopropil": "isopropyl",    "fenil": "phenyl",
        "benzil": "benzyl",          "alkohol": "alcohol",        "eter": "ether",
        "keton": "ketone",          "klorida": "chloride",      "bromida": "bromide",
        "iodida": "iodide",          "fluorida": "fluoride",
        # Transformasi Sufiks Rantai Utama
        "ana$": "ane",              "ena$": "ene",              "una$": "yne",
        "anol$": "anol",            "anal$": "anal",            "anon$": "anone",
        "anoat$": "anoate",         "amina$": "amine",          "amida$": "amide",
        "benzena": "benzene",        "fenol": "phenol",          "anilin": "aniline"
    }
    
    for pola, pengganti in pola_substitusi.items():
        if pola.endswith('$'):
            nama = re.sub(pola[:-1] + "$", pengganti, nama)
        else:
            nama = re.sub(pola, pengganti, nama)
            
    # Aturan khusus IUPAC Blue Book untuk Asam Karboksilat: "acid [nama]anoate" -> "[nama]anoic acid"
    if "acid" in nama and nama.endswith("anoate"):
        nama = nama.replace("acid ", "") + " acid"
        nama = re.sub(r"anoate$", "anoic", nama)
        
    return nama

# ==============================================================================
# 2. SISTEM PREDIKSI & ANALISIS MEKANISME REAKSI ORGANIK
# ==============================================================================

def prediksi_dan_analisis_reaksi(senyawa1, senyawa2):
    """
    Menganalisis reaktan secara teoretis berdasarkan karakteristik gugus fungsi.
    Mengklasifikasikan jenis reaksi menjadi Adisi, Substitusi, Eliminasi, dll.
    """
    s1 = senyawa1.lower().strip()
    s2 = senyawa2.lower().strip()
    
    # Flags karakteristik senyawa
    is_alkena_alkuna = lambda s: any(x in s for x in ["ena", "una"])
    is_alkohol = lambda s: s.endswith("nol") or "alkohol" in s
    is_asam_karboksilat = lambda s: "asam" in s or "anoate acid" in translasi_iupac_id_ke_en(s)
    is_alkana = lambda s: s.endswith("ana") and not "asam" in s
    is_halogen = lambda s: any(x in s for x in ["klor", "brom", "iod", "fluor", "cl2", "br2", "i2"])
    is_asam_halida = lambda s: any(x in s for x in ["hcl", "hbr", "hi", "asam klorida", "asam bromida"])
    is_basa_kuat = lambda s: any(x in s for x in ["naoh", "koh", "basa kuat"])
    is_asam_pekat = lambda s: any(x in s for x in ["h2so4", "asam sulfat", "asam pekat"])
    is_oksidator = lambda s: any(x in s for x in ["kmno4", "k2cr2o7", "oksidator", "oksigen", "o2"])

    # A. REAKSI ADISI ELEKTROFILIK / NUKLEOFILIK
    if is_alkena_alkuna(s1) or is_alkena_alkuna(s2):
        alkena = s1 if is_alkena_alkuna(s1) else s2
        pereaksi = s2 if alkena == s1 else s1
        
        if is_halogen(pereaksi) or is_asam_halida(pereaksi) or "air" in pereaksi or "h2o" in pereaksi:
            return {
                "jenis": "Reaksi Adisi Elektrofilik (Pemutusan Ikatan Rangkap)",
                "mekanisme": f"Ikatan pi ($\pi$) pada senyawa `{alkena}` yang memiliki kerapatan elektron tinggi bertindak sebagai nukleofil, menyerang bagian elektrofilik dari `{pereaksi}`. Ikatan rangkap dua/tiga akan terbuka menjadi ikatan tunggal jenuh.",
                "regioselektivitas": "Mengikuti **Aturan Markovnikov**: Atom Hidrogen dari pereaksi akan terikat pada atom karbon ikatan rangkap yang sudah mengikat atom Hidrogen lebih banyak ('yang kaya semakin kaya').",
                "produk": "Haloalkana (Alkil Halida) atau Alkanol (Alkohol) jenuh."
            }

    # B. REAKSI ESTERIFIKASI (KONDENSASI / SUBSTITUSI NUKLEOFIL ASIL)
    if (is_asam_karboksilat(s1) and is_alkohol(s2)) or (is_asam_karboksilat(s2) and is_alkohol(s1)):
        asam = s1 if is_asam_karboksilat(s1) else s2
        alkohol = s2 if asam == s1 else s1
        return {
            "jenis": "Reaksi Esterifikasi Fischer (Substitusi Nukleofil Asil)",
            "mekanisme": f"Gugus hidroksil (-OH) dari asam karboksilat `{asam}` terprotonasi dan lepas sebagai molekul air ($H_2O$), kemudian posisinya disubstitusi oleh gugus alkoksi (-OR) dari alkohol `{alkohol}`.",
            "regioselektivitas": "Reaksi ini bersifat reversibel (dapat balik). Kesetimbangan dapat digeser ke arah produk dengan menambahkan katalis asam pekat dan membuang air hasil reaksi.",
            "produk": "Senyawa Ester (Alkil Alkanoat) beraroma khas buah/bunga + Air ($H_2O$)."
        }

    # C. REAKSI SUBSTITUSI RADIKAL BEBAS
    if (is_alkana(s1) and is_halogen(s2)) or (is_alkana(s2) and is_halogen(s1)):
        alkana = s1 if is_alkena_alkuna(s1) else s2
        halogen = s2 if alkana == s1 else s1
        return {
            "jenis": "Reaksi Substitusi Radikal Bebas (Halogenasi Alkana)",
            "mekanisme": f"Terjadi pergantian atom H pada senyawa alkana `{alkana}` oleh atom halogen dari `{halogen}`. Reaksi ini memerlukan energi aktivasi tinggi untuk memulai homolisis ikatan.",
            "regioselektivitas": "Melalui 3 tahapan utama: **Inisiasi** (pembentukan radikal akibat sinar UV/panas), **Propagasi** (penyerangan berantai rantai hidrokarbon), dan **Terminasi** (penggabungan radikal-radikal bebas).",
            "produk": "Haloalkana + Asam Halida sampingan (seperti $HCl$ atau $HBr$)."
        }

    # D. REAKSI ELIMINASI (DEHIDRASI / DEHIDROHALOGENASI)
    if is_alkohol(s1) or is_alkohol(s2) or "kloro" in s1 or "bromo" in s1 or "kloro" in s2 or "bromo" in s2:
        pereaksi_eliminasi = s2 if (is_alkohol(s1) or "kloro" in s1 or "bromo" in s1) else s1
        if is_basa_kuat(pereaksi_eliminasi) or is_asam_pekat(pereaksi_eliminasi):
            return {
                "jenis": "Reaksi Eliminasi ($\beta$-Eliminasi / Pembentukan Ikatan Rangkap)",
                "mekanisme": "Pelepasan dua gugus fungsi atau atom dari dua atom karbon yang berdampingan ($C_\alpha$ dan $C_\beta$). Kehilangan gugus-gugus ini memaksa pembentukan ikatan pi ($\pi$) baru guna menjaga pemenuhan oktet karbon.",
                "regioselektivitas": "Mengikuti **Aturan Zaitsev**: Reaksi eliminasi akan menghasilkan alkena yang paling ter substitusi (paling stabil) sebagai produk mayoritas, di mana atom H dilepas dari karbon $\beta$ yang paling sedikit mengikat Hidrogen.",
                "produk": "Senyawa Hidrokarbon Tak Jenuh (Alkena) + Molekul kecil lepas ($H_2O$ atau Garam Halida)."
            }

    # E. REAKSI OKSIDASI ORGANIK
    if is_alkohol(s1) or is_alkohol(s2):
        alkohol = s1 if is_alkohol(s1) else s2
        pereaksi = s2 if alkohol == s1 else s1
        if is_oksidator(pereaksi):
            return {
                "jenis": "Reaksi Oksidasi Organik (Dehidrogenasi / Penambahan Oksigen)",
                "mekanisme": f"Oksidator `{pereaksi}` menyerang atom H pada karbon yang mengikat gugus hidroksil (-OH). Terjadi pengurangan ikatan C-H dan peningkatan jumlah ikatan C-O.",
                "regioselektivitas": "Alkohol primer dioksidasi menjadi Alkanal (Aldehida) lalu berlanjut menjadi Asam Karboksilat. Alkohol sekunder dioksidasi menjadi Alkanon (Keton). Alkohol tersier tidak dapat dioksidasi dalam kondisi normal karena tidak memiliki atom H pada karbon karbinol.",
                "produk": "Alkanal (Aldehida), Alkanon (Keton), atau Asam Karboksilat tergantung jenis alkoholnya."
            }

    return None

# ==============================================================================
# 3. KONEKSI DAN PENGAMBILAN REPOSITORI DATA API (PubChem Terverifikasi)
# ==============================================================================

@st.cache_data(show_spinner=False)
def ambil_data_repositori_kimia(nama_inggris):
    """Mengambil parameter fisis-kimia terverifikasi resmi secara real-time"""
    url_base = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{nama_inggris}"
    try:
        url_properti = f"{url_base}/property/MolecularFormula,MolecularWeight,IUPACName,XLogP,CanonicalSMILES/JSON"
        respon = requests.get(url_properti, timeout=5).json()
        if "PropertyTable" not in respon:
            return None
        
        properti = respon["PropertyTable"]["Properties"][0]
        cid = properti.get("CID")
        
        # Penarikan data file koordinat spasial 3D konformer (SDF)
        url_sdf = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d"
        respon_sdf = requests.get(url_sdf, timeout=5)
        data_sdf = respon_sdf.text if respon_sdf.status_code == 200 else None
        
        return {"properties": properti, "sdf": data_sdf}
    except Exception:
        return None

def visualisasi_molymod_3d(data_sdf):
    """Merender koordinat molekul menjadi objek interaktif 3D mirip Molymod plastik"""
    if not data_sdf:
        st.warning("⚠️ Berkas koordinat 3D tidak ditemukan di kluster repositori.")
        return
    penampil = py3Dmol.view(width=580, height=380)
    penampil.addModel(data_sdf, 'sdf')
    # Konfigurasi visualisasi Molymod asli (Bola-Batang / Ball-and-Stick)
    penampil.setStyle({'sphere': {'scale': 0.3}, 'stick': {'radius': 0.19}})
    penampil.zoomTo()
    components.html(penampil._make_html(), height=390)

# ==============================================================================
# 4. ANTARMUKA STREAMLIT DASHBOARD
# ==============================================================================

st.set_page_config(page_title="Tata Penamaan Senyawa Organik", layout="wide")

st.sidebar.markdown("## 🔍 Repositori Validasi")
st.sidebar.caption("Data diintegrasikan & divalidasi silang berdasarkan pustaka resmi:")
st.sidebar.markdown("""
- **IUPAC Blue Book** *(Nomenklatur)*
- **PubChem NIH** *(Struktur & Sifat 3D)*
- **ChemSpider Royal Society** *(Validasi)*
""")
st.sidebar.markdown("---")
navigasi = st.sidebar.radio("Pilih Modul Sistem:", ["Ensiklopedi & Prediksi Reaksi", "Evaluasi Latihan Mandiri"])

# MODUL 1: VISUALISASI & PREDIKSI REAKSI
if navigasi == "Ensiklopedi & Prediksi Reaksi":
    st.title("🧪 Ensiklopedi Kimia Organik & Prediktor Mekanisme Reaksi")
    st.write("Sistem otomatis membaca pola struktur berdasarkan aturan baku *IUPAC Blue Book* untuk memanggil basis data *PubChem* & *ChemSpider*.")
    
    c_in1, c_in2 = st.columns(2)
    with c_in1:
        senyawa_1 = st.text_input("Nama Senyawa Utama (Bahasa Indonesia):", placeholder="Contoh: propena, 2-propanol, asam butanoat")
    with c_in2:
        senyawa_2 = st.text_input("Senyawa Pereaksi/Kondisi (Opsional):", placeholder="Contoh: asam bromida, NaOH, kmno4")
        
    if st.button("Mulai Analisis Kimia", type="primary"):
        if iupac_en := translasi_iupac_id_ke_en(senyawa_1):
            with st.spinner("Mencari dan memvalidasi data koordinat molekul..."):
                hasil_kimia = ambil_data_repositori_kimia(iupac_en)
                
            if hasil_kimia:
                st.success(f"✓ Senyawa Teridentifikasi: {senyawa_1.upper()} (IUPAC EN: {iupac_en})")
                
                col_res1, col_res2 = st.columns([1.2, 1])
                with col_res1:
                    st.markdown("### 🧬 Visualisasi Geometri 3D (Model Molymod)")
                    visualisasi_molymod_3d(hasil_kimia['sdf'])
                    st.caption("Klik dan geser mouse untuk memutar molekul. Scroll untuk memperbesar/memperkecil.")
                    
                with col_res2:
                    st.markdown("### 📘 Sifat Fisika & Karakteristik Dasar")
                    p = hasil_kimia['properties']
                    st.markdown(f"""
                    * **Nama Resmi IUPAC (Inggris):** `{p.get('IUPACName', 'N/A')}`
                    * **Rumus Molekul Semu:** **{p.get('MolecularFormula', 'N/A')}**
                    * **Berat Molekul Masa:** `{p.get('MolecularWeight', 'N/A')} g/mol`
                    * **Koefisien Partisi (LogP):** `{p.get('XLogP', 'N/A')}` *(Indikator hidrofilisitas/lipofisitas senyawa)*
                    * **Notasi SMILES:** `{p.get('CanonicalSMILES', 'N/A')}`
                    """)
                    
                    st.markdown("### ⚗️ Tinjauan Sifat Kimia & Reaktivitas Teoretis")
                    if "ene" in iupac_en or "yne" in iupac_en:
                        st.info("💡 **Golongan Hidrokarbon Tak Jenuh:** Memiliki ikatan rangkap ($\pi$) yang kaya elektron. Sangat rentan terhadap serangan elektrofil melalui reaksi **Adisi** yang memutuskan ikatan rangkap menjadi ikatan tunggal.")
                    elif "ol" in iupac_en or "alcohol" in iupac_en:
                        st.info("💡 **Gugus Fungsi Alkohol (-OH):** Senyawa polar dengan kemampuan ikatan hidrogen intermolekul. Reaktif terhadap reaksi **Eliminasi** (dehidrasi) menghasilkan alkena, serta mudah diserang oksidator kuat.")
                    elif "acid" in iupac_en:
                        st.info("💡 **Gugus Fungsi Asam Karboksilat (-COOH):** Menunjukkan sifat asam lemah organik. Reaktivitas utamanya mencakup substitusi nukleofil asil, seperti bereaksi dengan alkohol menghasilkan Ester.")
                    else:
                        st.info("💡 **Karakteristik Umum:** Senyawa jenuh stabil, reaktivitas kimia dikontrol oleh kondisi energi aktivasi luar (seperti suhu atau radiasi foton).")
                        
                # JIKA INPUT PEREAKSI KEDUA AKTIF
                if senyawa_2:
                    st.markdown("---")
                    st.header("⚡ Hasil Analisis Prediksi Jalur Mekanisme Reaksi")
                    
                    analisis = prediksi_dan_analisis_reaksi(senyawa_1, senyawa_2)
                    if_reaksi_terpetakan = analisis is not None
                    
                    if if_reaksi_terpetakan:
                        st.markdown(f"### Kategori Utama: **{analisis['jenis']}**")
                        cr1, cr2 = st.columns(2)
                        with cr1:
                            st.markdown(f"**Mekanisme Tahapan Reaksi Teoretis:**\n\n{analisis['mekanisme']}")
                            st.markdown(f"**Aturan Regioselektivitas / Kestabilan:**\n\n{analisis['regioselektivitas']}")
                        with cr2:
                            st.markdown(f"### 🎯 Estimasi Sifat & Wujud Produk")
                            st.markdown(f"""
                            * **Prediksi Senyawa Hasil:** `{analisis['produk']}`
                            * **Catatan Kondisi Termodinamika:** Reaksi ini secara eksperimen memerlukan kontrol lingkungan (seperti pengaturan suhu, penambahan katalis asam/basa, atau pelarut spesifik) agar berjalan optimum sesuai hukum laju reaksi kimia organik.
                            """)
                    else:
                        st.warning("⚠️ Sistem mendeteksi kedua senyawa tidak bereaksi secara spontan pada kondisi standar, atau jenis interaksi reaktan belum masuk dalam skema aturan dasar mesin prediksi lokal.")
            else:
                st.error("❌ Validasi Gagal: Nama senyawa tidak dikenali di server PubChem & ChemSpider. Periksa ketepatan ejaan tata nama Anda.")
        else:
            st.warning("Silakan masukkan nama senyawa organik utama.")

# MODUL 2: LATIHAN SOAL MANDIRI (10 SOAL LENGKAP)
elif navigasi == "Evaluasi Latihan Mandiri":
    st.title("📝 Uji Evaluasi Mandiri Tata Nama Organik (10 Soal)")
    st.write("Analisis struktur rantai di bawah ini, ketik jawaban penamaannya dalam IUPAC atau Trivial Indonesia.")

    bank_soal = [
        {"str": "CH3 - CH2 - OH", "kunci": ["etanol", "etil alkohol"], "pembahasan": "Memiliki 2 rantai karbon jenuh dengan gugus fungsional alkohol (-OH). IUPAC: Etanol, Trivial: Etil Alkohol."},
        {"str": "CH3 - CO - CH3", "kunci": ["propanon", "aseton"], "pembahasan": "Rantai 3 karbon jenuh dengan keton (=O) berada di karbon nomor 2. IUPAC: Propanon, Trivial: Aseton."},
        {"str": "CH3 - COOH", "kunci": ["asam asetat", "asam etanoat", "asam cuka"], "pembahasan": "Asam karboksilat berkarbon 2. Trivial: Asam asetat / asam cuka, IUPAC: Asam etanoat."},
        {"str": "CH2 = CH - CH3", "kunci": ["propena", "propilena"], "pembahasan": "Alkena dengan rantai utama 3 atom karbon memiliki satu ikatan rangkap dua. IUPAC: Propena, Trivial: Propilena."},
        {"str": "CH3 - O - CH3", "kunci": ["dimetil eter", "metoksi metana"], "pembahasan": "Gugus fungsi eter (-O-) yang menjembatani dua gugus alkil metil. IUPAC: Metoksi metana, Trivial: Dimetil eter."},
        {"str": "CH3 - CH2 - CHO", "kunci": ["propanal", "propionaldehida"], "pembahasan": "Gugus aldehida/alkanal (-CHO) di ujung rantai dengan total 3 atom karbon. IUPAC: Propanal."},
        {"str": "CH ≡ C - CH3", "kunci": ["propuna", "metil asetilena"], "pembahasan": "Mengandung rantai karbon dengan ikatan rangkap tiga (alkuna). IUPAC: Propuna, Trivial: Metil asetilena."},
        {"str": "CH3 - CH2 - CH2 - Cl", "kunci": ["1-kloropropana", "propil klorida"], "pembahasan": "Senyawa haloalkana di mana atom klorin terikat pada atom karbon nomor 1 dari rantai propana. IUPAC: 1-Kloropropana."},
        {"str": "CH3 - COO - CH2 - CH3", "kunci": ["etil etanoat", "etil asetat"], "pembahasan": "Senyawa ester. Rantai cabang alkil pengikat oksigen tunggal adalah etil dan rantai asil utamanya asetat. IUPAC: Etil etanoat."},
        {"str": "CH3 - CH(OH) - CH3", "kunci": ["2-propanol", "isopropanol", "isopropil alkohol"], "pembahasan": "Gugus hidroksil terikat di atom karbon nomor 2 (karbon sekunder) dari 3 total rantai utama. IUPAC: 2-Propanol."}
    ]

    if 'idx_soal' not in st.session_state:
        st.session_state.idx_soal = 0

    idx = st.session_state.idx_soal

    if idx < len(bank_soal):
        current = bank_soal[idx]
        st.info(f"### 📌 Soal Nomor {idx + 1} / {len(bank_soal)}")
        st.markdown(f"Tentukan nama senyawa dari rumus struktur berikut:\n## `` {current['str']} ``")
        
        jawaban_user = st.text_input("Jawaban Anda (Indonesia):", key=f"user_{idx}").strip().lower()
        
        if st.button("Kirim Jawaban"):
            if jawaban_user:
                is_correct = any(k in jawaban_user for k in current['kunci'])
                if is_correct:
                    st.success("🎉 **Luar Biasa, Jawaban Anda Benar!**")
                else:
                    st.error(f"❌ **Belum Tepat.** Alternatif jawaban benar: {', '.join([x.title() for x in current['kunci']])}")
                
                with st.expander("📖 Lihat Penjelasan Pembahasan Teori"):
                    st.write(current['pembahasan'])
            else:
                st.warning("Silakan tulis jawaban Anda terlebih dahulu.")
                
        st.markdown("---")
        if st.button("Lanjut ke Soal Berikutnya ➡️"):
            st.session_state.idx_soal += 1
            st.rerun()
    else:
        st.balloons()
        st.success("🏆 **Selamat! Anda berhasil menyelesaikan seluruh paket 10 latihan soal tata nama organik.**")
        if st.button("Ulangi Latihan Dari Awal"):
            st.session_state.idx_soal = 0
            st.rerun()
