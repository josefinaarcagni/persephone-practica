import importlib.util
import streamlit as st
from common import concepto, PERSEPHONE_URL


def page():
    st.title('Persephone: modelado metabólico de la microbiota intestinal')
    st.markdown('#### Modelado basado en restricciones y aplicaciones en nutrición')
    st.markdown('**Herramientas avanzadas para el diseño de alimentos y dietas saludables** · 19 de noviembre de 2026')

    st.markdown(
        f"""
**Persephone** ([COBRA Toolbox]({PERSEPHONE_URL})) convierte la composición de la microbiota intestinal en
predicciones de su capacidad metabólica: qué nutrientes consume y qué metabolitos produce. Se usan sus módulos
**MARS** (armonización taxonómica) y **MgPipe** (modelos de comunidad y perfiles metabólicos).
"""
    )

    st.subheader('Contenido')
    mars_calc = 'En directo' if importlib.util.find_spec('persephone') else 'Precalculado'
    st.markdown(
        f"""
| Bloque | Contenido | Cálculo |
|---|---|---|
| 1 | Microbiota, dieta y metabolismo | — |
| 2 | Modelos metabólicos, FBA y FVA | En directo (modelo simplificado) |
| 3 | *Escherichia coli*: matriz S, intercambios, FBA y mapa metabólico | En directo |
| 4 | Flujo de trabajo de Persephone | — |
| 5 | Datos de entrada y armonización taxonómica (MARS) | {mars_calc} |
| 6 | MgPipe: abundancia de reacciones y subsistemas | Precalculado |
| 7 | MgPipe: modelos de comunidad y perfiles metabólicos | Precalculado |
| 8 | Aplicaciones en nutrición: comparación de dietas e intervención dietética | Precalculado |
| 9 | Discusión y cuestionario | — |
"""
    )

    st.subheader('Datos utilizados')
    st.markdown(
        """
**5 muestras fecales humanas** (P1–P5) con la abundancia relativa de **12 especies bacterianas** intestinales.

| Muestra | Especie dominante | Abundancia relativa |
|---|---|---|
| P1 | *Erysipelotrichaceae bacterium* | 59 % |
| P2 | *Eubacterium siraeum* | 79 % |
| P3 | *Erysipelotrichaceae bacterium* | 67 % |
| P4 | *Clostridium innocuum* | 41 % |
| P5 | *Blautia torques* | 79 % |
"""
    )
    st.markdown(
        """
| Datos | Contenido | Bloques |
|---|---|---|
| Modelo de *E. coli* | e_coli_core y mapa del metabolismo central | 3 |
| Tabla de lecturas | 15 taxones × 5 muestras, con linaje completo | 5 |
| Abundancias relativas | 12 especies × 5 muestras | 5, 6 |
| Reconstrucciones metabólicas | Matriz reacción × especie (AGORA2-APOLLO) | 6, 7 |
| Dietas (5) | Menú de un día y ~90 compuestos (mmol/persona/día) | 8 |
| Modelos de comunidad y perfiles | P1, P2, P4, P5 × 5 dietas | 7, 8 |
| Intervención dietética | Fibra o proteína × 0–4 | 8 |
"""
    )

    concepto('Unidades',
             '<p>Dietas y perfiles en <b>mmol/persona/día</b>. Los perfiles son <b>capacidades máximas</b>, no '
             'concentraciones medidas: se comparan entre individuos y dietas.</p>')
