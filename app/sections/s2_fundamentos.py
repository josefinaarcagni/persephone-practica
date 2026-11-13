import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import cobra
from cobra.flux_analysis import flux_variability_analysis
from common import concepto, nutricion

# ---------------------------------------------------------------------------
# Modelo de juguete: una bacteria fermentadora del colon
# ---------------------------------------------------------------------------
REACTIONS = [
    # id, nombre, estequiometría, lb, ub
    ('EX_fibra', 'Entrada de fibra (dieta)', {'fibra': 1}, 0, 10),
    ('EX_glc', 'Entrada de glucosa (dieta)', {'glc': 1}, 0, 10),
    ('HIDR', 'Hidrólisis de fibra', {'fibra': -1, 'glc': 2}, 0, 1000),
    ('GLIC', 'Glucólisis', {'glc': -1, 'pyr': 2, 'atp': 2, 'nadh': 2}, 0, 1000),
    ('PFOR', 'Piruvato → acetil-CoA', {'pyr': -1, 'accoa': 1}, 0, 1000),
    ('ACK', 'Producción de acetato', {'accoa': -1, 'ac': 1, 'atp': 1}, 0, 1000),
    ('BUT', 'Producción de butirato', {'accoa': -2, 'nadh': -2, 'but': 1, 'atp': 1}, 0, 1000),
    ('HYD', 'Hidrogenasa (NADH → H₂)', {'nadh': -1, 'h2': 1}, 0, 1000),
    ('BIOMASA', 'Crecimiento (biomasa)', {'accoa': -2, 'atp': -5, 'nadh': -2}, 0, 1000),
    ('ATPM', 'Mantenimiento celular (ATP)', {'atp': -1}, 1, 1000),
    ('EX_ac', 'Secreción de acetato', {'ac': -1}, 0, 1000),
    ('EX_but', 'Secreción de butirato', {'but': -1}, 0, 1000),
    ('EX_h2', 'Liberación de H₂', {'h2': -1}, 0, 1000),
]
METS = ['fibra', 'glc', 'pyr', 'accoa', 'atp', 'nadh', 'ac', 'but', 'h2']
MET_NAMES = {'fibra': 'Fibra', 'glc': 'Glucosa', 'pyr': 'Piruvato', 'accoa': 'Acetil-CoA',
             'atp': 'ATP', 'nadh': 'NADH', 'ac': 'Acetato', 'but': 'Butirato', 'h2': 'H₂'}

def build_toy(fibra, glc, atpm, enzima, h2=2.0):
    m = cobra.Model('toy')
    mets = {k: cobra.Metabolite(k, name=MET_NAMES[k], compartment='c') for k in METS}
    for rid, name, st_, lb, ub in REACTIONS:
        r = cobra.Reaction(rid, name=name, lower_bound=lb, upper_bound=ub)
        r.add_metabolites({mets[k]: v for k, v in st_.items()})
        m.add_reactions([r])
    m.reactions.EX_fibra.upper_bound = fibra
    m.reactions.EX_glc.upper_bound = glc
    m.reactions.ATPM.lower_bound = atpm
    m.reactions.EX_h2.upper_bound = h2
    if not enzima:
        m.reactions.HIDR.upper_bound = 0
    m.objective = 'BIOMASA'
    return m

def s_matrix():
    S = pd.DataFrame(0, index=[MET_NAMES[m] for m in METS], columns=[r[0] for r in REACTIONS])
    for rid, _, st_, _, _ in REACTIONS:
        for k, v in st_.items():
            S.loc[MET_NAMES[k], rid] = v
    return S

