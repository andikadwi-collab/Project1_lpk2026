import streamlit as st
import requests
import py3Dmol
import streamlit.components.v1 as components

# ==========================================
# FUNGSI BANTUAN (HELPER FUNCTIONS)
# ==========================================

def translate_id_to_en(nama_senyawa):
    """Translasi sederhana dari Trivial/IUPAC Indonesia ke Inggris untuk API PubChem"""
    kamus = {
        "etanol": "ethanol", "metanol": "methanol", "metana": "methane",
        "etana": "ethane", "propana": "propane", "butana": "butane",
        "asam asetat": "acetic acid", "asam cuka": "acetic acid",
        "aseton": "acetone", "benzena": "benzene", "fenol": "phenol"
    }
    return kamus.get(nama_senyawa.lower().strip(), nama_senyawa.lower().strip())

def get_pubchem_data(compound_name):
    """Mengambil data senyawa dari PubChem API"""
    base_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}"
    
    try:
        # Ambil properties dasar
        prop_url = f"{base_url}/property/MolecularFormula,MolecularWeight,IUPACName,XLogP/JSON"
        prop_res = requests.get(prop_url).json()
        
        if "PropertyTable" not in prop_res:
            return None
            
        properties = prop_res["PropertyTable"]["Properties"][0]
        cid = properties.get("CID", 1)
        
        # Ambil struktur 3D SDF
        sdf_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d"
        sdf_res = requests.get(sdf_url)
        sdf_data = sdf_res.text if sdf_res.status_code == 200 else None
        
        return {"properties": properties, "sdf": sdf_data}
    except Exception as e:
        return None

def show_3d_molecule(sdf_data):
    """Menampilkan model 3D seperti Molymod menggunakan py3Dmol"""
    if not sdf_data:
        st.warning("Struktur 3D tidak tersedia untuk senyawa ini.")
        return
        
    view = py3Dmol.view(width=500, height=400)
    view.addModel(sdf_data, 'sdf')
    view.setStyle({'sphere': {'scale': 0.3}, 'stick': {'radius': 0.2}}) # Gaya Molymod
    view.zoomTo()
    
    html = view._make_html()
    components.html(html, height=400)

def cek_reaksi(senyawa1, senyawa2):
    """
    Simulasi database reaksi kimia.
    Di dunia nyata, ini membutuhkan engine cheminformatics (misal: RDKit).
    """
    s1 = senyawa1.lower()
    s2 = senyawa2.lower()
    
    # Contoh Reaksi Esterifikasi
    if (s1 == "etanol" and s2 == "asam asetat") or (s1 == "asam asetat" and s2 == "etanol"):
        return {
            "hasil_nama": "Etil Asetat",
            "hasil_en": "ethyl acetate",
            "jenis_reaksi": "Reaksi Esterifikasi",
            "penjelasan": "Reaksi antara alkohol (etanol) dan asam karboksilat (asam asetat) menghasilkan ester (etil asetat) dan air (H2O). Reaksi ini bersifat dapat balik dan biasanya dikatalisis oleh asam pekat."
        }
    # Tambahkan kemungkinan reaksi lain di sini
    return None

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="Tata Penamaan Senyawa Organik", layout="wide")

# Navigasi Sidebar
menu = st.sidebar.selectbox("Pilih Menu", ["Visualisasi & Reaksi", "Latihan Soal"])

