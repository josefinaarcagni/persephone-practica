import streamlit as st
from common import PERSEPHONE_URL

QUIZ = [
    ('¿Qué representa la restricción S·v = 0 en un modelo metabólico?',
     ['Que todas las reacciones tienen flujo cero',
      'Que los metabolitos internos no se acumulan ni se agotan (estado estacionario)',
      'Que la célula no crece',
      'Que la dieta no aporta nutrientes'],
     1, 'S·v = 0 es el balance de masas en estado estacionario: lo que se produce de cada metabolito interno se consume.'),
    ('¿Cuál es la función principal de MARS?',
     ['Calcular flujos metabólicos',
      'Armonizar la taxonomía y mapear las especies a las bases de datos de reconstrucciones',
      'Construir la dieta de cada individuo',
      'Diseñar dietas'],
     1, 'MARS traduce la taxonomía de la muestra a la nomenclatura de AGORA2/APOLLO y renormaliza las abundancias.'),
    ('La abundancia de una reacción calculada por MgPipe...',
     ['Depende de la dieta aplicada',
      'Es la fracción de la comunidad que posee los genes para catalizarla',
      'Es el flujo real medido en heces',
      'Solo puede valer 0 o 1'],
     1, 'Es un indicador de potencial genético, independiente de la dieta.'),
    ('¿Cómo se introduce una dieta en un modelo basado en restricciones?',
     ['Como límites de captación en las reacciones de intercambio de cada nutriente',
      'Cambiando la matriz estequiométrica',
      'Eliminando especies de la comunidad',
      'Modificando la función objetivo'],
     0, 'Cada componente de la dieta fija la cantidad máxima de ese metabolito que puede entrar al sistema.'),
    ('¿Por qué Persephone utiliza FVA para los perfiles de secreción?',
     ['Porque es más rápido que FBA',
      'Porque la solución del FBA no es única y el FVA da la capacidad máxima de cada metabolito manteniendo el crecimiento',
      'Porque no requiere dieta',
      'Porque mide metabolitos experimentalmente'],
     1, 'El FVA calcula el rango de flujo posible de cada reacción; el máximo de secreción neta es la NMPC.'),
    ('Dos personas siguen la misma dieta rica en fibra, pero el modelo predice mucho más butirato en una de ellas. La explicación más directa es...',
     ['Un error del solucionador',
      'Diferencias en su microbiota (abundancia de productores de butirato)',
      'Que la dieta no influye en el butirato',
      'Diferencias en su edad'],
     1, 'Con la misma dieta, la diferencia procede de la comunidad.'),
    ('En una muestra, la capacidad de producir butirato no cambia al multiplicar por cuatro la fibra de la dieta. La explicación más probable es...',
     ['La fibra no se fermenta en el colon',
      'La producción está limitada por la baja abundancia de especies productoras (restricciones de acoplamiento)',
      'El modelo no incluye la fibra',
      'El solucionador no ha convergido'],
     1, 'Sin productores abundantes, más sustrato no aumenta la producción.'),
]

def page():
    st.title('9 · Discusión y cuestionario')

    st.subheader('9.1 Cuestiones para la discusión')
    st.markdown(
        """
1. **Validación.** ¿Qué datos experimentales usaría para validar las capacidades predichas?
2. **Cobertura.** Si MARS mapea solo el 60 % de las lecturas, ¿cómo afecta a la interpretación?
3. **Dieta.** ¿Cómo construiría una dieta personalizada a partir de un registro dietético?
4. **Causalidad.** Si los casos tienen menor capacidad de producir butirato, ¿es el butirato la causa?
5. **Aplicación.** ¿Cómo usaría Persephone para seleccionar a quién beneficiaría un suplemento de fibra?
"""
    )

    st.subheader('9.2 Cuestionario')
    answers = []
    for i, (q, opts, _, _) in enumerate(QUIZ):
        answers.append(st.radio(f'**{i + 1}.** {q}', opts, index=None, key=f'quiz_{i}'))
    if st.button('Corregir', type='primary'):
        score = 0
        for i, ((q, opts, ok, expl), a) in enumerate(zip(QUIZ, answers)):
            if a is None:
                st.warning(f'Pregunta {i + 1}: sin responder. {expl}')
            elif opts.index(a) == ok:
                score += 1
                st.success(f'Pregunta {i + 1}: correcta. {expl}')
            else:
                st.error(f'Pregunta {i + 1}: incorrecta. Respuesta correcta: «{opts[ok]}». {expl}')
        st.metric('Puntuación', f'{score} / {len(QUIZ)}')

    st.subheader('9.3 Limitaciones del modelado')
    st.markdown(
        """
- **Reconstrucciones**: pueden faltar o sobrar reacciones.
- **Resolución**: pan-modelos de especie, no cepas.
- **Estado estacionario**: sin dinámica ni regulación.
- **Capacidades máximas**: cotas superiores, no valores medidos.
- **Dietas estándar**: no reflejan la dieta ni la digestión de cada persona.
"""
    )

    st.subheader('9.4 Referencias')
    st.markdown(
        f"""
- Persephone (COBRA Toolbox): [código fuente]({PERSEPHONE_URL}).
- Virtual Metabolic Human (VMH): [vmh.life](https://www.vmh.life).
- Heinken A. *et al.* (2023). Genome-scale metabolic reconstruction of 7,302 human microorganisms for personalized medicine (AGORA2). *Nature Biotechnology*.
- Orth J. D., Thiele I., Palsson B. Ø. (2010). What is flux balance analysis? *Nature Biotechnology*.
- Orth J. D., Fleming R. M. T., Palsson B. Ø. (2010). Reconstruction and use of microbial metabolic networks: the core *Escherichia coli* metabolic model as an educational guide. *EcoSal Plus*.
- King Z. A. *et al.* (2015). Escher: a web application for building, sharing, and embedding data-rich visualizations of biological pathways. *PLOS Computational Biology*.
"""
    )
