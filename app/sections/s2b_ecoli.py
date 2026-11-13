import json
import os

import cobra
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from common import concepto, nutricion, fuente, DATA

MAP = os.path.join(DATA, 'reference', 'maps', 'e_coli_core.Core metabolism.json')
ESCHER_JS = 'https://unpkg.com/escher@1.7.3/dist/escher.min.js'

FUENTES_C = {
    'Glucosa': 'EX_glc__D_e', 'Fructosa': 'EX_fru_e', 'Piruvato': 'EX_pyr_e', 'D-lactato': 'EX_lac__D_e',
    'Succinato': 'EX_succ_e', 'Fumarato': 'EX_fum_e', 'L-malato': 'EX_mal__L_e', '2-oxoglutarato': 'EX_akg_e',
    'Acetato': 'EX_ac_e', 'Etanol': 'EX_etoh_e', 'L-glutamato': 'EX_glu__L_e', 'L-glutamina': 'EX_gln__L_e',
}
PRODUCTOS = {'EX_ac_e': 'Acetato', 'EX_etoh_e': 'Etanol', 'EX_for_e': 'Formiato', 'EX_lac__D_e': 'D-lactato',
             'EX_succ_e': 'Succinato', 'EX_acald_e': 'Acetaldehído', 'EX_pyr_e': 'Piruvato', 'EX_co2_e': 'CO₂'}


@st.cache_resource
def base_model():
    return cobra.io.load_model('textbook')


@st.cache_data
def map_json():
    with open(MAP) as f:
        return f.read()


@st.cache_data
def simulate(fuente_c, captacion, o2, ko):
    m = base_model()
    with m:
        m.reactions.EX_glc__D_e.lower_bound = 0
        m.reactions.get_by_id(fuente_c).lower_bound = -captacion
        m.reactions.EX_o2_e.lower_bound = -o2
        for r in ko:
            m.reactions.get_by_id(r).knock_out()
        sol = m.optimize()
        if sol.status != 'optimal':
            return None
        return sol.fluxes.to_dict()


def escher(fluxes, height=720):
    data = {k: round(v, 4) for k, v in fluxes.items() if abs(v) > 1e-6}
    html = f"""
<div id="map" style="height:{height - 10}px; width:100%; border:1px solid #ddd;"></div>
<script src="{ESCHER_JS}"></script>
<script>
  var mapData = {map_json()};
  escher.Builder(mapData, null, null, escher.libs.d3_select('#map'), {{
    menu: 'zoom', enable_editing: false, enable_keys: false, fill_screen: false,
    never_ask_before_quit: true, scroll_behavior: 'none', enable_tooltips: ['label'],
    reaction_data: {json.dumps(data)},
    reaction_styles: ['color', 'size', 'text', 'abs'],
    reaction_scale: [{{type: 'min', color: '#c8c8c8', size: 10}},
                     {{type: 'value', value: 0.5, color: '#9ecae1', size: 14}},
                     {{type: 'value', value: 5, color: '#3182bd', size: 22}},
                     {{type: 'max', color: '#08306b', size: 30}}],
    reaction_no_data_color: '#e6e6e6', reaction_no_data_size: 6,
    identifiers_on_map: 'bigg_id', hide_secondary_metabolites: false,
  }});
</script>
"""
    components.html(html, height=height)


