import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from common import (concepto, nutricion,
                    load_example, load_profiles, load_active_exchanges, model_stats, species_label,
                    met_label, KEY_METS, SAMPLES, profile_samples)

DOT = r"""
digraph G {
  rankdir=LR; bgcolor="transparent";
  node [fontname="Helvetica", fontsize=11, style="rounded,filled", shape=box, color="#666666"];
  diet [label="Dieta  [d]\nDiet_EX_met_d", fillcolor="#f8bbd0"];
  lumen [label="Lumen intestinal  [u]\n(espacio compartido)", fillcolor="#fff3e0", shape=cylinder];
  fe [label="Heces  [fe]\nEX_met_fe", fillcolor="#d7ccc8"];
  subgraph cluster_sp { label="Especies (cada una con su red completa)"; style="dashed"; color="#999999"; fontname="Helvetica";
    a [label="Especie A\n(× abundancia a)", fillcolor="#c8e6c9"];
    b [label="Especie B\n(× abundancia b)", fillcolor="#c8e6c9"];
    c [label="Especie C\n(× abundancia c)", fillcolor="#c8e6c9"]; }
  bio [label="Biomasa de la comunidad\n= a·BioA + b·BioB + c·BioC", fillcolor="#bbdefb"];
  diet -> lumen [label="DUt_met"];
  lumen -> a [dir=both]; lumen -> b [dir=both]; lumen -> c [dir=both];
  lumen -> fe [label="UFEt_met"];
  a -> bio; b -> bio; c -> bio;
}
"""

