import streamlit as st
import pubchempy as pcp
from rdkit import Chem
from rdkit.Chem import Draw, AllChem, Descriptors
from rdkit.Chem.Draw import IPythonConsole
import py3Dmol
import pandas as pd
import requests
from io import BytesIO
import base64
import time
import random

# ========== KONFIGURASI HALAMAN ==========
st.set_page_config(page_title="Tata Nama & Latihan Senyawa Organik", layout="wide")

# ========== SESSION STATE ==========
if "page" not in st.session_state:
    st.session_state.page = "cover"
if "soal_batch" not in st.session_state:
    st.session_state.soal_batch = 0
if "soal_index" not in st.session_state:
    st.session_state.soal_index = 0
if "soal_list" not in st.session_state:
    st.session_state.soal_list = []
if "feedback" not in st.session_state:
    st.session_state.feedback = None
if "reaction_smiles" not in st.session_state:
    st.session_state.reaction_smiles = None

# ========== FUNGSI BANTU ==========

def search_compound(name):
    """Cari senyawa berdasarkan nama trivial/IUPAC di PubChem."""
    try:
        compounds = pcp.get_compounds(name, 'name')
        if compounds:
            return compounds[0]  # ambil pertama
        else:
            return None
    except Exception as e:
        st.error(f"Gagal mencari senyawa: {e}")
        return None

def get_compound_info(cid):
    """Ambil properti penting dari PubChem menggunakan CID."""
    try:
        props = pcp.Compound.from_cid(cid)
        weight = props.molecular_weight
        bp = props.boiling_point
        iupac = props.iupac_name
        # deskripsi umum tidak selalu tersedia, ambil dari record
        description = "Tidak tersedia"
        if props.synonyms:
            description = f"Nama lain: {', '.join(props.synonyms[:3])}"
        return {
            "iupac": iupac,
            "weight": weight,
            "bp": bp if bp else "Tidak diketahui",
            "desc": description
        }
    except:
        return {"iupac": "?", "weight": "?", "bp": "?", "desc": "?"}

def draw_3d(smiles):
    """Tampilkan struktur 3D interaktif menggunakan py3Dmol."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, randomSeed=42)
    AllChem.MMFFOptimizeMolecule(mol)
    conf = mol.GetConformer()
    xyz = []
    for atom in mol.GetAtoms():
        pos = conf.GetAtomPosition(atom.GetIdx())
        xyz.append(f"{atom.GetSymbol()} {pos.x:.4f} {pos.y:.4f} {pos.z:.4f}")
    xyz_str = "\n".join(xyz)
    view = py3Dmol.view(width=500, height=400)
    view.addModel(xyz_str, "xyz")
    view.setStyle({"stick": {}, "sphere": {"radius": 0.4}})
    view.zoomTo()
    view.spin()
    return view

def draw_2d(smiles):
    """Gambar struktur 2D sebagai gambar PNG."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    img = Draw.MolToImage(mol, size=(400, 200))
    return img

def reaction_possible(rxn_smarts, smi1, smi2=None):
    """Cek dan jalankan reaksi kimia menggunakan SMARTS. Kembalikan produk utama (SMILES)."""
    rxn = AllChem.ReactionFromSmarts(rxn_smarts)
    mol1 = Chem.MolFromSmiles(smi1)
    if smi2:
        mol2 = Chem.MolFromSmiles(smi2)
        if mol2 is None:
            return None, "Senyawa kedua tidak valid."
        products = rxn.RunReactants((mol1, mol2))
    else:
        products = rxn.RunReactants((mol1,))
    if not products:
        return None, "Reaksi tidak dapat terjadi dengan reaktan tersebut."
    # Ambil produk pertama (molekul target, abaikan produk samping seperti air)
    main_product = products[0][0]
    try:
        Chem.SanitizeMol(main_product)
        smi_prod = Chem.MolToSmiles(main_product)
        return smi_prod, None
    except:
        return None, "Produk reaksi tidak stabil atau tidak valid."

