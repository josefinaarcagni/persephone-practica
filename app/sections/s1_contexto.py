import streamlit as st
from common import concepto, nutricion

def page():
    st.title('1 · Microbiota, dieta y metabolismo')

    st.subheader('1.1 Función metabólica de la microbiota intestinal')
    st.markdown(
        """
El colon humano alberga del orden de 10¹³ células bacterianas pertenecientes a cientos de especies.
Una parte importante de los componentes de la dieta —en particular la **fibra dietética**, el
**almidón resistente** y las **proteínas no digeridas**— no se absorbe en el intestino delgado y llega
al colon, donde es fermentada por la microbiota. Como resultado se producen metabolitos con efectos
directos sobre el hospedador:
"""
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
**Metabolitos generalmente beneficiosos**
- **Butirato**: principal fuente de energía del colonocito; antiinflamatorio; refuerza la barrera intestinal.
- **Propionato**: sustrato gluconeogénico hepático; implicado en saciedad.
- **Acetato**: el más abundante; llega a la circulación sistémica.
- **Vitaminas** del grupo B y K₂.
"""
        )
    with c2:
        st.markdown(
            """
**Metabolitos potencialmente perjudiciales**
- **Sulfuro de hidrógeno (H₂S)**: genotóxico en concentraciones elevadas.
- **Trimetilamina (TMA)**: se oxida en el hígado a **TMAO**, asociado a riesgo cardiovascular.
- **p-Cresol, fenol, indol, amonio**: productos de la fermentación proteica.
- **Aminas biógenas** (histamina, putrescina).
"""
        )

    nutricion('Relación con la nutrición',
              '<p>La dieta determina <b>qué sustratos</b> llegan al colon y la microbiota determina <b>cómo se '
              'transforman</b>. Dos personas con la misma dieta pueden producir cantidades muy distintas de '
              'butirato si su microbiota difiere; esta variabilidad es la base de la <b>nutrición de precisión</b>.</p>')

    st.subheader('1.2 De la composición taxonómica a la función')
    st.markdown(
        """
La secuenciación del gen 16S rRNA informa de **qué taxones están presentes y en qué proporción**, pero no
de **qué funciones metabólicas** realizan. Las principales aproximaciones para inferir la función son:

| Aproximación | Qué ofrece | Limitación |
|---|---|---|
| Inferencia funcional (p. ej. PICRUSt) | Abundancia predicha de genes/rutas | No considera la dieta ni los flujos reales |
| Metatranscriptómica / metabolómica | Medida experimental | Coste elevado; no explica el mecanismo |
| **Modelado basado en restricciones** (Persephone) | **Flujos metabólicos** condicionados a la dieta, por individuo | Depende de la calidad de las reconstrucciones |
"""
    )

    concepto('Fundamento de Persephone',
             '<p>Para cada especie detectada existe una <b>reconstrucción metabólica</b> curada (bases de datos '
             '<b>AGORA2</b> y <b>APOLLO</b>). Persephone combina las reconstrucciones de las especies presentes en '
             'cada muestra, ponderadas por su abundancia, en un <b>modelo de comunidad personalizado</b>; le aplica '
             'una <b>dieta</b> y calcula qué metabolitos puede producir y consumir esa comunidad.</p>')
