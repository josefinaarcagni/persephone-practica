"""Utilidades compartidas de la práctica Persephone (rutas, carga de datos, estilos)."""
import os
import re
import pickle
import pandas as pd
import streamlit as st

APP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(APP)
RES = os.path.join(ROOT, 'results')
DATA = os.path.join(ROOT, 'data')
if os.path.isdir(os.path.join(ROOT, 'q2-Persephone')):
    REPO = os.path.join(ROOT, 'q2-Persephone')          # entradas de ejemplo (counts.tsv, taxa.tsv)
    PKG = os.path.join(REPO, 'persephone', 'data')     # datos del paquete
else:  # versión web: solo tablas de datos y resultados, sin el código de Persephone
    REPO = DATA
    PKG = os.path.join(DATA, 'reference')

DIETS = {
    'EUAverageDiet': 'Dieta europea media',
    'HighFiberDiet': 'Dieta rica en fibra',
    'HighProteinDiet': 'Dieta hiperproteica',
    'UnhealthyDiet': 'Dieta poco saludable (occidental)',
    'VegetarianDiet': 'Dieta vegetariana',
}

PERSEPHONE_URL = 'https://github.com/opencobra/cobratoolbox/tree/master/src/analysis/persephone'

SAMPLES = ['CSM5MCXD', 'CSM5MCY2', 'CSM67U9J', 'CSM67UAW', 'CSM67UB9']

# Metabolitos de interés nutricional (ID VMH -> nombre en español, grupo)
KEY_METS = {
    'ac': ('Acetato', 'Ácidos grasos de cadena corta'),
    'ppa': ('Propionato', 'Ácidos grasos de cadena corta'),
    'but': ('Butirato', 'Ácidos grasos de cadena corta'),
    'isobut': ('Isobutirato', 'Ácidos grasos ramificados'),
    'isoval': ('Isovalerato', 'Ácidos grasos ramificados'),
    'lac_L': ('L-lactato', 'Ácidos orgánicos'),
    'lac_D': ('D-lactato', 'Ácidos orgánicos'),
    'succ': ('Succinato', 'Ácidos orgánicos'),
    'for': ('Formiato', 'Ácidos orgánicos'),
    'etoh': ('Etanol', 'Alcoholes'),
    'h2': ('Hidrógeno (H₂)', 'Gases'),
    'co2': ('CO₂', 'Gases'),
    'ch4': ('Metano', 'Gases'),
    'h2s': ('Sulfuro de hidrógeno (H₂S)', 'Gases'),
    'nh4': ('Amonio', 'Metabolismo nitrogenado'),
    'tma': ('Trimetilamina (TMA)', 'Metabolismo nitrogenado'),
    'indole': ('Indol', 'Derivados del triptófano'),
    'pcresol': ('p-Cresol', 'Fermentación proteica'),
    'phenol': ('Fenol', 'Fermentación proteica'),
    'ttdca': ('Tetradecanoato', 'Lípidos'),
    'trp_L': ('L-triptófano', 'Aminoácidos'),
    'glu_L': ('L-glutamato', 'Aminoácidos'),
    'gaba': ('GABA', 'Neuroactivos'),
    'hista': ('Histamina', 'Aminas biógenas'),
    'ptrc': ('Putrescina', 'Aminas biógenas'),
    'thm': ('Tiamina (B1)', 'Vitaminas'),
    'ribflv': ('Riboflavina (B2)', 'Vitaminas'),
    'fol': ('Folato (B9)', 'Vitaminas'),
    'btn': ('Biotina (B7)', 'Vitaminas'),
    'pnto_R': ('Pantotenato (B5)', 'Vitaminas'),
    'nac': ('Nicotinato (B3)', 'Vitaminas'),
    'adocbl': ('Adenosilcobalamina (B12)', 'Vitaminas'),
}


def met_from_rxn(rxn: str) -> str:
    """EX_but_fe -> but ; Diet_EX_but_d -> but"""
    rxn = re.sub(r'^(Diet_)?EX_', '', rxn)
    return re.sub(r'_(fe|d)$', '', rxn)


@st.cache_data
def vmh_names() -> pd.Series:
    df = pd.read_csv(os.path.join(PKG, 'mets', 'VMH_metabolites.csv'))
    return df.set_index('metID')['metName']


def met_label(met: str) -> str:
    if met in KEY_METS:
        return KEY_METS[met][0]
    n = vmh_names()
    return str(n.get(met, met))


@st.cache_data
def load_example():
    counts = pd.read_table(os.path.join(REPO, 'counts.tsv'), index_col=0)
    taxa = pd.read_table(os.path.join(REPO, 'taxa.tsv'), index_col=0)
    return counts, taxa


@st.cache_data
def load_raw_demo():
    return pd.read_table(os.path.join(DATA, 'raw_counts_demo.tsv'), index_col=0)


def species_label(pan: str) -> str:
    return pan.replace('pan', '', 1).replace('_', ' ')


@st.cache_data
def load_mgpipe(name: str, diet: str = 'EUAverageDiet') -> pd.DataFrame:
    """name: rxnAbundance | rxnPresence | subsAbundance | netSecretionFluxes | netUptakeFluxes"""
    p = os.path.join(RES, diet, name + '.csv')
    if not os.path.exists(p):
        return None
    return pd.read_csv(p, index_col=0)