def page():
    st.title('2 · Modelos metabólicos a escala genómica y análisis de flujos')

    st.subheader('2.1 Reconstrucción metabólica y matriz estequiométrica')
    st.markdown(
        """
Una **reconstrucción metabólica a escala genómica** (GEM) reúne todas las reacciones que permite el genoma de un
organismo (≈ 1.000–1.500 en una bacteria intestinal). Se representa como una **matriz estequiométrica S**:
filas = metabolitos, columnas = reacciones, celdas = coeficientes (negativo = consumo, positivo = producción).
"""
    )

    concepto('Modelado basado en restricciones (CBM)',
             '<ol><li><b>Estado estacionario</b>: S·v = 0.</li>'
             '<li><b>Límites de flujo</b>: lb ≤ v ≤ ub (reversibilidad, capacidad, <b>nutrientes de la dieta</b>).</li></ol>'
             '<p>El <b>FBA</b> busca, por programación lineal, los flujos que cumplen ambas restricciones y '
             'maximizan un objetivo, normalmente el <b>crecimiento</b>.</p>')

    st.subheader('2.2 Modelo simplificado de una bacteria fermentadora')
    st.markdown(
        """
Bacteria ficticia (9 metabolitos, 13 reacciones) que toma glucosa de la dieta o **hidroliza fibra**, y destina el
acetil-CoA a **crecer** o **fermentar**:

- **Acetato**: más ATP, pero libera **H₂**, que otros microorganismos deben consumir.
- **Butirato**: menos ATP, pero **reoxida NADH** y no depende del H₂.
"""
    )
    with st.expander('Ver la matriz estequiométrica S del modelo de juguete', expanded=False):
        S = s_matrix()
        st.dataframe(S.style.map(lambda v: 'color: #c62828' if v < 0 else ('color: #2e7d32' if v > 0 else 'color: #bbb')),
                     use_container_width=True)
        st.caption('Filas: metabolitos. Columnas: reacciones. Rojo: consumo; verde: producción. '
                   'Las reacciones EX_ son de intercambio con el medio (dieta / secreción).')

    st.markdown('**Parámetros del modelo.** La solución se recalcula al modificar cualquier parámetro.')
    c1, c2, c3, c4, c5 = st.columns(5)
    fibra = c1.slider('Fibra en la dieta', 0.0, 10.0, 4.0, 0.5, help='Límite superior de EX_fibra (mmol/gPS/h)')
    glc = c2.slider('Glucosa en la dieta', 0.0, 10.0, 1.0, 0.5, help='Límite superior de EX_glc')
    atpm = c3.slider('Mantenimiento (ATP)', 0.0, 20.0, 1.0, 0.5, help='Límite inferior de ATPM')
    h2 = c4.slider('Eliminación de H₂ por la comunidad', 0.0, 12.0, 3.0, 0.5,
                   help='Límite superior de EX_h2: capacidad de otros microorganismos para consumir H₂')
    enzima = c5.toggle('Posee la enzima de hidrólisis de fibra', value=True)

    m = build_toy(fibra, glc, atpm, enzima, h2)
    sol = m.optimize()
    if sol.status != 'optimal':
        st.error('Problema **infactible**: ninguna distribución de flujos cumple las restricciones; '
                 'la bacteria no sobrevive en estas condiciones.')
        return

    fva = flux_variability_analysis(m, ['EX_ac', 'EX_but'], fraction_of_optimum=0.9)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric('Crecimiento óptimo (FBA)', f'{sol.objective_value:.3f}')
    k2.metric('Butirato secretado (FBA)', f'{sol.fluxes["EX_but"]:.2f}')
    k3.metric('Acetato secretado (FBA)', f'{sol.fluxes["EX_ac"]:.2f}')
    k4.metric('Rango de butirato al 90 % del crecimiento (FVA)',
              f'{fva.loc["EX_but", "minimum"]:.2f} – {fva.loc["EX_but", "maximum"]:.2f}')

    # Diagrama de Sankey de los flujos
    node_ids = ['Dieta: fibra', 'Dieta: glucosa', 'Glucosa', 'Piruvato', 'Acetil-CoA', 'Biomasa',
                'Acetato (secretado)', 'Butirato (secretado)']
    f = sol.fluxes
    links = [
        (0, 2, 2 * f['HIDR'], 'Hidrólisis'), (1, 2, f['EX_glc'], 'Captación'),
        (2, 3, f['GLIC'], 'Glucólisis'), (3, 4, f['PFOR'], 'PFOR'),
        (4, 5, 2 * f['BIOMASA'], 'Biomasa'), (4, 6, f['ACK'], 'ACK'), (4, 7, 2 * f['BUT'], 'BUT'),
    ]
    links = [l for l in links if l[2] > 1e-9]
    fig = go.Figure(go.Sankey(
        node=dict(label=node_ids, pad=18, thickness=16,
                  color=['#8d6e63', '#ffb300', '#ffd54f', '#90caf9', '#42a5f5', '#66bb6a', '#ab47bc', '#e53935']),
        link=dict(source=[l[0] for l in links], target=[l[1] for l in links],
                  value=[l[2] for l in links], label=[l[3] for l in links])))
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10), font_size=13)
    st.plotly_chart(fig, use_container_width=True)
    st.caption('Grosor de cada banda ∝ flujo de carbono (en unidades de glucosa/acetil-CoA) en la solución FBA. '
               f'H₂ liberado: {f["EX_h2"]:.2f}.')

    st.markdown(
        """
**Comportamiento del modelo** (resto de parámetros por defecto):

| Cambio | Resultado |
|---|---|
| Glucosa = 0 | La bacteria sigue creciendo a partir de la fibra |
| Glucosa = 0 y sin enzima de hidrólisis | Problema infactible: no hay fuente de carbono |
| Eliminación de H₂ = 10 | Desaparece el butirato; aumentan el acetato y el crecimiento |
| Eliminación de H₂ = 0 | Todo el carbono fermentado se secreta como butirato |
| Mantenimiento = 10 | Menor crecimiento y mayor fermentación |

"""
    )

    with st.expander('Ver todos los flujos de la solución'):
        st.dataframe(pd.DataFrame({'Reacción': [r.name for r in m.reactions], 'Flujo': sol.fluxes.values},
                                  index=sol.fluxes.index).round(3), use_container_width=True)

    concepto('Análisis de variabilidad de flujos (FVA)',
             '<p>Muchas distribuciones de flujo alcanzan el mismo crecimiento. El <b>FVA</b> calcula el <b>mínimo y '
             'el máximo</b> de cada flujo con el objetivo cerca de su óptimo. Persephone lo usa para obtener la '
             '<b>capacidad máxima de secreción y captación</b> de cada metabolito.</p>')

    nutricion('La dieta en el modelo',
              '<p>«Fibra» y «Glucosa» funcionan como una dieta real: cada componente fija el <b>límite de captación</b> '
              'de su reacción de intercambio. Otra dieta, otras restricciones, otras predicciones.</p>')
