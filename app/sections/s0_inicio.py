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
**Muestras.** El conjunto de ejemplo procede de los ficheros de prueba de la implementación en Python
(`counts.tsv`, `taxa.tsv`): **5 muestras fecales humanas** (`CSM5MCXD`, `CSM5MCY2`, `CSM67U9J`, `CSM67UAW`,
`CSM67UB9`) con las abundancias relativas de **12 especies bacterianas** ya mapeadas a la base de datos
AGORA2-APOLLO (en cada muestra suman 1). La comunidad está reducida a 12 especies para que los cálculos sean
abordables; un estudio real incluye cientos de especies por muestra, pero el procedimiento y el tipo de resultados
son los mismos.
"""
    )
    st.markdown(
        """
| Datos | Procedencia | Bloques |
|---|---|---|
| Abundancias relativas de 12 especies × 5 muestras | Ficheros de prueba de la implementación en Python de Persephone | 5–8 |
| Tabla de lecturas con linaje taxonómico completo (`data/raw_counts_demo.tsv`) | Construida para esta práctica a partir de la anterior: lecturas = abundancia relativa × profundidad de secuenciación asignada (18.766–38.908 lecturas por muestra), con linajes en formato SILVA (`k__…; s__…`) y tres ASV añadidos que ilustran casos no modelables | 5 |
| Reconstrucciones metabólicas de especie (pan-modelos) | AGORA2 (7.302 cepas) y APOLLO (MAGs), distribuidas con el paquete como matriz reacción × especie | 6, 7 |
| Dietas de referencia (5) | Virtual Metabolic Human (VMH), *Diet Designer*: cantidades diarias de ~90 compuestos (mmol/persona/día) | 7, 8 |
| Abundancias de reacciones/subsistemas y modelos de comunidad | Calculados para esta práctica con MgPipe (dieta europea media, solucionador GLPK) | 6, 7 |
| Perfiles de secreción y captación (NMPC) | Calculados para esta práctica con MgPipe para las 5 dietas y las 5 muestras (FVA, GLPK) | 7, 8 |
| Intervención dietética | Calculada para esta práctica: dieta europea media con la fibra o la proteína multiplicadas por 0–4 | 8 |
| Modelo e_coli_core y mapa «Core metabolism» | BiGG Models (distribuido con COBRApy) y Escher | 3 |
"""
    )

    concepto('Unidades',
             '<p>Las dietas y los perfiles metabólicos se expresan en <b>mmol/persona/día</b>. Los perfiles son '
             '<b>capacidades máximas</b> compatibles con el crecimiento de la comunidad, no concentraciones medidas, '
             'y se interpretan de forma comparativa entre individuos y entre dietas.</p>')