@st.cache_data
def load_profiles() -> pd.DataFrame:
    """Tabla larga con los perfiles NMPC: Dieta, Muestra, Metabolito, Secreción, Captación.
    Secreción = secreción neta máxima; Captación = captación neta máxima (mmol/persona/día)."""
    rows = []
    for d in DIETS:
        for s in SAMPLES:
            f = os.path.join(RES, 'profiles', f'{s}__{d}.csv')
            if not os.path.exists(f):
                continue
            t = pd.read_csv(f, index_col=0)
            rows.append(pd.DataFrame({'Dieta': d, 'Muestra': s, 'Metabolito': [met_from_rxn(r) for r in t.index],
                                      'Secreción': t['maximum'].values, 'Captación': t['minimum'].values}))
    if not rows:
        return pd.DataFrame(columns=['Dieta', 'Muestra', 'Metabolito', 'Secreción', 'Captación'])
    out = pd.concat(rows, ignore_index=True)
    out['Nombre'] = out['Metabolito'].map(met_label)
    return out


@st.cache_data
def load_intervention() -> pd.DataFrame:
    rows = [pd.read_csv(os.path.join(RES, 'intervention', f)) for f in sorted(os.listdir(os.path.join(RES, 'intervention')))
            if f.endswith('.csv')] if os.path.isdir(os.path.join(RES, 'intervention')) else []
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True).rename(columns={'Secrecion': 'Secreción', 'Captacion': 'Captación'})


@st.cache_data
def load_active_exchanges() -> pd.DataFrame:
    """Matriz especie × metabolito intercambiable (1 = la especie puede intercambiarlo), calculada por MgPipe con FVA."""
    with open(os.path.join(RES, 'EUAverageDiet', 'activeExMets.pkl'), 'rb') as f:
        m = pickle.load(f)
    m.index = [re.sub(r'^EX_|\(e\)$', '', i) for i in m.index]
    return m


@st.cache_data
def model_stats() -> pd.DataFrame:
    pre = os.path.join(RES, 'model_stats.csv')
    if os.path.exists(pre):
        return pd.read_csv(pre, index_col=0)
    rows = []
    for s in SAMPLES:
        r = os.path.join(RES, 'EUAverageDiet', 'models', s + '.rxnInfo.csv')
        m = os.path.join(RES, 'EUAverageDiet', 'models', s + '.metInfo.csv')
        if os.path.exists(r):
            ri = pd.read_csv(r, usecols=['rxnID'])
            rows.append({'Muestra': s, 'Reacciones': len(ri), 'Metabolitos': len(pd.read_csv(m, usecols=['metID'])),
                         'Intercambios con la dieta': int(ri['rxnID'].str.startswith('Diet_EX_').sum()),
                         'Secreciones a heces': int((ri['rxnID'].str.startswith('EX_') & ri['rxnID'].str.endswith('_fe')).sum())})
    return pd.DataFrame(rows).set_index('Muestra') if rows else pd.DataFrame()


@st.cache_data
def load_diet(diet: str, wbm: bool = False) -> pd.Series:
    f = os.path.join(PKG, 'diet', diet + ('WBM' if wbm else '') + '.txt')
    t = pd.read_table(f)
    t.columns = ['r', 'v']
    t['met'] = (t['r'].str.replace(r'^(Diet_)?EX_', '', regex=True)
                .str.replace(r'[\[\(]e[\]\)]$', '', regex=True)
                .str.replace(r'_d$', '', regex=True))
    return t.set_index('met')['v']


@st.cache_data
def db_stats() -> tuple:
    """Nº de reconstrucciones y de especies de AGORA2-APOLLO (tabla del paquete o valores precalculados)."""
    f = os.path.join(PKG, 'sp', 'full_db.parquet')
    if os.path.exists(f):
        db = pd.read_parquet(f)
        return len(db), int(db['Species'].nunique())
    s = pd.read_csv(os.path.join(RES, 'MARS_demo', 'db_stats.csv'))
    return int(s['reconstrucciones'][0]), int(s['especies'][0])


def load_sample_model(sample: str):
    with open(os.path.join(RES, 'EUAverageDiet', 'models', sample + '.pkl'), 'rb') as f:
        return pickle.load(f)


# --------------------------------------------------------------------------
# Elementos visuales didácticos
# --------------------------------------------------------------------------
CSS = """
<style>
.box {border-radius: 8px; padding: 0.9rem 1.1rem; margin: 0.6rem 0 1rem 0; border-left: 4px solid;}
.box h4 {margin: 0 0 0.35rem 0; font-size: 1.02rem;}
.box p, .box li {margin-bottom: 0.25rem;}
.conc {background: rgba(30,90,200,0.07);  border-color: #1e5ac8;}
.nutri{background: rgba(170,60,160,0.08); border-color: #aa3ca0;}
.small {font-size: 0.88rem; opacity: 0.85;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def _box(kind: str, title: str, body: str):
    st.markdown(f'<div class="box {kind}"><h4>{title}</h4>{body}</div>', unsafe_allow_html=True)


def concepto(title, body):
    _box('conc', title, body)


def nutricion(title, body):
    _box('nutri', title, body)


def fuente(text):
    st.caption('Fuente: ' + text)