def page():
    st.title('3 · Modelo de Escherichia coli y mapa metabólico')

    m = base_model()
    st.subheader('3.1 El modelo e_coli_core')
    st.markdown(
        """
Metabolismo central de *E. coli* K-12: glucólisis, pentosas fosfato, ciclo de Krebs, respiración, fermentación
y una reacción de biomasa.
"""
    )
    c1, c2, c3 = st.columns(3)
    c1.metric('Reacciones', len(m.reactions))
    c2.metric('Metabolitos', len(m.metabolites))
    c3.metric('Genes', len(m.genes))
    st.markdown(
        """
Flujos en **mmol/gPS/h** (por gramo de peso seco y hora); crecimiento en **h⁻¹**. Objetivo: biomasa.
`ATPM`: mantenimiento mínimo de 8,39 mmol ATP/gPS/h.
"""
    )
    fuente('modelo e_coli_core (BiGG Models), distribuido con COBRApy; mapa «Core metabolism» de Escher.')

    st.subheader('3.2 Matriz estequiométrica y reacciones de intercambio')
    S = cobra.util.array.create_stoichiometric_matrix(m, array_type='DataFrame')
    nz = int((S != 0).values.sum())
    st.markdown(
        f"""
**S**: {S.shape[0]} metabolitos × {S.shape[1]} reacciones; solo el {f'{100 * nz / S.size:.1f}'.replace('.', ',')} % de las
celdas es distinto de cero. Sufijos: `_c` citosol, `_e` extracelular.
"""
    )
    rxns = ['GLCpts', 'PGI', 'PFK', 'FBA', 'TPI', 'GAPD', 'PGK', 'PGM', 'ENO', 'PYK', 'PDH', 'CS']
    sub = S[rxns]
    sub = sub.loc[(sub != 0).any(axis=1)]
    st.markdown('**Fragmento de S: glucólisis y entrada al ciclo de Krebs.**')
    st.dataframe(sub.astype(int).style.map(
        lambda v: 'color: #c62828' if v < 0 else ('color: #2e7d32' if v > 0 else 'color: #bbb')),
        use_container_width=True, height=420)
    st.caption('Filas: metabolitos. Columnas: reacciones. Rojo: consumo; verde: producción.')

    st.markdown(
        """
Las **reacciones de intercambio** (`EX_`) conectan el modelo con el medio: flujo **negativo** = captación,
**positivo** = secreción. Su límite inferior (lb) **define el medio**. Persephone introduce la dieta del mismo modo.
"""
    )
    ex = pd.DataFrame([{'Reacción': r.id, 'Metabolito': next(iter(r.metabolites)).name,
                        'lb': r.lower_bound, 'ub': r.upper_bound,
                        'Medio por defecto': 'Captación limitada' if -1000 < r.lower_bound < 0 else
                        ('Captación libre' if r.lower_bound <= -1000 else 'Solo secreción')}
                       for r in m.exchanges]).set_index('Reacción')
    st.dataframe(ex, use_container_width=True, height=300)
    st.caption('lb = −1000: sin límite; lb = 0: sin captación. Fuente de carbono por defecto: glucosa (lb = −10).')

    st.subheader('3.3 Simulación del crecimiento')
    c1, c2, c3 = st.columns(3)
    nombre_c = c1.selectbox('Fuente de carbono', list(FUENTES_C))
    captacion = c2.slider('Captación máxima de la fuente de carbono (mmol/gPS/h)', 0.0, 20.0, 10.0, 0.5)
    o2 = c3.slider('Captación máxima de O₂ (mmol/gPS/h)', 0.0, 30.0, 30.0, 0.5,
                   help='0 = condiciones anaerobias. Con 30 el oxígeno no limita el crecimiento.')
    opciones = sorted((r.id for r in m.reactions if not r.boundary and not r.id.startswith('Biomass')),
                      key=lambda x: x.lower())
    ko = st.multiselect('Reacciones eliminadas (deleción génica simulada)', opciones,
                        format_func=lambda r: f'{r} · {m.reactions.get_by_id(r).name}')

    f = simulate(FUENTES_C[nombre_c], captacion, o2, tuple(ko))
    if f is None or f['Biomass_Ecoli_core'] < 1e-6:
        st.error('En estas condiciones el modelo **no puede crecer**.')
        if f is None:
            return

    k1, k2, k3, k4 = st.columns(4)
    k1.metric('Tasa de crecimiento (h⁻¹)', f'{f["Biomass_Ecoli_core"]:.3f}')
    k2.metric('Captación de carbono', f'{-f[FUENTES_C[nombre_c]]:.2f}')
    k3.metric('Captación de O₂', f'{max(0.0, -f["EX_o2_e"]):.2f}')
    k4.metric('Rendimiento (gPS/mmol)',
              f'{f["Biomass_Ecoli_core"] / -f[FUENTES_C[nombre_c]]:.4f}' if f[FUENTES_C[nombre_c]] < -1e-9 else '—')

    sec = {PRODUCTOS[k]: round(v, 2) for k, v in f.items() if k in PRODUCTOS and v > 1e-6}
    st.markdown('**Productos secretados (mmol/gPS/h):** ' +
                (', '.join(f'{k} {v}' for k, v in sec.items()) if sec else 'ninguno'))

    st.markdown('**Mapa del metabolismo central.** Color y grosor ∝ flujo; gris: flujo nulo.')
    escher(f)
    fuente('solución FBA calculada en directo con COBRApy (solucionador GLPK); visualización con Escher.')

    with st.expander('Ver todos los flujos de la solución'):
        df = pd.DataFrame({'Reacción': [m.reactions.get_by_id(r).name for r in f], 'Flujo': list(f.values())},
                          index=list(f)).round(3)
        st.dataframe(df[df['Flujo'].abs() > 1e-6], use_container_width=True)

    st.markdown(
        """
**Comportamiento del modelo** (glucosa 10 mmol/gPS/h):

| Condición | Crecimiento (h⁻¹) | Resultado |
|---|---|---|
| Aerobiosis | 0,874 | Oxidación completa a CO₂ |
| O₂ = 5 | 0,392 | Acetato, formiato y etanol |
| Anaerobiosis | 0,212 | Fermentación ácido-mixta: acetato 8,5; etanol 8,3; formiato 17,8 |
| Anaerobiosis, sin `PFL` | 0,180 | Etanol 16,6 |
| Sin `PGI` | 0,863 | Desvío por las pentosas fosfato |
| Sin `CS` o sin `ENO` | 0 | Letal |
| Sin `CYTBD` | 0,212 | Igual que anaerobiosis |
| Acetato como fuente de carbono | 0,173 | Solo en aerobiosis |
"""
    )

    concepto('Deleciones génicas',
             '<p>Eliminar un gen fija a cero sus reacciones. Si el modelo no crece, el gen es <b>esencial</b>; si '
             'crece con otros flujos, hay <b>rutas alternativas</b>.</p>')

    nutricion('Relación con la microbiota intestinal',
              '<p>En el colon, sin O₂, <i>E. coli</i> fermenta a acetato, formiato y etanol, que otras especies '
              'pueden consumir. Persephone hace este cálculo con muchas especies a la vez y la dieta como medio.</p>')
