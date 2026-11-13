import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from common import (concepto, nutricion,
                    load_profiles, load_intervention, load_diet, load_diet_limits, load_diet_foods, met_label, DIETS, SAMPLES, KEY_METS)

# Agrupación de los componentes de las dietas en categorías nutricionales
GROUPS = {
    'Azúcares simples': ['glc_D', 'fru', 'gal', 'sucr', 'lcts', 'malt'],
    'Almidón y fibra': ['strch1', 'starch1200', 'cellul'],
    'Polioles': ['sbt_D', 'mnl', 'xylt'],
    'Proteína (aminoácidos)': ['ala_L', 'arg_L', 'asp_L', 'cys_L', 'glu_L', 'gly', 'his_L', 'ile_L', 'leu_L', 'lys_L',
                               'met_L', 'phe_L', 'pro_L', 'ser_L', 'thr_L', 'trp_L', 'tyr_L', 'val_L'],
    'Grasas saturadas': ['but', 'octa', 'dca', 'ddca', 'ttdca', 'ptdca', 'hdca', 'hpdca', 'ocdca', 'arach', 'docosac', 'lgnc'],
    'Grasas insaturadas': ['ttdcea', 'hdcea', 'ocdcea', 'lnlc', 'lnlnca', 'arachd', 'CE2510', 'doco13ac', 'clpnd', 'crvnc', 'CE4843', 'strdnc', 'adrn'],
    'Colesterol': ['chsterol'],
    'Alcohol': ['etoh'],
}
GROUPS_ALL = {**GROUPS,
    'Vitaminas': ['10fthf', '5mthf', 'adpcbl', 'ascb_L', 'avite1', 'btn', 'caro', 'fol', 'nac', 'ncam', 'phyQ',
                  'pnto_R', 'pydam', 'pydx', 'pydxn', 'retinol', 'ribflv', 'thf', 'thm', 'vitd3'],
    'Minerales': ['ca2', 'cl', 'cu2', 'fe2', 'fe3', 'i', 'k', 'mg2', 'mn2', 'na1', 'pi', 'zn2'],
    'Otros': ['urate'],
}
GROUP_OF = {m: g for g, ms in GROUPS_ALL.items() for m in ms}
DIET_DESC = {
    'EUAverageDiet': '**Europea media.** Pan blanco, carne empanada, patata, lácteos grasos, bollería, refresco y cerveza. Referencia.',
    'HighFiberDiet': '**Rica en fibra.** Integrales, legumbres, semillas, setas, verdura y fruta. Frente a la europea: '
                     'almidón y fibra ×1,4; proteína ×1,4; grasas saturadas ×0,2; casi sin alcohol.',
    'HighProteinDiet': '**Hiperproteica.** Atún, pollo, huevos, queso fresco y proteína en polvo. Aminoácidos ×1,8; '
                       'azúcares ×0,6; grasas saturadas ×0,3; sin alcohol.',
    'UnhealthyDiet': '**Poco saludable.** Pizza, hamburguesa, patatas fritas, embutido, tarta, refresco y cerveza. '
                     'Energía ×1,7; proteína, grasas y colesterol ×2.',
    'VegetarianDiet': '**Vegetariana.** Muesli, fruta, verdura, risotto, seitán y yogur de soja. Proteína ×0,7; '
                      'grasas saturadas ×0,3; casi sin colesterol.',
}
FIBRE_DETAIL = {'strch1': 'Almidón', 'starch1200': 'Almidón resistente', 'cellul': 'Celulosa'}

