import streamlit as st
import pubchempy as pcp
import py3Dmol
from stmol import showmol
from deep_translator import GoogleTranslator

# Mengatur konfigurasi halaman web
st.set_page_config(page_title="Visualizer Senyawa Organik", page_icon="🧪", layout="wide")

st.title("Pencari Sifat Senyawa & Visualizer 3D 🧪")
st.write("Masukkan nama senyawa organik (IUPAC atau Trivial) dalam Bahasa Indonesia atau Inggris.")

# Input Form
compound_input = st.text_input("Nama Senyawa:", "Asam asetat")

if st.button("Cari Senyawa"):
    with st.spinner("Mencari data ke database PubChem..."):
        try:
            # 1. Menerjemahkan input Bahasa Indonesia ke Bahasa Inggris
            # PubChem lebih optimal menggunakan query Bahasa Inggris
            translated_name = GoogleTranslator(source='auto', target='en').translate(compound_input)
            
            # 2. Mencari data senyawa di PubChem
            compounds = pcp.get_compounds(translated_name, 'name')
            
            if compounds:
                comp = compounds[0] # Ambil hasil pencarian pertama (paling relevan)
                
                st.success(f"Senyawa ditemukan: **{translated_name.capitalize()}** (Input: {compound_input})")
                st.divider()
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("Data Fisik & Kimiawi")
                    st.write(f"**Nama IUPAC:** {comp.iupac_name}")
                    st.write(f"**Rumus Molekul:** {comp.molecular_formula}")
                    st.write(f"**Berat Molekul:** {comp.molecular_weight} g/mol")
                    st.write(f"**SMILES:** {comp.canonical_smiles}")
                    
                    # Catatan tentang Titik Didih dan Reaktivitas
                    st.info(
                        "**Catatan Titik Didih & Reaktivitas:**\n"
                        "Data spesifik seperti titik didih (Boiling Point) dan reaktivitas di PubChem "
                        "berbentuk teks eksperimental dari berbagai sumber. API dasar hanya mengekstrak "
                        "properti komputasional. Untuk detail reaktivitas, biasanya dibutuhkan referensi "
                        "tabel periodik atau MSDS (Material Safety Data Sheet) senyawanya."
                    )
                
                with col2:
                    st.subheader("Visualisasi 3D (Model Molymod)")
                    # 3. Menyiapkan Viewer 3D menggunakan CID (Compound ID) dari PubChem
                    view = py3Dmol.view(width=500, height=400)
                    view.addModel(f"cid:{comp.cid}", "pubchem")
                    
                    # Gaya 'stick' dan 'sphere' membuat tampilan seperti Molymod
                    view.setStyle({'stick': {'radius': 0.15}, 'sphere': {'scale': 0.3}})
                    view.zoomTo()
                    
                    # Menampilkan di Streamlit
                    showmol(view, height=400, width=500)
                    
            else:
                st.error("Senyawa tidak ditemukan. Silakan cek ejaan atau gunakan nama alternatif.")
                
        except Exception as e:
            st.error(f"Terjadi kesalahan pada sistem: {e}")

st.divider()
st.caption("Ditenagai oleh Streamlit, PubChemPy, dan py3Dmol")
