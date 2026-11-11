import os
import pandas as pd
import plotly.express as px
import streamlit as st
from common import (concepto, nutricion,
                    load_example, load_mgpipe, species_label, PKG)

FEATURED = {
    'BUTKr': 'Butirato quinasa (producción de butirato)',
    'PBUTT': 'Fosfato butiriltransferasa (producción de butirato)',
    'MMCD': 'Metilmalonil-CoA descarboxilasa (vía del succinato → propionato)',
    'TMAOR1': 'TMAO reductasa (TMAO → TMA)',
    'SULR': 'Sulfito reductasa (producción de H₂S)',
    'PFL': 'Piruvato formiato liasa (fermentación)',
    'LDH_L': 'L-lactato deshidrogenasa',
}

@st.cache_data
def rxn_tax_matrix(taxa: tuple):
    d = os.path.join(PKG, 'models', 'AGORA2-APOLLO')
    ri = pd.read_csv(os.path.join(d, 'AGORA2-APOLLO.rxnInfo.csv'))
    rt = pd.read_csv(os.path.join(d, 'AGORA2-APOLLO.rxnTaxMat.csv'), usecols=list(taxa))
    rt.index = ri['rxnID']
    return rt, ri.set_index('rxnID')

def page():
    st.title('5 · MgPipe: abundancia de reacciones y subsistemas')

    counts, taxa = load_example()
    rt, ri = rxn_tax_matrix(tuple(taxa['Taxon']))
    rxnAb = load_mgpipe('rxnAbundance')
    subsAb = load_mgpipe('subsAbundance')
    rxnPre = load_mgpipe('rxnPresence')

    st.subheader('5.1 Abundancia de reacciones')
    concepto('Fórmula',
             '<p>Para cada reacción <i>r</i> y muestra <i>j</i>:</p>'
             '<p style="text-align:center; font-size:1.1rem"><b>Abundancia(r, j) = Σ<sub>especies i</sub> '
             'Presencia(r, i) × Abundancia relativa(i, j)</b></p>'
             '<p>Es decir, la <b>fracción de la comunidad</b> que posee los genes para catalizar esa reacción. '
             'Un valor de 1 indica que todas las especies la poseen; 0, que ninguna.</p>')

    sel = st.selectbox('Reacción', list(FEATURED),
                       format_func=lambda r: f'{r} — {FEATURED[r]}')
    pres = rt.loc[sel]
    ab = counts.copy()
    ab.index = taxa['Taxon']
    contrib = ab.mul(pres, axis=0)
    contrib.index = [species_label(t) for t in contrib.index]

    c1, c2 = st.columns([1, 2])
    with c1:
        tbl = pd.DataFrame({'Especie': [species_label(t) for t in taxa['Taxon']],
                            '¿Posee la reacción?': ['Sí' if pres[t] == 1 else 'No' for t in taxa['Taxon']]})
        st.dataframe(tbl, hide_index=True, use_container_width=True, height=460)
        st.caption(f'Subsistema: {ri.loc[sel, "rxnSubs"]}')
    with c2:
        long = contrib[contrib.sum(axis=1) > 0].reset_index().melt(id_vars='index', var_name='Muestra', value_name='Aporte')
        long.columns = ['Especie', 'Muestra', 'Aporte']
        fig = px.bar(long, x='Muestra', y='Aporte', color='Especie',
                     title=f'Abundancia de {sel} por muestra y especie que la aporta',
                     color_discrete_sequence=px.colors.qualitative.Safe)
        fig.update_layout(yaxis_range=[0, 1], yaxis_title='Abundancia de la reacción', height=430)
        st.plotly_chart(fig, use_container_width=True)
        if rxnAb is not None and sel in rxnAb.index:
            st.caption('Valores calculados por MgPipe (rxnAbundance.csv): ' +
                       ', '.join(f'{s}: {v:.3f}' for s, v in rxnAb.loc[sel].items()))

    if rxnPre is not None:
        st.markdown(f'En total, las cinco comunidades contienen **{len(rxnAb):,} reacciones distintas**; '
                    'el número de reacciones presentes por muestra es: '.replace(',', '.') +
                    ', '.join(f'{s}: **{n:,}**'.replace(',', '.') for s, n in rxnPre.sum().items()) + '.')

    st.subheader('5.2 Abundancia de subsistemas (rutas metabólicas)')
    st.markdown(
        """
Cada reacción pertenece a un **subsistema** (p. ej. «Metabolismo del butanoato», «Degradación de O-glicanos»).
La abundancia de un subsistema es la **media de las abundancias de sus reacciones**. Esto resume miles de
reacciones en unas 90 rutas interpretables.
"""
    )
    if subsAb is None:
        st.warning('No se encuentran los resultados de MgPipe.')
        return
    n = st.slider('Número de subsistemas más variables entre muestras', 10, len(subsAb), 25)
    top = subsAb.loc[subsAb.var(axis=1).sort_values(ascending=False).index[:n]]
    fig = px.imshow(top, color_continuous_scale='Viridis', aspect='auto', zmin=0, zmax=1,
                    labels=dict(color='Abundancia'))
    fig.update_layout(height=max(380, 18 * n), margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Subsistemas con mayor varianza entre muestras.')
    st.caption('Fuente: subsAbundance.csv, calculado con MgPipe a partir de las abundancias de MARS y la matriz '
               'reacción × especie de AGORA2-APOLLO.')

    subs = st.selectbox('Subsistema', subsAb.index.tolist(),
                        index=subsAb.index.tolist().index('Butanoate metabolism') if 'Butanoate metabolism' in subsAb.index else 0)
    fig = px.bar(subsAb.loc[subs].reset_index(), x='index', y=subs, labels={'index': 'Muestra', subs: 'Abundancia'},
                 color_discrete_sequence=['#1e5ac8'])
    fig.update_layout(yaxis_range=[0, 1], height=320)
    st.plotly_chart(fig, use_container_width=True)

    nutricion('Interpretación nutricional',
              '<p>Subsistemas como <b>degradación de O-glicanos</b> (consumo de mucinas del hospedador, frecuente cuando '
              'falta fibra), <b>metabolismo del almidón y la sacarosa</b>, <b>reacción de Stickland</b> '
              '(fermentación de aminoácidos, típica de dietas ricas en proteína) o <b>metabolismo de ácidos biliares</b> '
              'tienen interpretación directa en nutrición.</p>')

    st.warning('**Limitación:** la abundancia de reacciones refleja *potencial genético*, no actividad. '
               'Una reacción abundante puede no utilizarse si la dieta no aporta el sustrato. La dieta se incorpora '
               'en los **modelos de comunidad** (bloque 6).')