def diet_limits():
    st.subheader('8.4 Componentes de la dieta que limitan la producción')
    st.markdown(
        """
Se calcula la secreción neta máxima con la dieta europea media y se duplica cada componente de la dieta.
Un componente es **limitante** si duplicarlo aumenta la secreción más de un 1 %. Si ninguno lo es, el límite es
la **microbiota**.
"""
    )
    lim = load_diet_limits()
    if lim.empty:
        st.warning('Resultados no disponibles todavía.')
        return
    mets = [m for m in KEY_METS if m in set(lim['Metabolito'])]
    real = lim[lim['Limitante']]

    # Resumen: tipo de límite por metabolito e individuo
    tipo = (lim.groupby(['Metabolito', 'Muestra'])
            ['Limitante'].any().map({True: 'Dieta', False: 'Microbiota'})
            .unstack().reindex(mets))
    tipo.index = [met_label(m) for m in tipo.index]
    st.markdown('**Factor que limita la secreción neta máxima** (dieta europea media):')
    st.dataframe(tipo.style.map(lambda v: 'background-color: rgba(170,60,160,0.15)' if v == 'Dieta' else ''),
                 use_container_width=True)

    st.markdown(
        """
**Resultados.**
- **H₂S**: único metabolito limitado por la dieta, por **L-cisteína** y **L-metionina**. Cada mmol adicional da
  1 mmol más de H₂S en P2, P4 y P5; en P1, solo ≈ 1 mmol/día en total (microbiota cerca de su máximo).
- **Resto, incluido el butirato**: limitado por la microbiota o por el techo del modelo (≈ 400 mmol/día).
"""
    )
    met = st.selectbox('Metabolito', mets, index=mets.index('h2s') if 'h2s' in mets else 0,
                       format_func=met_label, key='met_lim')
    sub = real[real['Metabolito'] == met]
    if sub.empty:
        st.markdown(f'Ningún componente de la dieta limita la producción de **{met_label(met)}** en estos individuos.')
        return
    piv = sub.pivot_table(index='Componente', columns='Muestra', values='Aumento').fillna(0)
    piv = piv.reindex(columns=[c for c in SAMPLES if c in set(lim['Muestra'])], fill_value=0)
    piv = piv.loc[piv.max(axis=1).sort_values(ascending=False).index]
    piv.index = [met_label(c) for c in piv.index]
    fig = px.imshow(piv, color_continuous_scale='Purples', text_auto='.2f', aspect='auto',
                    labels=dict(color='mmol/día', x='Individuo', y='Componente de la dieta'))
    fig.update_layout(height=120 + 32 * len(piv), margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f'Aumento de la secreción de {met_label(met)} (mmol/persona/día) al duplicar cada componente.')
    with st.expander('Ver la tabla completa'):
        t = sub[['Muestra', 'Componente', 'Cantidad en la dieta', 'Secreción neta máxima', 'Secreción neta con el doble']].copy()
        t['Componente'] = t['Componente'].map(met_label)
        st.dataframe(t.round(2), use_container_width=True, hide_index=True)


