import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from common import (concepto, nutricion,
                    load_profiles, load_intervention, load_diet, met_label, DIETS, SAMPLES, KEY_METS)

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
FIBRE_DETAIL = {'strch1': 'Almidón', 'starch1200': 'Almidón resistente', 'cellul': 'Celulosa'}

def page():
    st.title('7 · Aplicaciones en nutrición')

    # ------------------------------------------------------------------ 7.1
    st.subheader('7.1 Dietas de referencia')
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
    st.subheader('7.2 Efecto de la dieta sobre la producción microbiana')

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
              'abundancia de <i>E. siraeum</i> (bloque 6), no por el sustrato: cambiar la dieta no la modifica.</li>'
              '<li><b>H₂S:</b> es el metabolito más sensible a la dieta. Aumenta con la dieta poco saludable (hasta ≈ ×2,3) y la '
              'hiperproteica, y disminuye con la vegetariana (≈ −30 %), en paralelo al aporte de aminoácidos azufrados.</li>'
              '<li><b>Amonio y succinato</b> varían ligeramente; acetato y lactato permanecen en el techo del modelo.</li>'
              '<li><b>Isovalerato y p-cresol</b> son prácticamente nulos con todas las dietas: ninguna de las 12 especies '
              'fermenta aminoácidos ramificados ni aromáticos. El modelo solo predice lo que permiten las reconstrucciones '
              'presentes.</li></ul>'
              '<p>Conclusión: en esta comunidad la dieta modula sobre todo los productos de la <b>fermentación proteica</b>, '
              'mientras que la capacidad de producir AGCC está fijada por la composición de la microbiota.</p>')

    # ------------------------------------------------------------------ 7.3
    st.subheader('7.3 Variabilidad interindividual de la respuesta')
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

    # ------------------------------------------------------------------ 7.4
    st.subheader('7.4 Simulación de una intervención dietética (dosis–respuesta)')
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
  En **CSM5MCXD** la curva se aplana a partir de ×2 (≈ 23 mmol/día): esa microbiota, dominada por una
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
