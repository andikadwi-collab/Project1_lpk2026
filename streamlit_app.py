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
                "produk": "Haloalkana (Alkil Halida) atau Alkanol (Alk
