"""Práctica guiada de q2-Persephone (Streamlit).

Lanzar con:  bash run_app.sh   (o: streamlit run app/app.py)
"""
import os
import sys
import warnings

import streamlit as st

warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, 'sections')]

from common import inject_css  # noqa: E402
import s0_inicio, s1_contexto, s2_fundamentos, s3_pipeline, s4_mars  # noqa: E402
import s5_reacciones, s6_comunidad, s7_nutricion, s9_discusion  # noqa: E402

st.set_page_config(page_title='Práctica Persephone', layout='wide')
inject_css()

pages = [
    st.Page(s0_inicio.page, title='Presentación y datos', url_path='inicio', default=True),
    st.Page(s1_contexto.page, title='1 · Microbiota, dieta y metabolismo', url_path='contexto'),
    st.Page(s2_fundamentos.page, title='2 · Modelos metabólicos y análisis de flujos', url_path='fundamentos'),
    st.Page(s3_pipeline.page, title='3 · Flujo de trabajo de Persephone', url_path='pipeline'),
    st.Page(s4_mars.page, title='4 · Datos de entrada y MARS', url_path='mars'),
    st.Page(s5_reacciones.page, title='5 · MgPipe: reacciones y subsistemas', url_path='reacciones'),
    st.Page(s6_comunidad.page, title='6 · MgPipe: comunidad y perfiles', url_path='comunidad'),
    st.Page(s7_nutricion.page, title='7 · Aplicaciones en nutrición', url_path='nutricion'),
    st.Page(s9_discusion.page, title='8 · Discusión y cuestionario', url_path='discusion'),
]

with st.sidebar:
    st.markdown('### Persephone')
    st.caption('Herramientas avanzadas para el diseño de alimentos y dietas saludables')
    st.caption('19 de noviembre de 2026')

nav = st.navigation(pages)
nav.run()
