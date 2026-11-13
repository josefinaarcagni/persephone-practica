import contextlib
import importlib.util
import io
import os
import pickle
import tempfile
import warnings
import pandas as pd
import plotly.express as px
import streamlit as st
from common import (relabel, SAMPLE_LABELS, concepto,
                    load_raw_demo, db_stats, species_label, RES)

def _short(lineage: str) -> str:
    parts = [p.strip() for p in lineage.split(';')]
    sp = parts[-1].replace('s__', '').replace('_', ' ')
    if sp:
        return sp
    return parts[-2].replace('g__', '').replace('_', ' ') + ' (sin especie)'

def stacked_bar(df_rel: pd.DataFrame, title: str):
    long = df_rel.reset_index().melt(id_vars=df_rel.index.name or 'index', var_name='Muestra', value_name='Abundancia')
    long.columns = ['Taxón', 'Muestra', 'Abundancia']
    fig = px.bar(long, x='Muestra', y='Abundancia', color='Taxón', title=title,
                 color_discrete_sequence=px.colors.qualitative.Safe + px.colors.qualitative.Pastel)
    fig.update_layout(yaxis_tickformat='.0%', height=430, legend=dict(font=dict(size=10)), margin=dict(t=50))
    return fig

CUTOFFS = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2]


def mars_precomputed(cutoff: float) -> str:
    return os.path.join(RES, 'MARS_demo', 'cutoffs', f'{cutoff:.0e}.pkl')


def mars_live_available() -> bool:
    return importlib.util.find_spec('persephone') is not None


@st.cache_data(show_spinner=False)
def run_mars(database: str, cutoff: float):
    """Ejecuta MARS si el paquete está instalado; si no, lee el resultado precalculado con los mismos parámetros."""
    if not mars_live_available():
        with open(mars_precomputed(cutoff), 'rb') as f:
            counts, taxa, summ, reads, unmapped, log = pickle.load(f)
    else:
        counts, taxa, summ, reads, unmapped, log = compute_mars(database, cutoff)
    for k, v in SAMPLE_LABELS.items():
        log = log.replace(k, v)
    return relabel(counts), taxa, summ, relabel(reads), relabel(unmapped), log


def compute_mars(database: str, cutoff: float):
    from persephone import runMARS
    raw = load_raw_demo()
    out = tempfile.mkdtemp(prefix='mars_')
    cwd = os.getcwd()
    try:
        os.chdir(out)  # MARS escribe un fichero temporal en el directorio actual
        with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
            warnings.simplefilter('ignore')
            counts, taxa = runMARS(counts=raw.drop(columns='Taxon'), taxa=raw[['Taxon']], database=database,
                                   taxa_delimiter=';', cutoff=cutoff, output_dir=os.path.join(out, 'MARS'))
    finally:
        os.chdir(cwd)
    summ = pd.read_csv(os.path.join(out, 'MARS', 'metrics', 'Species', 'summary_statistics_Species.csv'), index_col=0)
    reads = pd.read_csv(os.path.join(out, 'MARS', 'metrics', 'Species', 'read_counts.csv'), index_col=0)
    unm_f = os.path.join(out, 'MARS', 'normalized_unmapped', 'normalized_unmapped_species.csv')
    unmapped = pd.read_csv(unm_f, index_col=0) if os.path.exists(unm_f) else pd.DataFrame()
    log = open(os.path.join(out, 'MARS', 'MARS.log')).read()
    return counts, taxa, summ, reads, unmapped, log

