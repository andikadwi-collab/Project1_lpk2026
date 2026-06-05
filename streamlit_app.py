import streamlit as st
import pubchempy as pcp
from rdkit import Chem
from rdkit.Chem import Draw, AllChem, Descriptors
from rdkit.Chem.Draw import IPythonConsole
import py3Dmol
import random
import time

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
if "compound_data" not in st.session_state:
    st.session_state.compound_data = None
if "reaction_result" not in st.session_state:
    st.session_state.reaction_result = None

# ========== FUNGSI BANTU ==========

@st.cache_data(ttl=3600)
def search_compound(name):
    """Cari senyawa berdasarkan nama trivial/IUPAC di PubChem."""
    try:
        compounds = pcp.get_compounds(name, 'name')
        if compounds:
            comp = compounds[0]
            return {
                "cid": comp.cid,
                "iupac": comp.iupac_name if comp.iupac_name else "Tidak tersedia",
                "weight": comp.molecular_weight if comp.molecular_weight else "Tidak diketahui",
                "bp": comp.boiling_point if comp.boiling_point else "Tidak diketahui",
                "smiles": comp.canonical_smiles,
                "synonyms": ", ".join(comp.synonyms[:5]) if comp.synonyms else "Tidak tersedia"
            }
        return None
    except Exception as e:
        st.error(f"Error mencari senyawa: {str(e)}")
        return None

def draw_3d(smiles):
    """Tampilkan struktur 3D interaktif menggunakan py3Dmol."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, randomSeed=42)
        AllChem.MMFFOptimizeMolecule(mol)
        
        conf = mol.GetConformer()
        xyz_lines = []
        for atom in mol.GetAtoms():
            pos = conf.GetAtomPosition(atom.GetIdx())
            xyz_lines.append(f"{atom.GetSymbol()} {pos.x:.4f} {pos.y:.4f} {pos.z:.4f}")
        
        xyz_str = "\n".join(xyz_lines)
        view = py3Dmol.view(width=500, height=400)
        view.addModel(xyz_str, "xyz")
        view.setStyle({"stick": {}, "sphere": {"radius": 0.4}})
        view.zoomTo()
        view.spin()
        return view
    except:
        return None

def detect_functional_groups(smiles):
    """Deteksi gugus fungsi sederhana dari SMILES."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return []
        
        groups = []
        patterns = {
            "asam karboksilat": "[CX3](=O)[OX2H1]",
            "alkohol/fenol": "[OX2H]",
            "amina primer": "[NX3H2]",
            "amina sekunder": "[NX3H1]",
            "amina tersier": "[NX3]([CX4])([CX4])[CX4]",
            "alkena": "[CX3]=[CX3]",
            "alkuna": "[CX2]#[CX2]",
            "aldehida": "[CX3H1](=O)[#6]",
            "keton": "[CX3](=O)[CX3]",
            "ester": "[CX3](=O)[OX2][CX4]",
            "eter": "[OX2]([CX4])[CX4]",
            "amida": "[NX3][CX3](=[OX1])",
            "benzena/aromatik": "c1ccccc1"
        }
        
        for name, smarts in patterns.items():
            pattern = Chem.MolFromSmarts(smarts)
            if pattern and mol.HasSubstructMatch(pattern):
                groups.append(name)
        return groups if groups else ["tidak teridentifikasi"]
    except:
        return ["tidak teridentifikasi"]