# ==========================================
# MENU 1: VISUALISASI & REAKSI
# ==========================================
if menu == "Visualisasi & Reaksi":
    st.title("🧪 Tata Penamaan Senyawa Organik")
    st.write("Masukkan nama senyawa organik (IUPAC/Trivial) untuk melihat struktur 3D dan sifatnya.")
    
    col1, col2 = st.columns(2)
    with col1:
        senyawa_utama = st.text_input("Nama Senyawa Utama (Wajib):", placeholder="Contoh: etanol")
    with col2:
        senyawa_opsional = st.text_input("Nama Senyawa Pereaksi (Opsional):", placeholder="Contoh: asam asetat")
        
    if st.button("Mulai", type="primary"):
        if senyawa_utama:
            nama_en = translate_id_to_en(senyawa_utama)
            data = get_pubchem_data(nama_en)
            
            if data:
                st.subheader(f"Senyawa: {senyawa_utama.title()}")
                
                # Layout hasil
                res_col1, res_col2 = st.columns([1, 1])
                with res_col1:
                    st.write("*Struktur 3D (Molymod):*")
                    show_3d_molecule(data['sdf'])
                
                with res_col2:
                    st.write("*Sifat Fisika & Kimia:*")
                    props = data['properties']
                    st.write(f"- *Rumus Molekul:* {props.get('MolecularFormula', 'N/A')}")
                    st.write(f"- *Berat Molekul:* {props.get('MolecularWeight', 'N/A')} g/mol")
                    st.write(f"- *Nama IUPAC:* {props.get('IUPACName', 'N/A')}")
                    st.write(f"- *XLogP (Sifat Lipofilik):* {props.get('XLogP', 'N/A')}")
                
                # Bagian Reaksi Opsional
                if senyawa_opsional:
                    st.divider()
                    st.subheader("⚡ Hasil Reaksi")
                    reaksi_info = cek_reaksi(senyawa_utama, senyawa_opsional)
                    
                    if reaksi_info:
                        st.success(f"*{reaksi_info['jenis_reaksi']}* terjadi!")
                        st.write(reaksi_info['penjelasan'])
                        
                        data_hasil = get_pubchem_data(reaksi_info['hasil_en'])
                        if data_hasil:
                            hasil_col1, hasil_col2 = st.columns(2)
                            with hasil_col1:
                                st.write(f"*Struktur 3D: {reaksi_info['hasil_nama']}*")
                                show_3d_molecule(data_hasil['sdf'])
                            with hasil_col2:
                                st.write("*Sifat Produk:*")
                                h_props = data_hasil['properties']
                                st.write(f"- *Rumus Molekul:* {h_props.get('MolecularFormula', 'N/A')}")
                                st.write(f"- *Nama IUPAC:* {h_props.get('IUPACName', 'N/A')}")
                    else:
                        st.warning("Reaksi antara dua senyawa tersebut belum ada di database lokal kami atau secara teori tidak bereaksi secara langsung pada kondisi standar.")
            else:
                st.error("Senyawa tidak ditemukan. Pastikan ejaan benar atau gunakan nama IUPAC bahasa Inggris/Indonesia yang baku.")
        else:
            st.warning("Harap masukkan nama senyawa utama terlebih dahulu.")

# ==========================================
# MENU 2: LATIHAN SOAL
# ==========================================
elif menu == "Latihan Soal":
    st.title("📝 Latihan Tata Penamaan")
    st.write("Tebak nama IUPAC atau Trivial (Indonesia) dari rumus struktur berikut.")
    
    # Database Soal Sederhana
    soal_list = [
        {
            "struktur": "CH3 - CH2 - OH",
            "jawaban_valid": ["etanol", "etil alkohol", "ethanol"],
            "pembahasan": "Senyawa ini memiliki dua atom karbon (et-) dan gugus fungsi alkohol (-OH). Oleh karena itu, nama IUPAC-nya adalah Etanol, atau nama trivialnya Etil Alkohol."
        },
        {
            "struktur": "CH3 - CO - CH3",
            "jawaban_valid": ["propanon", "aseton", "dimetil keton"],
            "pembahasan": "Senyawa ini memiliki tiga atom karbon (prop-) dengan gugus fungsi keton (-CO-) di tengah. Nama IUPAC-nya adalah Propanon, dikenal luas dengan nama trivial Aseton."
        },
        {
            "struktur": "CH3 - CH2 - CH2 - CH3",
            "jawaban_valid": ["butana", "n-butana"],
            "pembahasan": "Rantai lurus alkana dengan 4 atom karbon. Diberi awalan but- dan akhiran -ana. Nama IUPAC-nya adalah Butana."
        }
    ]
    
    # Inisialisasi Session State untuk indeks soal
    if 'nomor_soal' not in st.session_state:
        st.session_state.nomor_soal = 0

    soal_sekarang = soal_list[st.session_state.nomor_soal]
    
    st.subheader(f"Soal {st.session_state.nomor_soal + 1}")
    st.info(f"*Rumus Struktur:*\n\n### {soal_sekarang['struktur']}")
    
    jawaban_user = st.text_input("Masukkan Nama Senyawa (IUPAC/Trivial):", key=f"input_{st.session_state.nomor_soal}")
    
    if st.button("Cek Jawaban"):
        if jawaban_user:
            if jawaban_user.lower().strip() in soal_sekarang['jawaban_valid']:
                st.success("🎉 BENAR!")
            else:
                st.error("❌ SALAH.")
                
            st.write("*Pembahasan:*")
            st.write(soal_sekarang['pembahasan'])
            
            # Tombol ke soal berikutnya
            if st.session_state.nomor_soal < len(soal_list) - 1:
                if st.button("Soal Selanjutnya"):
                    st.session_state.nomor_soal += 1
                    st.rerun()
            else:
                st.write("🌟 *Anda telah menyelesaikan semua soal!*")
                if st.button("Ulangi Latihan"):
                    st.session_state.nomor_soal = 0
                    st.rerun()
        else:
            st.warning("Tulis jawaban Anda terlebih dahulu.")
