import streamlit as st
from rdkit import Chem
from rdkit.Chem import AllChem
import py3Dmol
import streamlit.components.v1 as components

# ==============================================================================
# DATABASE MINI (Untuk Demo Sifat Fisika/Kimia & Reaksi)
# Karena konversi nama -> struktur -> sifat & reaksi secara realtime membutuhkan 
# API eksternal (seperti PubChem), kita gunakan dictionary terkurasi untuk demo ini.
# ==============================================================================
DATABASE_SENYAWA = {
    "etanol": {
        "smiles": "CCO",
        "iupac": "Etanol",
        "trivial": "Alkohol / Etil Alkohol",
        "fisika": "Cairan tidak berwarna, titik didih 78.37°C, mudah larut dalam air.",
        "kimia": "Mudah terbakar, dapat dioksidasi menjadi etanal lalu asam etanoat.",
        "reaksi": {
            "asam asetat": {
                "produk_smiles": "CCOC(=O)C",
                "produk_nama": "Etil Asetat (Ester)",
                "jenis": "Esterifikasi (Substitusi Nukleofilik)",
                "penjelasan": "Reaksi antara etanol dan asam asetat dengan katalis asam menghasilkan etil asetat dan air."
            }
        }
    },
    "asam asetat": {
        "smiles": "CC(=O)O",
        "iupac": "Asam Etanoat",
        "trivial": "Asam Asetat / Cuka",
        "fisika": "Cairan jernih, bau menyengat, titik didih 118°C.",
        "kimia": "Asam lemah, korosif pada konsentrasi tinggi.",
        "reaksi": {
            "etanol": {
                "produk_smiles": "CCOC(=O)C",
                "produk_nama": "Etil Asetat (Ester)",
                "jenis": "Esterifikasi",
                "penjelasan": "Asam asetat bereaksi dengan etanol membentuk senyawa ester beraroma buah (etil asetat)."
            }
        }
    }
}

SOAL_LATIHAN = [
    {"smiles": "CC(=O)C", "jawaban": ["propanon", "aseton"]},
    {"smiles": "CCO", "jawaban": ["etanol", "etil alkohol"]},
    {"smiles": "CCCC", "jawaban": ["butana", "n-butana"]}
]

# ==============================================================================
# FUNGSI HELPER (Visualisasi 3D menggunakan Py3Dmol)
# ==============================================================================
def render_3d(smiles):
    if not smiles:
        return None
    try:
        # Generate 3D Koordinat dari SMILES
        mol = Chem.MolFromSmiles(smiles)
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, AllChem.ETKDG())
        AllChem.MMFFOptimizeMolecule(mol)
        pdb_block = Chem.MolToPDBBlock(mol)
        
        # Py3Dmol viewer
        viewer = py3Dmol.view(width=400, height=300)
        viewer.addModel(pdb_block, 'pdb')
        viewer.setStyle({'stick': {}, 'sphere': {'scale': 0.3}})
        viewer.zoomTo()
        
        # Render ke HTML
        html = viewer._make_html()
        return html
    except:
        return "<p style='color:red;'>Gagal membuat struktur 3D.</p>"

# ==============================================================================
# INTERFACE STREAMLIT
# ==============================================================================
st.set_page_config(page_title="Tata Penamaan Senyawa Organik", layout="wide")

st.title("🧪 Tata Penamaan & Reaksi Senyawa Organik")
st.write("Aplikasi visualisasi molekul 3D, sifat fisik/kimia, prediksi reaksi, dan latihan soal.")

# Sidebar Menu Navigation
menu = st.sidebar.selectbox("Pilih Menu:", ["Eksplorasi & Reaksi", "Latihan Soal"])

