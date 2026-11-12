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

SAMPLE_IDS = ['CSM5MCXD', 'CSM5MCY2', 'CSM67U9J', 'CSM67UAW', 'CSM67UB9']   # nombres en los ficheros
SAMPLE_LABELS = {s: f'P{i}' for i, s in enumerate(SAMPLE_IDS, 1)}          # nombres mostrados
SAMPLES = list(SAMPLE_LABELS.values())


def relabel(df):
    """Sustituye los identificadores de muestra por P1–P5 en índice, columnas y columna «Muestra»."""
    df = df.rename(index=SAMPLE_LABELS, columns=SAMPLE_LABELS)
    if 'Muestra' in df.columns:
        df['Muestra'] = df['Muestra'].replace(SAMPLE_LABELS)
    return df

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


# Nombres en español de los componentes de las dietas
DIET_NAMES = {
    '10fthf': '10-Formiltetrahidrofolato',
    '5mthf': '5-Metiltetrahidrofolato',
    'CE2510': 'Ácido eicosenoico (C20:1)',
    'CE4843': 'Ácido eicosadienoico (C20:2)',
    'adpcbl': 'Adenosilcobalamina (vitamina B12)',
    'adrn': 'Ácido adrénico (C22:4)',
    'ala_L': 'L-alanina',
    'arach': 'Araquidato (C20:0)',
    'arachd': 'Araquidonato (C20:4)',
    'arg_L': 'L-arginina',
    'ascb_L': 'L-ascorbato (vitamina C)',
    'asp_L': 'L-aspartato',
    'avite1': 'α-tocoferol (vitamina E)',
    'btn': 'Biotina',
    'but': 'Butirato',
    'ca2': 'Calcio',
    'caro': 'β-caroteno',
    'cellul': 'Celulosa',
    'chsterol': 'Colesterol',
    'cl': 'Cloruro',
    'clpnd': 'Ácido clupanodónico (C22:5)',
    'crvnc': 'Ácido cervónico (DHA, C22:6 n-3)',
    'cu2': 'Cobre',
    'cys_L': 'L-cisteína',
    'dca': 'Decanoato (C10:0)',
    'ddca': 'Laurato (C12:0)',
    'doco13ac': 'Ácido docosenoico (C22:1)',
    'docosac': 'Ácido behénico (C22:0)',
    'etoh': 'Etanol',
    'fe2': 'Hierro (Fe²⁺)',
    'fe3': 'Hierro (Fe³⁺)',
    'fol': 'Folato',
    'fru': 'D-fructosa',
    'gal': 'D-galactosa',
    'glc_D': 'D-glucosa',
    'glu_L': 'L-glutamato',
    'gly': 'Glicina',
    'h2o': 'Agua',
    'hdca': 'Palmitato (C16:0)',
    'hdcea': 'Palmitoleato (C16:1)',
    'his_L': 'L-histidina',
    'hpdca': 'Margarato (C17:0)',
    'i': 'Yoduro',
    'ile_L': 'L-isoleucina',
    'k': 'Potasio',
    'lcts': 'Lactosa',
    'leu_L': 'L-leucina',
    'lgnc': 'Lignocerato (C24:0)',
    'lnlc': 'Linoleato (C18:2)',
    'lnlnca': 'α-linolenato (C18:3)',
    'lys_L': 'L-lisina',
    'malt': 'Maltosa',
    'met_L': 'L-metionina',
    'mg2': 'Magnesio',
    'mn2': 'Manganeso',
    'mnl': 'D-manitol',
    'na1': 'Sodio',
    'nac': 'Nicotinato',
    'ncam': 'Nicotinamida',
    'ocdca': 'Estearato (C18:0)',
    'ocdcea': 'Oleato (C18:1)',
    'octa': 'Octanoato (C8:0)',
    'phe_L': 'L-fenilalanina',
    'phyQ': 'Filoquinona (vitamina K1)',
    'pi': 'Fosfato',
    'pnto_R': 'Pantotenato',
    'pro_L': 'L-prolina',
    'ptdca': 'Pentadecanoato (C15:0)',
    'pydam': 'Piridoxamina',
    'pydx': 'Piridoxal',
    'pydxn': 'Piridoxina',
    'retinol': 'Retinol (vitamina A)',
    'ribflv': 'Riboflavina',
    'sbt_D': 'D-sorbitol',
    'ser_L': 'L-serina',
    'starch1200': 'Almidón resistente',
    'strch1': 'Almidón',
    'strdnc': 'Ácido estearidónico (C18:4 n-3)',
    'sucr': 'Sacarosa',
    'thf': 'Tetrahidrofolato',
    'thm': 'Tiamina',
    'thr_L': 'L-treonina',
    'trp_L': 'L-triptófano',
    'ttdca': 'Miristato (C14:0)',
    'ttdcea': 'Miristoleato (C14:1)',
    'tyr_L': 'L-tirosina',
    'urate': 'Urato',
    'val_L': 'L-valina',
    'vitd3': 'Colecalciferol (vitamina D3)',
    'xylt': 'Xilitol',
    'zn2': 'Zinc',
    'amet': 'S-adenosil-L-metionina',
    'cgly': 'Cisteinilglicina',
    'glymet': 'Glicil-metionina',
    'metsox_S_L': 'L-metionina S-sulfóxido',
}


