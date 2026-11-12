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
Para cada muestra, MgPipe:

1. **Toma las reconstrucciones** de todas las especies presentes (tras MARS) y las une en un único modelo.
   Cada especie conserva su metabolismo interno, con sus reacciones etiquetadas con el nombre de la especie.
2. **Conecta las especies a un lumen compartido** [u], donde pueden captar y liberar metabolitos. Así surge la
   **alimentación cruzada**: lo que una especie secreta lo puede consumir otra.
3. **Añade un compartimento de dieta** [d] (entrada) y otro de **heces** [fe] (salida).
4. Define una **reacción de biomasa comunitaria** en la que cada especie contribuye en proporción a su abundancia relativa.
5. Añade **restricciones de acoplamiento**: los flujos de cada especie quedan limitados por su propia biomasa,
   de forma que una especie poco abundante no pueda sostener flujos desproporcionados.
"""
    )
    stats = model_stats()
    if len(stats):
        st.markdown('**Tamaño de los modelos de comunidad:**')
        st.dataframe(stats.style.format('{:,.0f}'), use_container_width=True)
        st.caption('Compárese con una bacteria aislada (~1.000–1.500 reacciones): el modelo comunitario de 12 especies '
                   'supera las 14.000 reacciones.')

    st.subheader('7.2 Capacidad de intercambio de metabolitos por especie')
    st.markdown(
        """
Antes de construir los modelos, MgPipe determina mediante FVA qué metabolitos puede **captar o secretar** cada especie
por separado. Esta matriz indica, por ejemplo, qué especies de la comunidad pueden producir butirato.
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
            st.caption('Verde: la especie posee una reacción de intercambio activa (puede captar y/o secretar el metabolito).')
    except FileNotFoundError:
        st.warning('Matriz de intercambios no disponible.')

    st.subheader('7.3 Perfiles metabólicos por individuo (dieta europea media)')
    concepto('Capacidad neta máxima de producción (NMPC)',
             '<p>Aplicada la dieta, MgPipe fija la biomasa comunitaria cerca de su valor óptimo y calcula con FVA, '
             'para cada metabolito, el <b>flujo máximo de salida hacia las heces</b> y el de <b>entrada desde la dieta</b>. '
             'Combinándolos se obtiene la <b>secreción neta máxima</b> (lo que la comunidad puede producir por encima de lo '
             'que aporta la dieta) y la <b>captación neta máxima</b>. Unidades: mmol/persona/día.</p>')

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
        st.caption('Secreción neta máxima por muestra con la dieta europea media.')
        st.caption('Fuente: perfiles NMPC calculados con MgPipe para cada muestra (dieta europea media, FVA al 99,99 % '
                   'del óptimo, biomasa comunitaria entre 0,4 y 1, solucionador GLPK).')

    st.markdown(
        """
**Comparación entre muestras.** P2 está dominada por *Eubacterium siraeum* (≈ 79 %) y P5 por
*Blautia torques* (≈ 79 %).
- **Butirato:** ≈ 315 mmol/día en P2 frente a ≈ 4 en P5. La diferencia corresponde a la abundancia del
  único productor relevante, *E. siraeum* (79 % frente a 1 %).
- **H₂S:** ambas muestras obtienen prácticamente el mismo valor (≈ 18,5 mmol/día). Las dos contienen productores
  abundantes, de modo que el factor limitante no es la microbiota sino la dieta (aminoácidos azufrados disponibles).
"""
    )

    st.subheader('7.4 Factores que limitan la capacidad de producción')
    st.markdown(
        """
La figura relaciona, para el metabolito elegido, la **abundancia conjunta de las especies capaces de intercambiarlo**
(según la matriz del apartado 7.2) con la secreción neta máxima de cada individuo.
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

    concepto('Dos tipos de límite',
             '<ul><li><b>Límite microbiano.</b> Para el <b>butirato</b>, la secreción crece casi linealmente con la '
             'abundancia de <i>E. siraeum</i> (≈ 4 mmol/día por cada 1 % de abundancia). Las restricciones de acoplamiento '
             'impiden que una especie poco abundante sostenga flujos elevados, por lo que la capacidad depende de '
             '<b>quién está presente y en qué proporción</b>.</li>'
             '<li><b>Límite dietético.</b> Para el <b>H₂S</b>, todas las muestras dan valores parecidos aunque su composición '
             'sea muy distinta: los productores son suficientes y lo que limita es el sustrato que aporta la dieta.</li>'
             '<li><b>Techo del modelo.</b> Algunos metabolitos (acetato, lactato, succinato, amonio) alcanzan valores '
             'cercanos a 400 mmol/día en casi todas las muestras: es el máximo que permiten las restricciones de '
             'acoplamiento para el conjunto de la comunidad. En esos casos el modelo no discrimina entre individuos ni dietas, '
             'y conviene no sobreinterpretarlos.</li></ul>')

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
    c2.caption('Los primeros puestos suelen ocuparlos productos generales del metabolismo (CO₂, H₂O, H⁺, acetato...). '
               'Para la interpretación nutricional interesan las diferencias entre individuos y entre dietas.')

    nutricion('Interpretación nutricional',
              '<p>Cada individuo presenta un perfil metabólico propio, determinado por su microbiota. Las muestras P1 y P5 muestran '
              'una capacidad muy baja de producir butirato. Antes de recomendar más fibra conviene preguntarse si el problema '
              'es la dieta o la ausencia de especies productoras; el bloque 8 aborda esta cuestión.</p>')