def page():
    st.title('8 · Aplicaciones en nutrición')

    # ------------------------------------------------------------------ 7.1
    st.subheader('8.1 Dietas de referencia')
    st.markdown(
        """
Cinco dietas, cada una el menú de un día. El modelo recibe su equivalente en **~90 compuestos** (mmol/persona/día).
La captación por la microbiota se limita al 80 % de cada compuesto, por la absorción en el intestino delgado.
"""
    )
    foods = load_diet_foods()
    st.markdown('**Alimentos de cada dieta.**')
    dfood = st.selectbox('Dieta', list(DIETS), format_func=DIETS.get, key='diet_foods')
    fd = foods[foods['Dieta'] == dfood]
    st.markdown(DIET_DESC[dfood])
    k1, k2, k3 = st.columns(3)
    k1.metric('Alimentos', len(fd))
    k2.metric('Energía total (kcal/día)', f"{fd['Energía (kcal)'].sum():,.0f}".replace(',', '.'))
    k3.metric('Cantidad total (g/día)', f"{fd['Cantidad (g)'].sum():,.0f}".replace(',', '.'))
    cols = st.columns(3)
    for col, meal in zip(cols, ['Desayuno', 'Comida', 'Cena']):
        t = fd[fd['Comida'] == meal][['Alimento', 'Cantidad (g)', 'Energía (kcal)']]
        col.markdown(f'**{meal}** · {t["Energía (kcal)"].sum():.0f} kcal')
        col.dataframe(t, hide_index=True, use_container_width=True)
    with st.expander('Comparar la energía de las cinco dietas'):
        e = foods.groupby(['Dieta', 'Comida'], sort=False)['Energía (kcal)'].sum().reset_index()
        e['Dieta'] = e['Dieta'].map(DIETS)
        fig = px.bar(e, x='Dieta', y='Energía (kcal)', color='Comida', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(height=340, xaxis_title='', yaxis_title='kcal/día', margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('**Compuestos de las dietas por grupo nutricional.**')
    diets = pd.DataFrame({DIETS[d]: load_diet(d) for d in DIETS}).fillna(0)
    agg = pd.DataFrame({g: diets.reindex(m).fillna(0).sum() for g, m in GROUPS.items()}).T
    rel = agg.div(agg[DIETS['EUAverageDiet']], axis=0)
    view = st.radio('Mostrar', ['Relativo a la dieta europea media', 'Valores absolutos (mmol/persona/día)'], horizontal=True)
    data = rel if view.startswith('Relativo') else agg
    long = data.reset_index().melt(id_vars='index', var_name='Dieta', value_name='Valor')
    fig = px.bar(long, x='index', y='Valor', color='Dieta', barmode='group',
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(height=420, xaxis_title='', yaxis_title='× dieta europea' if view.startswith('Relativo') else 'mmol/persona/día',
                      legend=dict(orientation='h', y=-0.25))
    if view.startswith('Relativo'):
        fig.add_hline(y=1, line_dash='dot', line_color='grey')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('**Composición completa de una dieta.**')
    c1, c2 = st.columns(2)
    dsel = c1.selectbox('Dieta', list(DIETS), format_func=DIETS.get, key='diet_detail')
    gsel = c2.selectbox('Grupo de componentes', ['Todos'] + list(GROUPS_ALL), key='diet_group')
    comp = pd.DataFrame({'Cantidad (mmol/persona/día)': diets[DIETS[dsel]],
                         '× dieta europea': diets[DIETS[dsel]] / diets[DIETS['EUAverageDiet']].replace(0, np.nan)})
    comp = comp[(comp.iloc[:, 0] > 0) & (comp.index != 'h2o')]
    comp.insert(0, 'Grupo', [GROUP_OF.get(m, 'Otros') for m in comp.index])
    comp.insert(0, 'Componente', [met_label(m) for m in comp.index])
    if gsel != 'Todos':
        comp = comp[comp['Grupo'] == gsel]
    comp = comp.sort_values('Cantidad (mmol/persona/día)', ascending=True)
    fig = px.bar(comp, x='Cantidad (mmol/persona/día)', y='Componente', color='Grupo', orientation='h', log_x=True,
                 color_discrete_sequence=px.colors.qualitative.Safe, hover_data={'× dieta europea': ':.2f'})
    fig.update_layout(height=max(320, 18 * len(comp) + 120), yaxis_title='', margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation='h', y=-0.08 if len(comp) > 40 else -0.25))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f'{len(comp)} componentes; escala logarítmica; sin agua.')
    with st.expander('Ver la tabla de componentes'):
        st.dataframe(comp.sort_values('Cantidad (mmol/persona/día)', ascending=False).round(3),
                     use_container_width=True, hide_index=True)

    with st.expander('Ver carbohidratos complejos'):
        st.dataframe(diets.loc[list(FIBRE_DETAIL)].rename(index=FIBRE_DETAIL).round(2), use_container_width=True)


    prof = load_profiles()
    if prof.empty or prof['Dieta'].nunique() < 2:
        st.warning('Los perfiles para las distintas dietas todavía no están disponibles. '
                   'Ejecute el precálculo (scripts/02_profiles.sbatch).')
        return

    # ------------------------------------------------------------------ 7.2
    st.subheader('8.2 Efecto de la dieta sobre la producción microbiana')

    keys = [m for m in KEY_METS if m in set(prof['Metabolito'])]
    met = st.selectbox('Metabolito', keys, index=keys.index('but') if 'but' in keys else 0, format_func=met_label)
    sub = prof[prof['Metabolito'] == met].copy()
    sub['Dieta'] = sub['Dieta'].map(DIETS)
    fig = px.bar(sub, x='Muestra', y='Secreción', color='Dieta', barmode='group',
                 color_discrete_sequence=px.colors.qualitative.Set2,
                 category_orders={'Dieta': list(DIETS.values())})
    fig.update_layout(height=420, yaxis_title='Secreción neta máxima (mmol/persona/día)',
                      title=f'{met_label(met)}: capacidad de producción por individuo y dieta',
                      legend=dict(orientation='h', y=-0.2))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('**Cambio respecto a la dieta europea media** (media de las muestras)')
    sel = [m for m in ['ac', 'ppa', 'but', 'isobut', 'isoval', 'lac_L', 'succ', 'for', 'h2', 'h2s', 'nh4', 'indole',
                       'pcresol', 'phenol', 'etoh'] if m in keys]
    mean = prof[prof['Metabolito'].isin(sel)].groupby(['Metabolito', 'Dieta'])['Secreción'].mean().unstack()
    lfc = np.log2((mean + 1e-3).div(mean['EUAverageDiet'] + 1e-3, axis=0)).drop(columns='EUAverageDiet')
    lfc = lfc.reindex(sel)
    lfc.index = [met_label(m) for m in lfc.index]
    lfc.columns = [DIETS[c] for c in lfc.columns]
    lim = max(0.5, float(np.nanmax(np.abs(lfc.values))))
    fig = px.imshow(lfc, color_continuous_scale='RdBu_r', zmin=-lim, zmax=lim, text_auto='.2f', aspect='auto',
                    labels=dict(color='log₂(cambio)'))
    fig.update_layout(height=80 + 32 * len(sel), margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Rojo: más que con la dieta europea; azul: menos. log₂ = 1: el doble.')
    nutricion('Resultados',
              '<ul><li><b>Butirato:</b> igual con las cinco dietas; lo limita <i>E. siraeum</i>.</li>'
              '<li><b>H₂S:</b> el más sensible: hasta ×2,3 con la dieta poco saludable, −30 % con la vegetariana.</li>'
              '<li><b>Acetato y lactato:</b> en el techo del modelo.</li>'
              '<li><b>Isovalerato y p-cresol:</b> ≈ 0; ninguna especie fermenta aminoácidos ramificados ni aromáticos.</li></ul>')

    # ------------------------------------------------------------------ 7.3
    st.subheader('8.3 Variabilidad interindividual de la respuesta')
    concepto('Mejor dieta por individuo',
             '<p>Dieta que maximiza (o minimiza) el metabolito en cada individuo y cambio respecto a la dieta europea.</p>')
    met2 = st.selectbox('Metabolito objetivo', keys, index=keys.index('but') if 'but' in keys else 0,
                        format_func=met_label, key='met_precision')
    goal = st.radio('Objetivo', ['Maximizar (metabolito beneficioso)', 'Minimizar (metabolito perjudicial)'], horizontal=True)
    piv = prof[prof['Metabolito'] == met2].pivot_table(index='Muestra', columns='Dieta', values='Secreción')
    best = piv.idxmax(axis=1) if goal.startswith('Max') else piv.idxmin(axis=1)
    tbl = pd.DataFrame({
        'Dieta europea (mmol/día)': piv['EUAverageDiet'].round(2),
        'Mejor dieta': best.map(DIETS),
        'Valor con la mejor dieta': [round(piv.loc[s, best[s]], 2) for s in piv.index],
    })
    tbl['Cambio (%)'] = ((tbl['Valor con la mejor dieta'] / piv['EUAverageDiet'].replace(0, np.nan) - 1) * 100).round(0)
    st.dataframe(tbl, use_container_width=True)
    piv_n = piv.rename(columns=DIETS)
    fig = px.imshow(piv_n, color_continuous_scale='Greens' if goal.startswith('Max') else 'Reds', text_auto='.1f', aspect='auto',
                    labels=dict(color='mmol/día'))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------ 8.4
    diet_limits()

    # ------------------------------------------------------------------ 8.5
    st.subheader('8.5 Simulación de una intervención dietética (dosis–respuesta)')
    st.markdown(
        """
Dieta europea media con la **fibra y almidón** o la **proteína** (18 aminoácidos) multiplicadas por 0–4.
"""
    )
    iv = load_intervention()
    if iv.empty:
        st.warning('Resultados de la intervención no disponibles todavía.')
    else:
        iv = iv[iv['Estado'] == 'ok']
        c1, c2 = st.columns(2)
        inter = c1.radio('Intervención', sorted(iv['Intervención'].unique()), horizontal=True)
        mets_iv = [m for m in KEY_METS if m in set(iv['Metabolito'])]
        met3 = c2.selectbox('Metabolito', mets_iv, index=mets_iv.index('but') if 'but' in mets_iv else 0,
                            format_func=met_label, key='met_iv')
        d = iv[(iv['Intervención'] == inter) & (iv['Metabolito'] == met3)].sort_values('Factor')
        fig = px.line(d, x='Factor', y='Secreción', color='Muestra', markers=True,
                      color_discrete_sequence=px.colors.qualitative.Bold)
        fig.add_vline(x=1, line_dash='dot', line_color='grey', annotation_text='dieta europea', annotation_position='top')
        fig.update_layout(height=420, xaxis_title=f'Factor de {inter.lower()} (× dieta europea)',
                          yaxis_title='Secreción neta máxima (mmol/persona/día)',
                          title=f'{met_label(met3)} frente a la cantidad de {inter.lower()} en la dieta')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(
            """
Curva creciente: limitada por la dieta. Curva plana: limitada por la microbiota.
"""
        )
        st.markdown(
            """
**Resultados.**
- **Proteína → H₂S:** lineal en P2, P4 y P5 (≈ 1 → 73 mmol/día); en P1 se estanca en ≈ 23 a partir de ×2.
- **Fibra → butirato:** plano en todos: **no respondedores** a una intervención con fibra.
"""
        )

    nutricion('Interpretación nutricional',
              '<ul><li><b>Fibra → AGCC</b> solo si hay especies productoras suficientes.</li>'
              '<li><b>Exceso de proteína</b> → H₂S, amonio, AGCR, fenoles e indoles.</li>'
              '<li>Con la misma dieta, la respuesta depende de la microbiota.</li></ul>')