def met_label(met: str) -> str:
    if met in KEY_METS:
        return KEY_METS[met][0]
    if met in DIET_NAMES:
        return DIET_NAMES[met]
    n = vmh_names()
    return str(n.get(met, met))


@st.cache_data
def load_example():
    counts = pd.read_table(os.path.join(REPO, 'counts.tsv'), index_col=0)
    taxa = pd.read_table(os.path.join(REPO, 'taxa.tsv'), index_col=0)
    return relabel(counts), taxa


@st.cache_data
def load_raw_demo():
    return relabel(pd.read_table(os.path.join(DATA, 'raw_counts_demo.tsv'), index_col=0))


def species_label(pan: str) -> str:
    return pan.replace('pan', '', 1).replace('_', ' ')


@st.cache_data
def load_mgpipe(name: str, diet: str = 'EUAverageDiet') -> pd.DataFrame:
    """name: rxnAbundance | rxnPresence | subsAbundance | netSecretionFluxes | netUptakeFluxes"""
    p = os.path.join(RES, diet, name + '.csv')
    if not os.path.exists(p):
        return None
    return relabel(pd.read_csv(p, index_col=0))


@st.cache_data
def load_profiles() -> pd.DataFrame:
    """Tabla larga con los perfiles NMPC: Dieta, Muestra, Metabolito, Secreción, Captación.
    Secreción = secreción neta máxima; Captación = captación neta máxima (mmol/persona/día)."""
    rows = []
    for d in DIETS:
        for s in SAMPLE_IDS:
            f = os.path.join(RES, 'profiles', f'{s}__{d}.csv')
            if not os.path.exists(f):
                continue
            t = pd.read_csv(f, index_col=0)
            rows.append(pd.DataFrame({'Dieta': d, 'Muestra': SAMPLE_LABELS[s], 'Metabolito': [met_from_rxn(r) for r in t.index],
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
    return relabel(pd.concat(rows, ignore_index=True).rename(columns={'Secrecion': 'Secreción', 'Captacion': 'Captación'}))


@st.cache_data
def load_diet_foods() -> pd.DataFrame:
    """Menú de un día de cada dieta: comida, alimento, cantidad (g) y energía (kcal)."""
    return pd.read_csv(os.path.join(DATA, 'diet_foods.csv'))


@st.cache_data
def load_diet_limits() -> pd.DataFrame:
    """Componentes de la dieta que limitan la secreción neta máxima (dieta europea media), por muestra y metabolito."""
    d = os.path.join(RES, 'diet_limits')
    fs = sorted(f for f in os.listdir(d) if f.endswith('.csv')) if os.path.isdir(d) else []
    if not fs:
        return pd.DataFrame()
    df = relabel(pd.concat([pd.read_csv(os.path.join(d, f)) for f in fs], ignore_index=True))
    df['Aumento'] = df['Secreción neta con el doble'] - df['Secreción neta máxima']
    # Limitante relevante: duplicar el componente aumenta la secreción más de un 1 % (y más de 0,05 mmol/día)
    df['Limitante'] = df['Componente'].notna() & (df['Aumento'] > 0.05) & (df['Aumento'] > 0.01 * df['Secreción neta máxima'])
    return df


@st.cache_data
def load_active_exchanges() -> pd.DataFrame:
    """Matriz especie × metabolito intercambiable (1 = la especie puede intercambiarlo), calculada por MgPipe con FVA."""
    with open(os.path.join(RES, 'EUAverageDiet', 'activeExMets.pkl'), 'rb') as f:
        m = pickle.load(f)
    m.index = [re.sub(r'^EX_|\(e\)$', '', i) for i in m.index]
    return m


def profile_samples() -> list:
    """Muestras con perfiles metabólicos calculados (las que se usan en los bloques 7 y 8)."""
    d = os.path.join(RES, 'profiles')
    ids = {f.split('__')[0] for f in os.listdir(d)} if os.path.isdir(d) else set()
    return [SAMPLE_LABELS[s] for s in SAMPLE_IDS if s in ids]


@st.cache_data
def model_stats() -> pd.DataFrame:
    df = _model_stats()
    return df.loc[[s for s in df.index if s in profile_samples()]] if len(df) else df


def _model_stats() -> pd.DataFrame:
    pre = os.path.join(RES, 'model_stats.csv')
    if os.path.exists(pre):
        return relabel(pd.read_csv(pre, index_col=0))
    rows = []
    for s in SAMPLE_IDS:
        r = os.path.join(RES, 'EUAverageDiet', 'models', s + '.rxnInfo.csv')
        m = os.path.join(RES, 'EUAverageDiet', 'models', s + '.metInfo.csv')
        if os.path.exists(r):
            ri = pd.read_csv(r, usecols=['rxnID'])
            rows.append({'Muestra': SAMPLE_LABELS[s], 'Reacciones': len(ri), 'Metabolitos': len(pd.read_csv(m, usecols=['metID'])),
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