def page():
    st.title('5 · Datos de entrada y armonización taxonómica (MARS)')

    st.subheader('5.1 Los datos de partida')
    st.markdown(
        """
Entrada de MARS: **lecturas por variante de secuencia (ASV) y muestra**, con el **linaje taxonómico** de cada ASV.
ASV 1–12: las 12 especies de las muestras. ASV 13–15: casos que no pueden modelarse.
"""
    )
    raw = load_raw_demo()
    show = raw.copy()
    show.insert(0, 'Especie (resumen)', show['Taxon'].map(_short))
    st.dataframe(show, use_container_width=True, height=330)
    st.caption('Número de lecturas. «Taxon»: linaje de reino (k__) a especie (s__).')

    rel = raw.drop(columns='Taxon')
    rel.index = raw['Taxon'].map(_short)
    rel = rel / rel.sum()
    st.plotly_chart(stacked_bar(rel, 'Composición relativa antes de MARS'), use_container_width=True)

    st.markdown(
        """
- **ASV_13** (*Prevotella*): clasificado solo hasta género.
- **ASV_14**: *Lachnospiraceae* no cultivada, sin nombre formal.
- **ASV_15** (*Candidatus* Fakeibacter intestinalis): sin reconstrucción en ninguna base de datos.
"""
    )

    st.subheader('5.2 Ejecución de MARS')
    concepto('Qué hace MARS (Microbial Abundances Retrieved from Sequencing data)',
             '<ol><li>Armoniza nombres (sinónimos, reclasificaciones, <i>Candidatus</i>).</li>'
             '<li>Descarta taxones sin especie o por debajo del umbral de abundancia.</li>'
             '<li>Busca cada especie en AGORA2 / APOLLO.</li>'
             '<li><b>Renormaliza</b> las especies mapeadas para que sumen 1.</li></ol>')

    database = 'AGORA2-APOLLO'
    c1, c2 = st.columns(2)
    c1.markdown('**Base de datos:** AGORA2-APOLLO')
    cutoff = c2.select_slider('Umbral de abundancia relativa mínima', options=CUTOFFS,
                              value=1e-6, format_func=lambda x: f'{x:.0e}')
    n_rec, n_sp = db_stats()
    st.caption(f'{n_rec:,} reconstrucciones ({n_sp:,} especies).'.replace(',', '.'))

    if st.button('▶ Ejecutar MARS', type='primary'):
        st.session_state['mars_params'] = (database, cutoff)

    if 'mars_params' not in st.session_state:
        st.info('Pulse «Ejecutar MARS» para procesar la tabla.')
        return

    database, cutoff = st.session_state['mars_params']
    with st.spinner('Ejecutando MARS...'):
        counts, taxa, summ, reads, unmapped, log = run_mars(database, cutoff)
    st.success(f'MARS completado con la base de datos **{database}** y umbral **{cutoff:.0e}**.')

    st.subheader('5.3 Resultados')
    k1, k2, k3 = st.columns(3)
    k1.metric('Taxones antes del mapeo', int(summ.loc['Total number of taxa', 'Pre mapping']))
    k2.metric('Taxones mapeados', int(summ.loc['Total number of taxa', 'Post mapping']))
    k3.metric('Lecturas asignadas a especies modelables',
              f'{reads.loc["Post mapping"].sum() / reads.loc["Pre mapping"].sum():.1%}')

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('**Especies mapeadas (entrada para MgPipe)**')
        t = taxa.copy()
        t['Especie'] = t['Taxon'].map(species_label)
        st.dataframe(t, use_container_width=True, height=300)
    with c2:
        st.markdown('**Taxones no mapeados** (abundancia relativa media)')
        if len(unmapped):
            st.dataframe(unmapped.mean(axis=1).rename('Abundancia media').to_frame().style.format('{:.2%}'),
                         use_container_width=True)

    cm = counts.copy()
    cm.index = taxa['Taxon'].map(species_label)
    st.plotly_chart(stacked_bar(cm, 'Composición relativa después de MARS (renormalizada)'), use_container_width=True)

    with st.expander('Ver las métricas de resumen generadas por MARS'):
        st.dataframe(summ, use_container_width=True)
    with st.expander('Ver el registro (log) de MARS: correcciones de nombres aplicadas'):
        lines = [l.split('\t')[-1] for l in log.splitlines() if 'Replacement' in l or 'removed' in l.lower()]
        st.code('\n'.join(lines) if lines else log[-3000:], language='text')

    st.markdown(
        """
- Tras renormalizar, las especies mapeadas ganan peso: **la cobertura del mapeo es un control de calidad**.
- **Umbral:** con 1e-6 se conservan las 12 especies; con 1e-3 se pierden *E. brachy* y *E. saphenum*.
"""
    )