def simulate_reaction(smiles1, smiles2, reaction_type):
    """Simulasi reaksi kimia berdasarkan tipe yang dipilih."""
    reactions = {
        "Esterifikasi": {
            "smarts": "[C:1](=[O:2])[O:3].[H:4][O:5][C:6]>>[C:1](=[O:2])[O:5][C:6].[O:3][H:4]",
            "type": "esterifikasi",
            "description": "Reaksi esterifikasi antara asam karboksilat dan alkohol"
        },
        "Hidrogenasi alkena": {
            "smarts": "[C:1]=[C:2].[H][H]>>[C:1]-[C:2]",
            "type": "adisi",
            "description": "Reaksi adisi hidrogen pada ikatan rangkap"
        },
        "Adisi HX ke alkena": {
            "smarts": "[C:1]=[C:2].[H][Br,Cl,I:3]>>[C:1]-[C:2]-[Br,Cl,I:3]",
            "type": "adisi",
            "description": "Reaksi adisi asam halida pada alkena"
        },
        "Oksidasi alkohol primer": {
            "smarts": "[C:1][CH2:2][OH:3]>>[C:1][CH:2]=[O:3]",
            "type": "oksidasi",
            "description": "Oksidasi alkohol primer menjadi aldehida"
        }
    }
    
    if reaction_type not in reactions:
        return None, "Tipe reaksi tidak tersedia"
    
    try:
        rxn_info = reactions[reaction_type]
        rxn = AllChem.ReactionFromSmarts(rxn_info["smarts"])
        mol1 = Chem.MolFromSmiles(smiles1)
        mol2 = Chem.MolFromSmiles(smiles2) if smiles2 else None
        
        if mol2:
            products = rxn.RunReactants((mol1, mol2))
        else:
            products = rxn.RunReactants((mol1,))
        
        if products:
            main_product = products[0][0]
            Chem.SanitizeMol(main_product)
            product_smiles = Chem.MolToSmiles(main_product)
            return {
                "smiles": product_smiles,
                "type": rxn_info["type"],
                "description": rxn_info["description"]
            }, None
        else:
            return None, "Reaksi tidak dapat berlangsung dengan reaktan yang diberikan"
    except Exception as e:
        return None, f"Error dalam simulasi reaksi: {str(e)}"

