import streamlit as st
from common import concepto, nutricion

def page():
    st.title('1 · Microbiota, dieta y metabolismo')

    st.subheader('1.1 Función metabólica de la microbiota intestinal')
    st.markdown(
        """
La **fibra**, el **almidón resistente** y la **proteína no digerida** llegan al colon, donde la microbiota los
fermenta y produce metabolitos con efectos sobre el hospedador:
"""
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
**Metabolitos generalmente beneficiosos**
- **Butirato**: energía del colonocito; antiinflamatorio.
- **Propionato**: gluconeogénesis hepática; saciedad.
- **Acetato**: el más abundante; pasa a la circulación.
- **Vitaminas** B y K₂.
"""
        )
    with c2:
        st.markdown(
            """
**Metabolitos potencialmente perjudiciales**
- **H₂S**: genotóxico a concentraciones elevadas.
- **TMA** → **TMAO** hepático: riesgo cardiovascular.
- **p-Cresol, fenol, indol, amonio**: fermentación proteica.
- **Aminas biógenas** (histamina, putrescina).
"""
        )

    nutricion('Relación con la nutrición',
              '<p>La dieta determina <b>qué sustratos</b> llegan al colon; la microbiota, <b>cómo se transforman</b>. '
              'Con la misma dieta, dos personas pueden producir cantidades muy distintas de butirato.</p>')

    st.subheader('1.2 De la composición taxonómica a la función')
    st.markdown(
        """
La secuenciación (16S rRNA o metagenómica) indica **qué taxones hay y en qué proporción**, no **qué hacen**:

| Aproximación | Qué ofrece | Limitación |
|---|---|---|
| Inferencia funcional (p. ej. PICRUSt) | Abundancia predicha de genes/rutas | No considera la dieta ni los flujos reales |
| Metatranscriptómica / metabolómica | Medida experimental | Coste elevado; no explica el mecanismo |
| **Modelado basado en restricciones** (Persephone) | **Flujos metabólicos** condicionados a la dieta, por individuo | Depende de la calidad de las reconstrucciones |
"""
    )

    concepto('Fundamento de Persephone',
             '<p>Persephone combina las <b>reconstrucciones metabólicas</b> (AGORA2, APOLLO) de las especies de cada '
             'muestra, ponderadas por su abundancia, en un <b>modelo de comunidad</b>; le aplica una <b>dieta</b> y '
             'calcula qué metabolitos puede producir y consumir.</p>')
