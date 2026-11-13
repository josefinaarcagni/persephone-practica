import streamlit as st
from common import concepto

DOT = r"""
digraph G {
  rankdir=LR; bgcolor="transparent";
  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, color="#555555"];
  edge [color="#777777", fontname="Helvetica", fontsize=9];

  seq   [label="Secuenciación\n16S rRNA / metagenómica", fillcolor="#eeeeee"];
  mars  [label="MARS\nArmonización taxonómica\ny mapeo a AGORA2/APOLLO", fillcolor="#bbdefb"];
  mg1   [label="MgPipe (I)\nAbundancia de reacciones\ny subsistemas", fillcolor="#c8e6c9"];
  mg2   [label="MgPipe (II)\nModelos de comunidad\npersonalizados", fillcolor="#c8e6c9"];
  prof  [label="Perfiles metabólicos\n(captación / secreción\nmáxima por FVA)", fillcolor="#a5d6a7"];
  diet  [label="Dieta\n(EU, fibra, proteína...)", shape=ellipse, fillcolor="#f8bbd0"];
  stat  [label="Análisis estadístico\ne interpretación", fillcolor="#e1bee7"];

  seq -> mars [label="tabla de abundancias\n+ taxonomía"];
  mars -> mg1 [label="abundancias\nmapeadas"];
  mars -> mg2;
  mg2 -> prof;
  diet -> prof;
  mg1 -> stat;
  prof -> stat;
}
"""

def page():
    st.title('4 · Flujo de trabajo de Persephone')

    st.graphviz_chart(DOT, use_container_width=True)
    st.caption('Flujo de trabajo de Persephone para el análisis de la comunidad microbiana.')

    st.subheader('Módulos')
    tabs = st.tabs(['MARS', 'MgPipe'])
    with tabs[0]:
        st.markdown(
            """
**¿Qué especies tienen modelo metabólico y en qué proporción?**

- **Entrada:** lecturas por taxón y muestra, con su taxonomía.
- **Proceso:** armoniza nombres, descarta taxones sin especie, busca cada especie en la base de datos y
  **renormaliza** las abundancias con las especies modelables.
- **Parámetros:** base de datos, umbral de abundancia (`cutoff`).
- **Salida:** abundancias relativas mapeadas y métricas de cobertura.
"""
        )
    with tabs[1]:
        st.markdown(
            """
**¿Qué puede producir la comunidad con una dieta dada?**

- **Entrada:** salida de MARS.
- **Proceso:**
  1. Abundancia de cada **reacción** y **subsistema** por muestra.
  2. **Modelo de comunidad** por muestra (dieta → lumen → heces; biomasa ponderada por abundancia).
  3. Con una **dieta**, **secreción y captación netas máximas** de cada metabolito por FVA (NMPC).
- **Parámetros:** dieta, solucionador.
- **Salida:** abundancias de reacciones y subsistemas, modelos, perfiles NMPC.
"""
        )
    concepto('Bases de datos de reconstrucciones',
             '<ul><li><b>AGORA2</b>: 7.302 reconstrucciones curadas de cepas intestinales humanas.</li>'
             '<li><b>APOLLO</b>: reconstrucciones de genomas ensamblados de metagenomas (MAGs).</li>'
             '<li><b>Pan-modelos</b> (prefijo <code>pan</code>): unión de las reacciones de todas las cepas de una especie.</li></ul>')

    st.subheader('Configuración del flujo completo')
    st.markdown(
        """
El flujo completo se lanza con un **fichero de configuración JSON** que activa los módulos y fija sus parámetros:
"""
    )
    st.code(
        """{
  "general_metadataPath": "metadata.tsv",
  "general_database": "AGORA2-APOLLO",
  "general_diet": "EUAverageDiet",
  "general_solver": "glpk",
  "mars_flagMars": true,      "mars_cutoff": 0.000001,
  "micro_flagMicro": true,    "micro_computeProfiles": true,
  "results_path": "resultados/"
}""", language='json')