# ========== HALAMAN COVER ==========
def cover():
    st.markdown("""
    <style>
    .cover-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        margin-top: 20px;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .member-list {
        font-size: 18px;
        line-height: 2.2;
        color: #333;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
        padding: 10px 24px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("<div class='cover-box'>", unsafe_allow_html=True)
        st.markdown("# 🧪 Aplikasi Pembelajaran Kimia Organik")
        st.markdown("### Tata Penamaan Senyawa & Latihan Soal")
        st.markdown("---")
        st.markdown("### 👥 Anggota Kelompok")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px;'>
        <h3 style='color: #667eea;'>📋 Anggota:</h3>
        <p style='font-size: 16px; line-height: 2.5;'>
        🔹 ANDIKA DWI PRASHOJO<br>
        🔹 JAWAHER SABRINA A<br>
        🔹 NAELY LUTHFIYAH ARIF<br>
        🔹 SALWA AZKA SABANA<br>
        🔹 ALEX KUSUMAH
        </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📚 Pilih Menu:")
        menu = st.radio("", 
                       ["🔬 Tata Penamaan Senyawa", "📝 Latihan Soal"],
                       label_visibility="collapsed")
        
        if st.button("✨ Masuk ke Aplikasi", type="primary", use_container_width=True):
            if "Tata Penamaan" in menu:
                st.session_state.page = "tata_penamaan"
            else:
                st.session_state.page = "latihan_soal"
                # Reset soal
                st.session_state.soal_batch = 0
                st.session_state.soal_index = 0
                st.session_state.soal_list = []
                st.session_state.feedback = None
            st.rerun()

# ========== HALAMAN TATA PENAMAAN ==========
def tata_penamaan():
    st.title("🔬 Tata Penamaan Senyawa Organik")
    st.markdown("Cari senyawa berdasarkan nama IUPAC atau trivial, lihat struktur 3D, dan simulasikan reaksi kimia!")
    
    # Input pencarian
    col1, col2 = st.columns([3, 1])
    with col1:
        nama_senyawa = st.text_input("Masukkan nama senyawa:", 
                                     placeholder="Contoh: asam asetat, ethanol, benzena, metana...")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        cari_button = st.button("🔍 Cari Senyawa", type="primary", use_container_width=True)
    
    if cari_button and nama_senyawa:
        with st.spinner("🔎 Mencari senyawa di database PubChem..."):
            compound_data = search_compound(nama_senyawa.strip())
            if compound_data:
                st.session_state.compound_data = compound_data
                st.session_state.reaction_result = None
                st.success(f"✅ Senyawa ditemukan: {compound_data['iupac']}")
            else:
                st.error("❌ Senyawa tidak ditemukan. Coba gunakan nama lain atau periksa ejaan.")
    
    # Tampilkan hasil pencarian
    if st.session_state.compound_data:
        data = st.session_state.compound_data
        
        st.markdown("---")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🧬 Struktur 3D Molekul")
            view_3d = draw_3d(data['smiles'])
            if view_3d:
                view_3d.show()
            else:
                st.warning("⚠️ Tidak dapat membuat visualisasi 3D untuk senyawa ini")
            
            # Struktur 2D sebagai backup
            mol = Chem.MolFromSmiles(data['smiles'])
            if mol:
                img = Draw.MolToImage(mol, size=(400, 200))
                st.image(img, caption="Struktur 2D")
        
        with col2:
            st.subheader("📊 Informasi Senyawa")
            st.markdown(f"""
            <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px;'>
            <p><strong>🧪 Nama IUPAC:</strong> {data['iupac']}</p>
            <p><strong>⚖️ Berat Molekul:</strong> {data['weight']} g/mol</p>
            <p><strong>🌡️ Titik Didih:</strong> {data['bp']} °C</p>
            <p><strong>📝 Sinonim:</strong> {data['synonyms']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Deteksi gugus fungsi
            groups = detect_functional_groups(data['smiles'])
            st.markdown(f"**🔍 Gugus Fungsi Terdeteksi:** {', '.join(groups)}")
        
        # Bagian Simulasi Reaksi
        st.markdown("---")
        st.subheader("⚗️ Simulasi Reaksi Kimia")
        
        col1, col2 = st.columns(2)
        with col1:
            reaktan2 = st.text_input("Senyawa kedua (nama):", 
                                    placeholder="Contoh: etanol, HCl, H2...",
                                    key="reactant2")
        with col2:
            tipe_reaksi = st.selectbox("Pilih tipe reaksi:", 
                                      ["Pilih tipe reaksi...",
                                       "Esterifikasi",
                                       "Hidrogenasi alkena", 
                                       "Adisi HX ke alkena",
                                       "Oksidasi alkohol primer"])
        
        if st.button("⚡ Simulasikan Reaksi", type="primary"):
            if tipe_reaksi == "Pilih tipe reaksi...":
                st.warning("⚠️ Pilih tipe reaksi terlebih dahulu!")
            elif not reaktan2:
                st.warning("⚠️ Masukkan senyawa kedua!")
            else:
                with st.spinner("🔄 Mensimulasikan reaksi..."):
                    # Cari senyawa kedua
                    compound2 = search_compound(reaktan2.strip())
                    if not compound2:
                        st.error("❌ Senyawa kedua tidak ditemukan!")
                    else:
                        result, error = simulate_reaction(data['smiles'], 
                                                        compound2['smiles'], 
                                                        tipe_reaksi)
                        if error:
                            st.error(f"❌ {error}")
                        else:
                            st.session_state.reaction_result = result
                            st.success("✅ Reaksi berhasil disimulasikan!")
        
        # Tampilkan hasil reaksi
        if st.session_state.reaction_result:
            st.markdown("---")
            result = st.session_state.reaction_result
            
            st.subheader("🧪 Hasil Reaksi")
            st.info(f"**Tipe Reaksi:** {result['type'].capitalize()} - {result['description']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Struktur Produk:**")
                view_prod = draw_3d(result['smiles'])
                if view_prod:
                    view_prod.show()
                else:
                    mol_prod = Chem.MolFromSmiles(result['smiles'])
                    if mol_prod:
                        img = Draw.MolToImage(mol_prod, size=(400, 200))
                        st.image(img, caption="Struktur Produk")
            
            with col2:
                # Cari info produk
                prod_data = search_compound(result['smiles'])
                if prod_data:
                    st.markdown(f"""
                    **Nama Produk:** {prod_data['iupac']}<br>
                    **Berat Molekul:** {prod_data['weight']} g/mol<br>
                    **Titik Didih:** {prod_data['bp']} °C
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"**SMILES Produk:** `{result['smiles']}`")
    
    # Tombol kembali
    if st.button("🔙 Kembali ke Menu Utama"):
        st.session_state.compound_data = None
        st.session_state.reaction_result = None
        st.session_state.page = "cover"
        st.rerun()

# ========== BANK SOAL ==========
def generate_soal_bank():
    """Generate bank soal dengan jawaban dalam Bahasa Indonesia."""
    return [
        {"smiles": "C", "jawaban": ["metana"], "pembahasan": "Metana adalah alkana paling sederhana dengan 1 atom karbon."},
        {"smiles": "CC", "jawaban": ["etana"], "pembahasan": "Etana memiliki 2 atom karbon."},
        {"smiles": "CCC", "jawaban": ["propana"], "pembahasan": "Propana adalah alkana dengan 3 karbon rantai lurus."},
        {"smiles": "CCCC", "jawaban": ["butana"], "pembahasan": "Butana memiliki 4 atom karbon."},
        {"smiles": "CO", "jawaban": ["metanol", "metil alkohol"], "pembahasan": "Metanol adalah alkohol dengan 1 atom karbon."},
        {"smiles": "CCO", "jawaban": ["etanol", "etil alkohol"], "pembahasan": "Etanol adalah alkohol dengan 2 karbon, terdapat dalam minuman beralkohol."},
        {"smiles": "CC(C)O", "jawaban": ["isopropil alkohol", "2-propanol", "propan-2-ol"], "pembahasan": "Alkohol sekunder dengan gugus OH pada karbon kedua."},
        {"smiles": "CC(=O)O", "jawaban": ["asam asetat", "asam etanoat", "asam cuka"], "pembahasan": "Asam karboksilat 2 karbon, komponen utama cuka."},
        {"smiles": "O=CO", "jawaban": ["asam format", "asam metanoat"], "pembahasan": "Asam karboksilat paling sederhana dengan 1 karbon."},
        {"smiles": "c1ccccc1", "jawaban": ["benzena"], "pembahasan": "Benzena adalah hidrokarbon aromatik dengan cincin 6 karbon."},
        {"smiles": "Cc1ccccc1", "jawaban": ["toluena", "metilbenzena"], "pembahasan": "Toluena adalah benzena dengan satu gugus metil."},
        {"smiles": "Oc1ccccc1", "jawaban": ["fenol", "hidroksibenzena"], "pembahasan": "Fenol adalah benzena dengan gugus hidroksil."},
        {"smiles": "CC(C)=O", "jawaban": ["aseton", "propanon", "dimetil keton"], "pembahasan": "Keton 3 karbon, sering digunakan sebagai pelarut."},
        {"smiles": "C=O", "jawaban": ["formaldehida", "metanal"], "pembahasan": "Aldehida 1 karbon, digunakan sebagai pengawet."},
        {"smiles": "CC=O", "jawaban": ["asetaldehida", "etanal"], "pembahasan": "Aldehida 2 karbon, zat antara metabolisme alkohol."},
        {"smiles": "CCOC", "jawaban": ["etil metil eter", "metoksietana"], "pembahasan": "Eter dengan gugus etil dan metil."},
        {"smiles": "CC(=O)OCC", "jawaban": ["etil asetat", "etil etanoat"], "pembahasan": "Ester dari asam asetat dan etanol, berbau harum."},
        {"smiles": "CCN", "jawaban": ["etilamina", "etanaamina"], "pembahasan": "Amina primer dengan 2 atom karbon."},
        {"smiles": "O=C(O)c1ccccc1", "jawaban": ["asam benzoat", "asam benzenakarboksilat"], "pembahasan": "Asam karboksilat aromatik pada cincin benzena."},
        {"smiles": "C1CCCCC1", "jawaban": ["sikloheksana"], "pembahasan": "Sikloalkana dengan cincin 6 karbon."},
        {"smiles": "C=CC", "jawaban": ["propena", "propilena"], "pembahasan": "Alkena 3 karbon dengan ikatan rangkap."},
        {"smiles": "C#C", "jawaban": ["etuna", "asetilena"], "pembahasan": "Alkuna 2 karbon dengan ikatan tripel."},
    ]

# ========== HALAMAN LATIHAN SOAL ==========
def latihan_soal():
    st.title("📝 Latihan Soal Tata Nama Senyawa")
    st.markdown("Tebak nama senyawa berdasarkan struktur yang ditampilkan! (Nama IUPAC atau trivial)")
    
    # Inisialisasi soal
    if not st.session_state.soal_list:
        semua_soal = generate_soal_bank()
        random.shuffle(semua_soal)
        st.session_state.soal_list = semua_soal[:20]  # Ambil 20 soal
        st.session_state.soal_batch = 0
        st.session_state.soal_index = 0
        st.session_state.feedback = None
    
    total_soal = len(st.session_state.soal_list)
    batch_start = st.session_state.soal_batch * 10
    batch_end = min(batch_start + 10, total_soal)
    current_index = batch_start + st.session_state.soal_index
    
    # Progress bar
    progress = st.session_state.soal_index / 10
    st.progress(progress, f"Soal {st.session_state.soal_index + 1} dari 10 (Batch {st.session_state.soal_batch + 1})")
    
    # Cek apakah batch sudah selesai
    if current_index >= batch_end:
        st.balloons()
        if batch_end < total_soal:
            st.success(f"🎉 Selamat! Anda menyelesaikan batch {st.session_state.soal_batch + 1}!")
            if st.button("➡️ Lanjut ke 10 Soal Berikutnya", type="primary"):
                st.session_state.soal_batch += 1
                st.session_state.soal_index = 0
                st.session_state.feedback = None
                st.rerun()
        else:
            st.success("🏆 Selamat! Anda telah menyelesaikan semua 20 soal!")
            if st.button("🔄 Kembali ke Menu Utama"):
                st.session_state.soal_list = []
                st.session_state.page = "cover"
                st.rerun()
        return
    
    # Tampilkan soal saat ini
    soal = st.session_state.soal_list[current_index]
    
    # Gambar struktur
    mol = Chem.MolFromSmiles(soal["smiles"])
    if mol:
        img = Draw.MolToImage(mol, size=(500, 250))
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(img, caption=f"Struktur Senyawa - Soal {st.session_state.soal_index + 1}")
    
    # Input jawaban
    user_jawab = st.text_input("Nama senyawa:", 
                              placeholder="Tulis nama IUPAC atau trivial...",
                              key=f"jawab_{current_index}")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("✅ Submit Jawaban", type="primary", use_container_width=True):
            if not user_jawab.strip():
                st.warning("⚠️ Masukkan jawaban terlebih dahulu!")
            else:
                jawaban_user = user_jawab.strip().lower()
                jawaban_benar = [j.lower() for j in soal["jawaban"]]
                
                if jawaban_user in jawaban_benar:
                    st.session_state.feedback = "benar"
                    st.success(f"✅ **Benar!** {soal['pembahasan']}")
                else:
                    st.session_state.feedback = "salah"
                    st.error(f"❌ **Salah!** Jawaban yang benar: {' atau '.join(soal['jawaban'])}")
                    st.info(f"📖 Pembahasan: {soal['pembahasan']}")
    
    with col2:
        if st.session_state.feedback:
            if st.button("➡️ Soal Selanjutnya", type="secondary", use_container_width=True):
                st.session_state.soal_index += 1
                st.session_state.feedback = None
                st.rerun()
    
    # Tombol kembali
    if st.button("🔙 Kembali ke Menu Utama"):
        st.session_state.soal_list = []
        st.session_state.feedback = None
        st.session_state.page = "cover"
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
