# BI_REPRODUTIVO.py


import streamlit as st
import pandas as pd
import plotly.express as px
from glob import glob

st.set_page_config(
    page_title="BI Reprodutivo",
    page_icon="🐄",
    layout="wide"
)

# =========================
# FUNÇÕES
# =========================

@st.cache_data

def carregar_diagnostico():
    arquivos = glob("DIAGNOSTICOS/*.xls*")

    if not arquivos:
        st.error("Nenhum arquivo encontrado na pasta DIAGNOSTICOS")
        st.stop()

    df = pd.read_excel(arquivos[0])

    # Descobrir coluna de status
    if 'Estado Diagnóstico' in df.columns:
        col_status = 'Estado Diagnóstico'
    else:
        col_status = 'Estado'

    df['STATUS'] = (
        df[col_status]
        .fillna('')
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df['ABORTO'] = (
        df['Tipo Aborto']
        .fillna('')
        .astype(str)
        .str.upper()
        .str.contains('ABORTO')
    )

    df['PRENHA'] = df['STATUS'].str.contains('PREN', na=False)
    df['VAZIA'] = df['STATUS'].str.contains('VAZ', na=False)

    return df


@st.cache_data

def carregar_medicao():
    arquivos = glob("MEDICOES/*.xls*")

    if not arquivos:
        st.error("Nenhum arquivo encontrado na pasta MEDICOES")
        st.stop()

    df = pd.read_excel(arquivos[0])

    return df


@st.cache_data

def carregar_grupo():
    arquivos = glob("GRUPOS/*.xls*")

    if not arquivos:
        st.error("Nenhum arquivo encontrado na pasta GRUPOS")
        st.stop()

    df = pd.read_excel(arquivos[0])

    return df


# =========================
# CARREGAR DADOS
# =========================


diag_df = carregar_diagnostico()
med_df = carregar_medicao()
grupo_df = carregar_grupo()

# =========================
# PADRONIZAR SIGLA USUAL
# =========================

diag_df['Sigla Usual'] = (
    diag_df['Sigla Usual']
    .astype(str)
    .str.strip()
    .str.upper()
)

grupo_df['Sigla Usual'] = (
    grupo_df['Sigla Usual']
    .astype(str)
    .str.strip()
    .str.upper()
)

med_df['Sigla Usual'] = (
    med_df['Sigla Usual']
    .astype(str)
    .str.strip()
    .str.upper()
)

# =========================
# PADRONIZAR SIGLA
# =========================


diag_df['Sigla Usual'] = diag_df['Sigla Usual'].astype(str).str.strip()
med_df['Sigla Usual'] = med_df['Sigla Usual'].astype(str).str.strip()
grupo_df['Sigla Usual'] = grupo_df['Sigla Usual'].astype(str).str.strip()

# =========================
# ECC
# =========================

med_df = med_df[['Sigla Usual', 'Valor']].copy()
med_df.rename(columns={'Valor': 'ECC'}, inplace=True)

# =========================
# GRUPO MANEJO
# =========================

if 'Grupo Manejo' in grupo_df.columns:
    grupo_col = 'Grupo Manejo'
else:
    grupo_col = 'Descrição'

grupo_df = grupo_df[['Sigla Usual', grupo_col]].copy()
grupo_df.rename(columns={grupo_col: 'Grupo Manejo'}, inplace=True)

# =========================
# MERGES
# =========================


diag_df = diag_df.merge(
    med_df,
    on='Sigla Usual',
    how='left'
)


diag_df = diag_df.merge(
    grupo_df,
    on='Sigla Usual',
    how='left'
)

# =========================
# DASHBOARD
# =========================

st.title("🐄 BI REPRODUTIVO")
st.markdown("### Dashboard Interativo de Reprodução")

# =========================
# FILTROS
# =========================

st.sidebar.header("Filtros")

lista_grupos = sorted(
    diag_df['Grupo Manejo']
    .dropna()
    .astype(str)
    .unique()
)

filtro_grupo = st.sidebar.multiselect(
    "Grupo Manejo",
    lista_grupos,
    default=lista_grupos
)

lista_ecc = sorted(
    diag_df['ECC']
    .dropna()
    .astype(str)
    .unique()
)

filtro_ecc = st.sidebar.multiselect(
    "ECC",
    lista_ecc,
    default=lista_ecc
)

# =========================
# FILTRAR
# =========================


df = diag_df.copy()

if filtro_grupo:
    df = df[df['Grupo Manejo'].astype(str).isin(filtro_grupo)]

if filtro_ecc:
    df = df[df['ECC'].astype(str).isin(filtro_ecc)]

# =========================
# KPIs
# =========================


total = len(df)
prenhas = int(df['PRENHA'].sum())
vazias = int(df['VAZIA'].sum())
abortos = int(df['ABORTO'].sum())

if total > 0:
    taxa = round((prenhas / total) * 100, 1)
else:
    taxa = 0

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total", total)
col2.metric("Prenhas", prenhas)
col3.metric("Vazias", vazias)
col4.metric("Abortos", abortos)
col5.metric("Taxa Prenhez", f"{taxa}%")

# =========================
# RESUMO POR ECC
# =========================


ecc_resumo = df.groupby('ECC').agg(
    Prenhas=('PRENHA', 'sum'),
    Vazias=('VAZIA', 'sum'),
    Abortos=('ABORTO', 'sum')
).reset_index()

fig_ecc = px.bar(
    ecc_resumo,
    x='ECC',
    y=['Prenhas', 'Vazias', 'Abortos'],
    barmode='group',
    title='Resultados por ECC'
)

# =========================
# RESUMO POR GRUPO
# =========================


grupo_resumo = df.groupby('Grupo Manejo').agg(
    Prenhas=('PRENHA', 'sum'),
    Vazias=('VAZIA', 'sum'),
    Abortos=('ABORTO', 'sum')
).reset_index()

fig_grupo = px.bar(
    grupo_resumo,
    x='Grupo Manejo',
    y=['Prenhas', 'Vazias', 'Abortos'],
    barmode='group',
    title='Resultados por Grupo Manejo'
)

# =========================
# GRÁFICOS
# =========================

colA, colB = st.columns(2)

with colA:
    st.plotly_chart(fig_ecc, use_container_width=True)

with colB:
    st.plotly_chart(fig_grupo, use_container_width=True)

# =========================
# TABELA
# =========================

st.subheader("Tabela Completa")

mostrar = [
    'Sigla Usual',
    'STATUS',
    'ECC',
    'Grupo Manejo'
]

st.dataframe(
    df[mostrar],
    use_container_width=True,
    height=500
)

# =========================
# DOWNLOAD CSV
# =========================

csv = df.to_csv(index=False).encode('utf-8')

st.download_button(
    "⬇ Baixar CSV",
    csv,
    "bi_reprodutivo.csv",
    "text/csv"
)

# =========================
# PDF
# =========================

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO


def gerar_pdf(total, prenhas, vazias, abortos, taxa):
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elementos = []

    titulo = Paragraph("BI REPRODUTIVO", styles['Title'])
    elementos.append(titulo)
    elementos.append(Spacer(1, 20))

    texto = f"""
    <b>Total de Animais:</b> {total}<br/>
    <b>Prenhas:</b> {prenhas}<br/>
    <b>Vazias:</b> {vazias}<br/>
    <b>Abortos:</b> {abortos}<br/>
    <b>Taxa de Prenhez:</b> {taxa}%<br/>
    """

    elementos.append(Paragraph(texto, styles['BodyText']))

    doc.build(elementos)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf


pdf = gerar_pdf(total, prenhas, vazias, abortos, taxa)

st.download_button(
    label="📄 Baixar PDF",
    data=pdf,
    file_name="relatorio_bi_reprodutivo.pdf",
    mime="application/pdf"
)


