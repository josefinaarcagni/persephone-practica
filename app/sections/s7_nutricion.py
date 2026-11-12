import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from common import (concepto, nutricion,
                    load_profiles, load_intervention, load_diet, load_diet_limits, met_label, DIETS, SAMPLES, KEY_METS)

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
FIBRE_DETAIL = {'strch1': 'Almidón', 'starch1200': 'Almidón resistente', 'cellul': 'Celulosa'}

def diet_limits():
    st.subheader('8.4 Componentes de la dieta que limitan la producción')
    st.markdown(
        """
Para cada individuo y metabolito se ha calculado la **secreción neta máxima** con la dieta europea media, manteniendo
el crecimiento de la comunidad en su óptimo. Un componente de la dieta es **limitante** si aumentar su cantidad
aumenta esa secreción máxima (coste reducido distinto de cero en la solución de programación lineal). Para cada
componente limitante se ha duplicado su cantidad en la dieta y se ha recalculado la secreción.

Si ningún componente es limitante, la capacidad de producción está fijada por la **microbiota** (abundancia de las
especies productoras y restricciones de acoplamiento), no por la dieta.
"""
    )
    lim = load_diet_limits()
    if lim.empty:
        st.warning('Resultados no disponibles todavía.')
        return
    mets = [m for m in KEY_METS if m in set(lim['Metabolito'])]
    real = lim[lim['Componente'].notna() & (lim['Aumento'] > 1e-3)]

    # Resumen: tipo de límite por metabolito e individuo
    tipo = (lim.groupby(['Metabolito', 'Muestra'])
            .apply(lambda g: 'Dieta' if ((g['Aumento'] > 1e-3) & g['Componente'].notna()).any() else 'Microbiota')
            .unstack().reindex(mets))
    tipo.index = [met_label(m) for m in tipo.index]
    st.markdown('**Factor que limita la secreción neta máxima** (dieta europea media):')
    st.dataframe(tipo.style.map(lambda v: 'background-color: rgba(170,60,160,0.15)' if v == 'Dieta' else ''),
                 use_container_width=True)

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
    st.caption(f'Aumento de la secreción neta máxima de {met_label(met)} (mmol/persona/día) al duplicar cada componente '
               'limitante de la dieta europea media. 0: el componente no es limitante en ese individuo.')
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
Persephone incluye cinco dietas de referencia, elaboradas con el *Diet Designer* de la base de datos Virtual
Metabolic Human (VMH) a partir de alimentos reales y expresadas como cantidad diaria de unos 90 compuestos
(mmol/persona/día). Los ficheros se distribuyen con el paquete (`persephone/data/diet`).
Antes de llegar a la microbiota, el modelo asume que una parte se absorbe en el intestino delgado
(Persephone limita la captación al 80 % del valor de la dieta y añade cantidades mínimas de micronutrientes esenciales).
"""
    )
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
    st.caption(f'{DIETS[dsel]}: {len(comp)} componentes{"" if gsel == "Todos" else " del grupo seleccionado"}, '
               'eje horizontal en escala logarítmica. El agua se omite.')
    with st.expander('Ver la tabla de componentes'):
        st.dataframe(comp.sort_values('Cantidad (mmol/persona/día)', ascending=False).round(3),
                     use_container_width=True, hide_index=True)

    with st.expander('Ver detalle de carbohidratos complejos (sustratos principales de la fermentación colónica)'):
        st.dataframe(diets.loc[list(FIBRE_DETAIL)].rename(index=FIBRE_DETAIL).round(2), use_container_width=True)
        st.caption('Las dietas de referencia representan la fibra principalmente como celulosa y almidón resistente. '
                   'En análisis más detallados pueden añadirse otras fibras (pectina, inulina, xilano...).')

    nutricion('Composición de las dietas',
              '<ul><li>La dieta <b>rica en fibra</b> multiplica la celulosa (×4,5) y aumenta el almidón; reduce las grasas saturadas.</li>'
              '<li>La dieta <b>hiperproteica</b> casi duplica los aminoácidos; la <b>poco saludable</b> duplica grasas y '
              'colesterol y también aporta muchos aminoácidos.</li>'
              '<li>La <b>vegetariana</b> reduce proteína y colesterol, y aumenta polioles y fructosa.</li></ul>')

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

    st.markdown('**Visión de conjunto: cambio respecto a la dieta europea media (media de las cinco muestras)**')
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
    st.caption('Rojo: mayor capacidad de producción que con la dieta europea; azul: menor. log₂ = 1 equivale al doble.')
    st.caption('Fuente: perfiles NMPC calculados con MgPipe para las 5 muestras y las 5 dietas de referencia.')
    nutricion('Resultados',
              '<ul><li><b>Butirato:</b> idéntico con las cinco dietas en cada individuo. Su producción está limitada por la '
              'abundancia de <i>E. siraeum</i> (bloque 7), no por el sustrato: cambiar la dieta no la modifica.</li>'
              '<li><b>H₂S:</b> es el metabolito más sensible a la dieta. Aumenta con la dieta poco saludable (hasta ≈ ×2,3) y la '
              'hiperproteica, y disminuye con la vegetariana (≈ −30 %), en paralelo al aporte de aminoácidos azufrados.</li>'
              '<li><b>Amonio y succinato</b> varían ligeramente; acetato y lactato permanecen en el techo del modelo.</li>'
              '<li><b>Isovalerato y p-cresol</b> son prácticamente nulos con todas las dietas: ninguna de las 12 especies '
              'fermenta aminoácidos ramificados ni aromáticos. El modelo solo predice lo que permiten las reconstrucciones '
              'presentes.</li></ul>'
              '<p>Conclusión: en esta comunidad la dieta modula sobre todo los productos de la <b>fermentación proteica</b>, '
              'mientras que la capacidad de producir AGCC está fijada por la composición de la microbiota.</p>')

    # ------------------------------------------------------------------ 7.3
    st.subheader('8.3 Variabilidad interindividual de la respuesta')
    concepto('Mejor dieta por individuo',
             '<p>La tabla muestra, para cada individuo, <b>qué dieta maximiza</b> la capacidad de producir el metabolito '
             'seleccionado y cuánto aumenta respecto a la dieta europea. Si las mejores dietas difieren entre individuos, '
             'el modelo sugiere que las recomendaciones dietéticas podrían personalizarse según la microbiota.</p>')
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
A partir de la dieta europea media se ha multiplicado la cantidad de **fibra y almidón** (celulosa, almidón,
almidón resistente) o de **proteína** (los 18 aminoácidos) por un factor entre 0 y 4, manteniendo el resto de
componentes, y se ha recalculado la capacidad de producción de cada metabolito para cada individuo. Esto equivale a
un experimento de **dosis–respuesta** *in silico*.
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
**Lectura de la figura.** Una curva creciente indica que la producción está **limitada por el sustrato** de la dieta;
una curva plana indica que la comunidad **no puede aprovechar** el aumento (faltan especies o rutas, o el factor
limitante es otro). Las diferencias de pendiente entre individuos son, de nuevo, respuestas personalizadas.
"""
        )
        st.markdown(
            """
**Resultados de la simulación.**
- **Proteína → H₂S:** respuesta lineal en cuatro individuos (de ≈ 1 mmol/día sin proteína a ≈ 73 con el cuádruple).
  En **P1** la curva se aplana a partir de ×2 (≈ 23 mmol/día): esa microbiota, dominada por una
  *Erysipelotrichaceae* que no produce H₂S, tiene pocos productores y alcanza antes su límite. Es un ejemplo claro de
  cómo un mismo cambio dietético tiene efectos distintos según la microbiota.
- **Fibra → butirato:** las curvas son planas en todos los individuos. Ninguna de estas comunidades puede convertir
  más fibra en más butirato, porque su capacidad está limitada por la abundancia de productores. En la práctica, estos
  individuos serían **«no respondedores»** a una intervención con fibra; la alternativa sería modificar la propia
  microbiota (p. ej. con probióticos o prebióticos específicos), hipótesis que el modelo permite evaluar.
"""
        )

    nutricion('Casos de interés nutricional',
              '<ul><li><b>Fibra → AGCC.</b> En la literatura, más fibra fermentable suele aumentar acetato, propionato y '
              'butirato. El modelo matiza esta expectativa: solo ocurre si la microbiota contiene productores suficientes, '
              'condición que no se cumple en estas muestras.</li>'
              '<li><b>Proteína → AGCR, amonio, H₂S, fenoles e indoles.</b> El exceso de proteína que llega al colon se fermenta '
              'a isobutirato, isovalerato, amonio, p-cresol o indol, metabolitos asociados a efectos negativos sobre el epitelio.</li>'
              '<li><b>Respuesta individual.</b> Aunque la dieta sea idéntica, el resultado depende de qué especies estén presentes: '
              'el modelo ayuda a identificar «respondedores» y «no respondedores» antes de una intervención.</li></ul>')
