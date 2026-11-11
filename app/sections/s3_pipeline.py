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
    st.title('3 · Flujo de trabajo de Persephone')

    st.graphviz_chart(DOT, use_container_width=True)
    st.caption('Flujo de trabajo de Persephone para el análisis de la comunidad microbiana.')

    st.subheader('Módulos')
    tabs = st.tabs(['MARS', 'MgPipe'])
    with tabs[0]:
        st.markdown(
            """
**Pregunta:** ¿qué especies de mi muestra tienen un modelo metabólico disponible, y en qué proporción?

- **Entradas:** tabla de abundancias (lecturas por taxón y muestra) + asignación taxonómica.
- **Qué hace:** normaliza nombres (sinónimos, reclasificaciones, prefijos como *Candidatus*), descarta taxones
  sin resolución de especie, comprueba su presencia en la base de datos elegida y **renormaliza** las
  abundancias relativas solo con las especies modelables.
- **Parámetros clave:** base de datos (`AGORA2`, `APOLLO`, `AGORA2-APOLLO`), umbral de abundancia mínima (`cutoff`).
- **Salidas:** abundancias relativas mapeadas, taxonomía mapeada, métricas de cobertura del mapeo.
"""
        )
    with tabs[1]:
        st.markdown(
            """
**Pregunta:** ¿qué potencial metabólico tiene la comunidad y qué puede producir con una dieta dada?

- **Entradas:** salidas de MARS.
- **Qué hace:**
  1. Calcula la **abundancia de cada reacción** y de cada **subsistema** (ruta) en cada muestra.
  2. Construye un **modelo de comunidad personalizado** por muestra, con compartimentos de dieta,
     lumen intestinal y heces, y la biomasa de cada especie ponderada por su abundancia.
  3. (Opcional) Aplica una **dieta** y calcula por FVA la **secreción y captación netas máximas** de cada metabolito
     (*net maximal production capacity*, NMPC).
- **Parámetros clave:** dieta, solucionador (`glpk`, `cplex`, `gurobi`), número de hilos.
- **Salidas:** `rxnAbundance`, `rxnPresence`, `subsAbundance`, modelos por muestra, `netSecretionFluxes`, `netUptakeFluxes`.
"""
        )
    concepto('Bases de datos de reconstrucciones',
             '<ul><li><b>AGORA2</b>: 7.302 reconstrucciones curadas de cepas de microorganismos intestinales humanos, '
             'incluidas capacidades de degradación de fármacos.</li>'
             '<li><b>APOLLO</b>: reconstrucciones generadas a partir de cientos de miles de genomas ensamblados de '
             'metagenomas (MAGs) de distintas poblaciones y localizaciones corporales.</li>'
             '<li>Persephone utiliza <b>pan-modelos</b> por especie (prefijo <code>pan</code>): la unión de las '
             'reacciones de todas las cepas de una especie, de modo que basta con resolución a nivel de especie.</li></ul>')

    st.subheader('Configuración del flujo completo')
    st.markdown(
        """
El flujo completo se lanza con una única llamada que lee un **fichero de configuración JSON**,
donde se activan o desactivan los módulos y se fijan sus parámetros. Un extracto ilustrativo:
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
    st.caption('Cada clave corresponde a una decisión del análisis: base de datos, dieta, solucionador, módulos '
               'activados y sus parámetros.')