def page():
    st.title('7 · MgPipe: modelos de comunidad y perfiles metabólicos')

    st.subheader('7.1 Construcción del modelo de comunidad')
    st.graphviz_chart(DOT, use_container_width=True)
    st.markdown(
        """
1. Une las reconstrucciones de las especies de la muestra.
2. Las conecta a un **lumen compartido** [u]: lo que una secreta, otra puede consumirlo (**alimentación cruzada**).
3. Añade **dieta** [d] (entrada) y **heces** [fe] (salida).
4. **Biomasa comunitaria**: cada especie aporta según su abundancia.
5. **Restricciones de acoplamiento**: los flujos de cada especie quedan limitados por su biomasa.
"""
    )
    stats = model_stats()
    if len(stats):
        st.markdown('**Tamaño de los modelos de comunidad:**')
        st.dataframe(stats.style.format('{:,.0f}'), use_container_width=True)
        st.caption('Una bacteria aislada: ~1.000–1.500 reacciones.')

    st.subheader('7.2 Capacidad de intercambio de metabolitos por especie')
    st.markdown(
        """
Metabolitos que cada especie puede **captar o secretar** (FVA por especie).
"""
    )
    try:
        act = load_active_exchanges()
        keys = [m for m in KEY_METS if m in act.index]
        mets = st.multiselect('Metabolitos', keys, default=[m for m in ['ac', 'ppa', 'but', 'lac_L', 'succ', 'h2', 'h2s', 'nh4', 'isoval', 'indole'] if m in keys],
                              format_func=met_label)
        if mets:
            sub = act.loc[mets].copy()
            sub.index = [met_label(m) for m in mets]
            sub.columns = [species_label(c) for c in sub.columns]
            fig = px.imshow(sub, color_continuous_scale=[[0, '#eeeeee'], [1, '#2e7d32']], zmin=0, zmax=1, aspect='auto')
            fig.update_coloraxes(showscale=False)
            fig.update_layout(height=60 + 34 * len(mets), margin=dict(l=10, r=10, t=10, b=10))
            fig.update_xaxes(tickangle=-40)
            st.plotly_chart(fig, use_container_width=True)
            st.caption('Verde: intercambio activo.')
    except FileNotFoundError:
        st.warning('Matriz de intercambios no disponible.')

    st.subheader('7.3 Perfiles metabólicos por individuo (dieta europea media)')
    concepto('Capacidad neta máxima de producción (NMPC)',
             '<p>Con la dieta aplicada y la biomasa cerca del óptimo, FVA da la <b>secreción neta máxima</b> (producción '
             'por encima de lo que aporta la dieta) y la <b>captación neta máxima</b> de cada metabolito (mmol/persona/día).</p>')

    prof = load_profiles()
    eu = prof[prof['Dieta'] == 'EUAverageDiet']
    if eu.empty:
        st.warning('Los perfiles metabólicos aún no están disponibles. Ejecute el precálculo (scripts/02_profiles.sbatch).')
        return

    keys = [m for m in KEY_METS if m in set(eu['Metabolito'])]
    sel = st.multiselect('Metabolitos a mostrar', keys,
                         default=[m for m in ['ac', 'ppa', 'but', 'isobut', 'isoval', 'lac_L', 'succ', 'h2', 'h2s', 'nh4', 'indole', 'pcresol'] if m in keys],
                         format_func=met_label, key='prof_mets')
    scale = st.radio('Escala de color', ['Valor absoluto', 'Normalizado por metabolito (0–1)'], horizontal=True)
    if sel:
        mat = eu[eu['Metabolito'].isin(sel)].pivot_table(index='Metabolito', columns='Muestra', values='Secreción')
        mat = mat.reindex(sel)
        if scale.startswith('Normalizado'):
            mat = mat.div(mat.max(axis=1).replace(0, np.nan), axis=0).fillna(0)
        mat.index = [met_label(m) for m in mat.index]
        fig = px.imshow(mat, color_continuous_scale='YlOrRd', aspect='auto', text_auto='.1f' if not scale.startswith('N') else '.2f',
                        labels=dict(color='mmol/persona/día' if not scale.startswith('N') else 'relativo'))
        fig.update_layout(height=80 + 36 * len(sel), margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption('Secreción neta máxima con la dieta europea media.')

    st.markdown(
        """
- **Butirato:** ≈ 315 mmol/día en P2 (*E. siraeum* 79 %) frente a ≈ 4 en P5 (*E. siraeum* 1 %).
- **H₂S:** ≈ 18,5 en ambas; lo limita la dieta (aminoácidos azufrados), no la microbiota.
"""
    )

    st.subheader('7.4 Factores que limitan la capacidad de producción')
    st.markdown(
        """
Abundancia de las especies productoras (apartado 7.2) frente a la secreción neta máxima.
"""
    )
    try:
        act = load_active_exchanges()
        counts_, taxa_ = load_example()
        ab = counts_.copy()
        ab.index = taxa_['Taxon']
        opts = [m for m in KEY_METS if m in act.index and m in set(eu['Metabolito'])]
        mp = st.selectbox('Metabolito', opts, index=opts.index('but') if 'but' in opts else 0,
                          format_func=met_label, key='prod_met')
        prod = act.columns[act.loc[mp] > 0]
        df = pd.DataFrame({'Abundancia de productores': ab.reindex(prod).fillna(0).sum()})
        df['Secreción'] = eu[eu['Metabolito'] == mp].set_index('Muestra')['Secreción']
        df = df.dropna().reset_index().rename(columns={'index': 'Muestra'})
        fig = px.scatter(df, x='Abundancia de productores', y='Secreción', text='Muestra')
        fig.update_traces(textposition='top center', marker=dict(size=12, color='#6a1b9a'))
        fig.update_layout(height=380, xaxis_tickformat='.0%', yaxis_title='Secreción neta máxima (mmol/persona/día)',
                          margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption('Especies consideradas productoras: ' + ', '.join(species_label(p) for p in prod) + '.')
    except FileNotFoundError:
        pass

    concepto('Tipos de límite',
             '<ul><li><b>Microbiano</b> (butirato): ≈ 4 mmol/día por cada 1 % de <i>E. siraeum</i>.</li>'
             '<li><b>Dietético</b> (H₂S): valores parecidos con composiciones muy distintas.</li>'
             '<li><b>Techo del modelo</b> (acetato, lactato, succinato, amonio): ≈ 400 mmol/día en casi todas las '
             'muestras; no discrimina entre individuos.</li></ul>')

    st.subheader('7.5 Perfil completo de una muestra')
    c1, c2 = st.columns([1, 3])
    s = c1.selectbox('Muestra', profile_samples())
    kind = c1.radio('Tipo de flujo', ['Secreción', 'Captación'])
    n = c1.slider('Nº de metabolitos', 5, 40, 20)
    counts, taxa = load_example()
    comp = counts[s].copy()
    comp.index = [species_label(t) for t in taxa['Taxon']]
    comp = comp[comp > 0.01].sort_values(ascending=False)
    c1.markdown('**Composición:**<br>' + '<br>'.join(f'{k}: {v:.0%}' for k, v in comp.items()), unsafe_allow_html=True)
    one = eu[eu['Muestra'] == s].sort_values(kind, ascending=False).head(n)
    fig = px.bar(one[::-1], x=kind, y='Nombre', orientation='h',
                 color_discrete_sequence=['#c62828' if kind == 'Secreción' else '#1565c0'])
    fig.update_layout(height=120 + 22 * n, xaxis_title='mmol/persona/día', yaxis_title='', margin=dict(t=10))
    c2.plotly_chart(fig, use_container_width=True)
    c2.caption('Los primeros puestos son productos generales (CO₂, H₂O, H⁺, acetato).')

    nutricion('Interpretación nutricional',
              '<p>P1 y P5 apenas pueden producir butirato. ¿Falta fibra o faltan productores? Bloque 8.</p>')