# ------------------------------------------------------------------------------
# MENU 1: EKSPLORASI & REAKSI
# ------------------------------------------------------------------------------
if menu == "Eksplorasi & Reaksi":
    st.header("🔍 Identifikasi & Reaksi Senyawa")
    
    st.info("💡 **Tips Demo:** Coba masukkan **'etanol'** atau **'asam asetat'** (huruf kecil semua) untuk melihat fitur lengkap termasuk prediksi reaksi.")
    
    # Input Nama Senyawa
    nama_input = st.text_input("Masukkan Nama Senyawa Organik (IUPAC / Trivial):", "").lower().strip()
    
    if nama_input:
        # Cari di database lokal terlebih dahulu
        data_senyawa = DATABASE_SENYAWA.get(nama_input)
        
        # Jika tidak ada di DB, coba generate SMILES langsung via RDKit (Simulasi cerdas)
        smiles_target = None
        if data_senyawa:
            smiles_target = data_senyawa["smiles"]
            iupac_name = data_senyawa["iupac"]
            trivial_name = data_senyawa["trivial"]
            fisika = data_senyawa["fisika"]
            kimia = data_senyawa["kimia"]
        else:
            # Fallback: Menganggap input adalah SMILES valid jika tidak ada di DB
            try:
                test_mol = Chem.MolFromSmiles(nama_input)
                if test_mol:
                    smiles_target = nama_input
                    iupac_name = "Terdeteksi dari SMILES"
                    trivial_name = "-"
                    fisika = "Data tidak tersedia di database lokal."
                    kimia = "Data tidak tersedia di database lokal."
            except:
                smiles_target = None

        if smiles_target:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Structure Viewer (3D)")
                html_3d = render_3d(smiles_target)
                components.html(html_3d, height=300)
                
            with col2:
                st.subheader("Informasi Senyawa")
                st.markdown(f"**Nama IUPAC:** {iupac_name}")
                st.markdown(f"**Nama Trivial:** {trivial_name}")
                st.markdown(f"**Sifat Fisika:** {fisika}")
                st.markdown(f"**Sifat Kimia:** {kimia}")
            
            # --- FITUR OPSIONAL: REAKSI ---
            st.write("---")
            st.subheader("⚗️ Simulasikan Reaksi Kimia (Opsional)")
            reaktan_2 = st.text_input("Masukkan senyawa kedua untuk direaksikan:", "").lower().strip()
            
            if reaktan_2:
                # Cek apakah ada data reaksi di database kita
                if data_senyawa and "reaksi" in data_senyawa and reaktan_2 in data_senyawa["reaksi"]:
                    info_reaksi = data_senyawa["reaksi"][reaktan_2]
                    
                    st.success(f"**Reaksi Terdeteksi!** Jenis Reaksi: *{info_reaksi['jenis']}*")
                    
                    col_rx1, col_rx2 = st.columns(2)
                    with col_rx1:
                        st.write(f"**Struktur 3D Produk: {info_reaksi['produk_nama']}**")
                        html_produk = render_3d(info_reaksi["produk_smiles"])
                        components.html(html_produk, height=300)
                    
                    with col_rx2:
                        st.write("**Mekanisme & Penjelasan Reaksi:**")
                        st.info(info_reaksi["penjelasan"])
                        st.write("**Sifat Produk:**")
                        st.write("- Umumnya memiliki aroma/karakteristik baru dibanding reaktannya.")
                else:
                    st.warning("Maaf, reaksi untuk kombinasi senyawa ini belum tersedia di database lokal simulator.")
                    
        else:
            st.error("Senyawa tidak ditemukan di database atau format SMILES salah. Coba gunakan kata kunci 'etanol' atau 'asam asetat'.")

# ------------------------------------------------------------------------------
# MENU 2: LATIHAN SOAL
# ------------------------------------------------------------------------------
elif menu == "Latihan Soal":
    st.header("🧠 Latihan Soal: Tebak Nama Struktur")
    
    # Inisialisasi state untuk nomor soal agar tidak reset saat button diklik
    if 'nomor_soal' not in st.session_state:
        st.session_state.nomor_soal = 0
    if 'skor' not in st.session_state:
        st.session_state.skor = 0

    if st.session_state.nomor_soal < len(SOAL_LATIHAN):
        soal_aktif = SOAL_LATIHAN[st.session_state.nomor_soal]
        
        col_soal1, col_soal2 = st.columns([1, 1])
        
        with col_soal1:
            st.write(f"### Soal ke-{st.session_state.nomor_soal + 1}")
            st.write("Tebak nama IUPAC atau Trivial dari struktur 3D di samping!")
            
            # Form untuk menjawab
            jawaban_user = st.text_input("Jawaban Anda:", key=f"soal_{st.session_state.nomor_soal}").lower().strip()
            tombol_jawab = st.button("Kirim Jawaban")
            
            if tombol_jawab:
                if jawaban_user in soal_aktif["jawaban"]:
                    st.success("🎉 Benar sekali!")
                    st.session_state.skor += 1
                else:
                    st.error(f"❌ Salah! Jawaban yang benar bisa: {', '.join(soal_aktif['jawaban'])}")
                
                # Tambah delay/tombol untuk lanjut
                st.session_state.nomor_soal += 1
                st.button("Lanjut ke Soal Berikutnya")
                
        with col_soal2:
            # Tampilkan struktur soal
            html_soal = render_3d(soal_aktif["smiles"])
            components.html(html_soal, height=320)
            
    else:
        st.balloons()
        st.success(f"### Kuis Selesai! Skor Anda: {st.session_state.skor} / {len(SOAL_LATIHAN)}")
        if st.button("Ulangi Kuis"):
            st.session_state.nomor_soal = 0
            st.session_state.skor = 0
            st.rerun()