# ========== HALAMAN COVER ==========
def cover():
    st.markdown("""
    <style>
    .cover-box {
        background-color: #f0f2f6;
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        margin-top: 50px;
    }
    .member-list {
        font-size: 18px;
        line-height: 2.2;
    }
    </style>
    """, unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='cover-box'>", unsafe_allow_html=True)
        st.image("https://img.icons8.com/color/96/chemistry.png", width=80)  # ikon kimia
        st.title("🧪 Aplikasi Pembelajaran Kimia Organik")
        st.subheader("Tata Penamaan Senyawa & Latihan Soal")
        st.markdown("---")
        st.markdown("### 👥 Anggota Kelompok:")
        members = [
            "ANDIKA DWI PRASHOJO",
            "JAWAHER SABRINA A",
            "NAELY LUTHFIYAH ARIF",
            "SALWA AZKA SABANA",
            "ALEX KUSUMAH"
        ]
        for m in members:
            st.markdown(f"🔹 {m}")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("Pilih menu:", ["Tata Penamaan Senyawa", "Latihan Soal"], horizontal=True)
        if st.button("Masuk", type="primary", use_container_width=True):
            if menu == "Tata Penamaan Senyawa":
                st.session_state.page = "tata_penamaan"
            else:
                st.session_state.page = "latihan_soal"
                # reset batch soal
                st.session_state.soal_batch = 0
                st.session_state.soal_index = 0
                st.session_state.soal_list = []
                st.session_state.feedback = None
            st.rerun()

# ========== HALAMAN TATA PENAMAAN ==========
def tata_penamaan():
    st.title("🧬 Tata Penamaan Senyawa Organik")
    st.markdown("Masukkan nama senyawa (IUPAC atau trivial, dalam Bahasa Indonesia/Inggris) dan dapatkan struktur 3D, data properti, serta simulasi reaksinya.")
    nama = st.text_input("Nama senyawa:", placeholder="contoh: asam asetat, ethanol, metana, benzena ...")
    if st.button("🔍 Mulai Analisis", type="primary"):
        if not nama.strip():
            st.warning("Masukkan nama senyawa terlebih dahulu.")
        else:
            with st.spinner("Mencari senyawa di PubChem..."):
                compound = search_compound(nama.strip())
            if compound is None:
                st.error("Senyawa tidak ditemukan di database PubChem.")
                return
            # Simpan data di session
            st.session_state.compound = compound
            st.session_state.info = get_compound_info(compound.cid)
            st.session_state.smiles = compound.canonical_smiles
            st.session_state.reaction_smiles = None  # reset hasil reaksi
            st.rerun()

    if "compound" in st.session_state:
        compound = st.session_state.compound
        info = st.session_state.info
        smiles = st.session_state.smiles
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Struktur 3D (interaktif)")
            view = draw_3d(smiles)
            if view:
                view.show()
            else:
                st.warning("Gagal membuat visual 3D.")
        with col2:
            st.subheader("Informasi Senyawa")
            st.markdown(f"**Nama IUPAC:** {info['iupac']}")
            st.markdown(f"**Berat Molekul:** {info['weight']} g/mol")
            st.markdown(f"**Titik Didih:** {info['bp']} °C")
            st.markdown(f"**Deskripsi:** {info['desc']}")
            # Reaktivitas singkat
            mol = Chem.MolFromSmiles(smiles)
            functional_groups = []
            if mol.HasSubstructMatch(Chem.MolFromSmarts("[CX3](=O)[OX2H1]")): functional_groups.append("asam karboksilat")
            if mol.HasSubstructMatch(Chem.MolFromSmarts("[OX2H]")): functional_groups.append("alkohol/fenol")
            if mol.HasSubstructMatch(Chem.MolFromSmarts("[NX3H2]")): functional_groups.append("amina primer")
            if mol.HasSubstructMatch(Chem.MolFromSmarts("[CX3]=[CX3]")): functional_groups.append("alkena")
            st.markdown(f"**Gugus fungsi terdeteksi:** {', '.join(functional_groups) if functional_groups else 'tidak spesifik'}")

        # Bagian reaksi opsional
        st.markdown("---")
        st.subheader("⚗️ Simulasi Reaksi (Opsional)")
        reaktan2 = st.text_input("Masukkan senyawa kedua (nama):", key="react2")
        # Pilihan tipe reaksi yang tersedia
        tipe_reaksi = st.selectbox("Pilih jenis reaksi yang mungkin:",
                                   ["Pilih...", "Esterifikasi (asam karboksilat + alkohol)",
                                    "Amida (asam karboksilat + amina primer)",
                                    "Hidrogenasi alkena (alkena + H₂)",
                                    "Adisi Br₂ ke alkena",
                                    "Substitusi nukleofilik alkil halida + H₂O"])
        if st.button("⚡ Reaksikan", type="primary") and reaktan2.strip():
            if tipe_reaksi == "Pilih...":
                st.warning("Pilih jenis reaksi terlebih dahulu.")
            else:
                # Cari reaktan kedua
                comp2 = search_compound(reaktan2.strip())
                if comp2 is None:
                    st.error("Senyawa kedua tidak ditemukan.")
                else:
                    smi2 = comp2.canonical_smiles
                    smi1 = smiles
                    rxn_map = {
                        "Esterifikasi (asam karboksilat + alkohol)": (
                            "[C:1](=[O:2])-[OH:3].[H:4][O:5][C:6]>>[C:1](=[O:2])[O:5][C:6]", True),
                        "Amida (asam karboksilat + amina primer)": (
                            "[C:1](=[O:2])-[OH:3].[H:4][N:5][C:6]>>[C:1](=[O:2])[N:5][C:6]", True),
                        "Hidrogenasi alkena (alkena + H₂)": (
                            "[C:1]=[C:2].[H:3][H:4]>>[C:1]([H:3])[C:2]([H:4])", True),
                        "Adisi Br₂ ke alkena": (
                            "[C:1]=[C:2].[Br:3][Br:4]>>[C:1]([Br:3])[C:2]([Br:4])", True),
                        "Substitusi nukleofilik alkil halida + H₂O": (
                            "[C:1][Cl,Br,I].[OH2:2]>>[C:1][OH].[H][Cl,Br,I]", True),
                    }
                    if tipe_reaksi not in rxn_map:
                        st.error("Reaksi tidak dikenali.")
                    else:
                        smarts, use_two = rxn_map[tipe_reaksi]
                        if use_two:
                            prod_smi, err = reaction_possible(smarts, smi1, smi2)
                        else:
                            prod_smi, err = reaction_possible(smarts, smi1)
                        if err:
                            st.error(err)
                        else:
                            st.session_state.reaction_smiles = prod_smi
                            st.rerun()

        if "reaction_smiles" in st.session_state and st.session_state.reaction_smiles:
            prod_smiles = st.session_state.reaction_smiles
            st.success("✅ Reaksi berhasil! Produk:")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Struktur 3D Produk**")
                view_p = draw_3d(prod_smiles)
                if view_p:
                    view_p.show()
                else:
                    st.warning("Tidak bisa menampilkan 3D.")
            with col2:
                # Cari info produk
                prod_compound = search_compound(prod_smiles)  # cari via SMILES (gunakan pcp get by SMILES)
                if prod_compound is None:
                    st.info("Senyawa produk tidak ada di database.")
                    st.markdown(f"**SMILES:** `{prod_smiles}`")
                else:
                    info_p = get_compound_info(prod_compound.cid)
                    st.markdown(f"**Nama IUPAC Produk:** {info_p['iupac']}")
                    st.markdown(f"**Berat Molekul:** {info_p['weight']} g/mol")
                    st.markdown(f"**Titik Didih:** {info_p['bp']} °C")
                    st.markdown(f"**Deskripsi:** {info_p['desc']}")
            st.markdown(f"**Reaksi yang terjadi:** {tipe_reaksi}")

    # Tombol kembali
    if st.button("🔙 Kembali ke menu utama"):
        st.session_state.page = "cover"
        # bersihkan data tata nama
        for key in ["compound", "info", "smiles", "reaction_smiles"]:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

# ========== BANK SOAL LATIHAN ==========
def generate_all_soal():
    """Daftar soal: (SMILES, daftar jawaban yang diterima, pembahasan)"""
    soal = [
        ("C", ["metana"], "Metana adalah alkana paling sederhana."),
        ("CC", ["etana"], "Etana memiliki dua atom karbon."),
        ("CCC", ["propana"], "Propana memiliki tiga karbon rantai lurus."),
        ("CO", ["metanol", "metil alkohol"], "Metanol adalah alkohol dengan satu karbon."),
        ("CCO", ["etanol", "etil alkohol"], "Etanol adalah alkohol dua karbon."),
        ("CC(=O)O", ["asam asetat", "asam etanoat", "asam cuka"], "Asam asetat memiliki gugus karboksil."),
        ("O=CO", ["asam format", "asam metanoat"], "Asam format adalah asam karboksilat paling sederhana."),
        ("c1ccccc1", ["benzena"], "Benzena adalah senyawa aromatik dengan enam karbon."),
        ("Cc1ccccc1", ["toluena", "metilbenzena"], "Toluena adalah benzena dengan satu gugus metil."),
        ("Oc1ccccc1", ["fenol"], "Fenol adalah benzena dengan gugus hidroksil."),
        ("CC(C)=O", ["aseton", "propanon", "dimetil keton"], "Aseton adalah keton dengan tiga karbon."),
        ("C=O", ["formaldehida", "metanal"], "Formaldehida adalah aldehida satu karbon."),
        ("CC=O", ["asetaldehida", "etanal"], "Asetaldehida adalah aldehida dua karbon."),
        ("CCOC", ["etil metil eter", "metoksietana"], "Eter dengan gugus etil dan metil."),
        ("CC(=O)OCC", ["etil asetat", "etil etanoat"], "Ester dari asam asetat dan etanol."),
        ("CCN", ["etilamina", "etanaamina"], "Amina primer dengan dua karbon."),
        ("CC(=O)N", ["asetamida", "etanaamida"], "Amida dari asam asetat."),
        ("Nc1ccccc1", ["anilina", "aminobenzena"], "Anilina adalah amina aromatik."),
        ("O=C(O)c1ccccc1", ["asam benzoat", "asam benzenakarboksilat"], "Asam benzoat memiliki gugus karboksil pada benzena."),
        ("CCC(C)=O", ["butanon", "metil etil keton"], "Keton dengan empat karbon."),
        ("CC(O)C", ["isopropil alkohol", "propan-2-ol", "2-propanol"], "Alkohol sekunder tiga karbon."),
        ("C1CCCCC1", ["sikloheksana"], "Sikloalkana enam karbon."),
    ]
    return soal

# ========== HALAMAN LATIHAN SOAL ==========
def latihan_soal():
    st.title("📝 Latihan Soal: Tebak Nama Senyawa")
    st.markdown("Jawablah dengan **nama IUPAC** atau **nama trivial** dalam Bahasa Indonesia.")
    if not st.session_state.soal_list:
        all_soal = generate_all_soal()
        # Acak, lalu ambil 20 soal (tapi cukup 20 saja)
        random.shuffle(all_soal)
        st.session_state.soal_list = all_soal[:20]  # simpan 20 soal
        st.session_state.soal_batch = 0
        st.session_state.soal_index = 0
        st.session_state.feedback = None

    total_soal = len(st.session_state.soal_list)
    batch_start = st.session_state.soal_batch * 10
    batch_end = min(batch_start + 10, total_soal)
    current_soal_idx = batch_start + st.session_state.soal_index
    if current_soal_idx >= batch_end:
        # Batch selesai
        if batch_end < total_soal:
            if st.button("Lanjutkan ke 10 soal berikutnya ➡️", type="primary"):
                st.session_state.soal_batch += 1
                st.session_state.soal_index = 0
                st.session_state.feedback = None
                st.rerun()
        else:
            st.success("🎉 Selamat! Anda telah menyelesaikan semua soal.")
            if st.button("Kembali ke menu"):
                st.session_state.page = "cover"
                st.session_state.soal_list = []
                st.rerun()
        return

    soal = st.session_state.soal_list[current_soal_idx]
    smiles, jawaban_benar, pembahasan = soal
    mol = Chem.MolFromSmiles(smiles)
    img = Draw.MolToImage(mol, size=(400, 200))
    st.image(img, caption=f"Soal {st.session_state.soal_index+1} dari 10 (batch {st.session_state.soal_batch+1})")
    user_jawab = st.text_input("Nama senyawa:", key=f"jawab_{current_soal_idx}")
    if st.button("✔️ Submit Jawaban"):
        if not user_jawab.strip():
            st.warning("Masukkan jawaban terlebih dahulu.")
        else:
            norm_user = user_jawab.strip().lower()
            norm_benar = [j.lower() for j in jawaban_benar]
            if norm_user in norm_benar:
                st.session_state.feedback = ("benar", f"✅ Benar! {pembahasan}")
            else:
                st.session_state.feedback = ("salah", f"❌ Salah. Jawaban yang benar: {' / '.join(jawaban_benar)}. {pembahasan}")
            st.rerun()

    if st.session_state.feedback:
        tipe, pesan = st.session_state.feedback
        if tipe == "benar":
            st.success(pesan)
        else:
            st.error(pesan)
        if st.button("Lanjut ke soal berikutnya ➡️"):
            st.session_state.soal_index += 1
            st.session_state.feedback = None
            st.rerun()

    # Tombol kembali
    if st.button("🔙 Kembali ke menu utama"):
        st.session_state.page = "cover"
        st.session_state.soal_list = []
        st.rerun()

# ========== MAIN ==========
def main():
    if st.session_state.page == "cover":
        cover()
    elif st.session_state.page == "tata_penamaan":
        tata_penamaan()
    elif st.session_state.page == "latihan_soal":
        latihan_soal()

if __name__ == "__main__":
    main()
