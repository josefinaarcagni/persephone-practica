import importlib.util
import streamlit as st
from common import concepto, PERSEPHONE_URL


def page():
    st.title('Persephone: modelado metabólico de la microbiota intestinal')
    st.markdown('#### Modelado basado en restricciones y aplicaciones en nutrición')
    st.markdown('**Herramientas avanzadas para el diseño de alimentos y dietas saludables** · 19 de noviembre de 2026')

    st.markdown(
        f"""
**Persephone** es un flujo de trabajo que transforma datos de composición de la microbiota intestinal
(secuenciación del gen 16S rRNA o metagenómica) en predicciones sobre su capacidad metabólica: qué nutrientes
de la dieta consume la comunidad y qué metabolitos produce.
Forma parte de la [COBRA Toolbox]({PERSEPHONE_URL}) (MATLAB).

En esta práctica se utiliza una implementación en Python de Persephone. La práctica cubre sus dos módulos de análisis de la microbiota: **MARS** (armonización
taxonómica) y **MgPipe** (modelos de comunidad y perfiles metabólicos).
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
**Muestras.** Se analizan **5 muestras fecales humanas**, denominadas P1 a P5. Para cada muestra se dispone de la **abundancia relativa de 12 especies bacterianas** intestinales
(en cada muestra suman 1), todas con reconstrucción metabólica en AGORA2-APOLLO:

*Bacteroides pectinophilus*, *Blautia torques*, *Clostridium innocuum*, *Clostridium leptum*,
*Clostridium methylpentosum*, *Erysipelotrichaceae bacterium*, *Eubacterium brachy*, *Eubacterium saphenum*,
*Eubacterium siraeum*, *Eubacterium sulci*, *Ruminococcus lactaris* y *Tyzzerella nexilis*.

Especie dominante en cada muestra:

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
| Abundancias relativas | 12 especies × 5 muestras | 5–8 |
| Tabla de lecturas (`data/raw_counts_demo.tsv`) | Número de lecturas por taxón y muestra (18.766–38.908 lecturas por muestra), con el linaje taxonómico completo (`k__…; s__…`); incluye tres taxones sin reconstrucción metabólica | 5 |
| Reconstrucciones metabólicas de especie | Matriz reacción × especie de AGORA2-APOLLO | 6, 7 |
| Dietas de referencia (5) | Cantidades diarias de ~90 compuestos (mmol/persona/día) | 7, 8 |
| Abundancias de reacciones y subsistemas; modelos de comunidad | Dieta europea media | 6, 7 |
| Perfiles de secreción y captación (NMPC) | 5 dietas × 5 muestras | 7, 8 |
| Intervención dietética | Dieta europea media con la fibra o la proteína multiplicadas por 0–4 | 8 |
| Modelo de *E. coli* | Modelo e_coli_core y mapa del metabolismo central | 3 |
"""
    )

    concepto('Unidades',
             '<p>Las dietas y los perfiles metabólicos se expresan en <b>mmol/persona/día</b>. Los perfiles son '
             '<b>capacidades máximas</b> compatibles con el crecimiento de la comunidad, no concentraciones medidas, '
             'y se interpretan de forma comparativa entre individuos y entre dietas.</p>')
