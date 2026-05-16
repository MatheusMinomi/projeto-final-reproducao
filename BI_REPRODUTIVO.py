import streamlit as st
import pandas as pd
import plotly.express as px
from glob import glob

# ====================================
# CONFIGURAÇÃO
# ====================================

st.set_page_config(
    page_title="BI Reprodutivo",
    page_icon="🐄",
    layout="wide"
)

st.title("🐄 BI REPRODUTIVO")
st.subheader("Dashboard Interativo de Reprodução")

# ====================================
# LEITURA DOS ARQUIVOS
# ====================================

@st.cache_data
def carregar_arquivos():

    # -------------------------
    # DIAGNOSTICOS
    # -------------------------

    arquivos_diag = glob("DIAGNOSTICOS/*.xls*")

    lista_diag = []

    for arq in arquivos_diag:

        df = pd.read_excel(arq)

        df.columns = df.columns.str.strip()

        # Corrigir nome da coluna
        if 'Estado Diagnóstico' in df.columns:
            df.rename(
                columns={'Estado Diagnóstico': 'Estado'},
                inplace=True
            )

        lista_diag.append(df)

    diag_df = pd.concat(lista_diag, ignore_index=True)

    # -------------------------
    # MEDICOES
    # -------------------------

    arquivos_med = glob("MEDICOES/*.xls*")

    lista_med = []

    for arq in arquivos_med:

        df = pd.read_excel(arq)

        df.columns = df.columns.str.strip()

        lista_med.append(df)

    med_df = pd.concat(lista_med, ignore_index=True)

    # -------------------------
    # GRUPOS
    # -------------------------

    arquivos_grupo = glob("GRUPOS/*.xls*")

    lista_grupo = []

    for arq in arquivos_grupo:

        df = pd.read_excel(arq)

        df.columns = df.columns.str.strip()

        # Corrigir nome da coluna grupo
        if 'Descrição' in df.columns:
            df.rename(
                columns={'Descrição': 'Grupo Manejo'},
                inplace=True
            )

        lista_grupo.append(df)

    grupo_df = pd.concat(lista_grupo, ignore_index=True)

    return diag_df, med_df, grupo_df


diag_df, med_df, grupo_df = carregar_arquivos()

# ====================================
# PADRONIZAR SIGLA
# ====================================

diag_df['Sigla Usual'] = (
    diag_df['Sigla Usual']
    .fillna('')
    .astype(str)
    .str.strip()
    .str.upper()
)

med_df['Sigla Usual'] = (
    med_df['Sigla Usual']
    .fillna('')
    .astype(str)
    .str.strip()
    .str.upper()
)

grupo_df['Sigla Usual'] = (
    grupo_df['Sigla Usual']
    .fillna('')
    .astype(str)
    .str.strip()
    .str.upper()
)

# ====================================
# ECC
# ====================================

if 'Valor' in med_df.columns:

    med_df = med_df[
        ['Sigla Usual', 'Valor']
    ]

    diag_df = diag_df.merge(
        med_df,
        on='Sigla Usual',
        how='left'
    )

    diag_df.rename(
        columns={'Valor': 'ECC'},
        inplace=True
    )

# ====================================
# GRUPO MANEJO
# ====================================

if 'Grupo Manejo' in grupo_df.columns:
    col_grupo = 'Grupo Manejo'

elif 'Descrição' in grupo_df.columns:
    col_grupo = 'Descrição'

else:
    col_grupo = None

if col_grupo:

    grupo_df = grupo_df[
        ['Sigla Usual', col_grupo]
    ]

    diag_df = diag_df.merge(
        grupo_df,
        on='Sigla Usual',
        how='left'
    )

    diag_df.rename(
        columns={col_grupo: 'Grupo Manejo'},
        inplace=True
    )

# ====================================
# STATUS REPRODUTIVO
# ====================================

diag_df['Estado'] = (
    diag_df['Estado']
    .fillna('')
    .astype(str)
    .str.upper()
)

diag_df['Tipo Aborto'] = (
    diag_df['Tipo Aborto']
    .fillna('')
    .astype(str)
    .str.upper()
)

diag_df['PRENHA'] = (
    diag_df['Estado']
    .str.contains('PREN', na=False)
)

diag_df['VAZIA'] = (
    diag_df['Estado']
    .str.contains('VAZ', na=False)
)

diag_df['ABORTO'] = (
    diag_df['Tipo Aborto']
    .str.contains('ABORT', na=False)
)

# ====================================
# DATAFRAME PRINCIPAL
# ====================================

df = diag_df.copy()

# ECC
if 'ECC' not in df.columns:
    df['ECC'] = 'SEM ECC'

df['ECC'] = (
    df['ECC']
    .fillna('SEM ECC')
    .astype(str)
)

# Grupo Manejo
if 'Grupo Manejo' not in df.columns:
    df['Grupo Manejo'] = 'SEM GRUPO'

df['Grupo Manejo'] = (
    df['Grupo Manejo']
    .fillna('SEM GRUPO')
    .astype(str)
)

# ====================================
# FILTROS
# ====================================

st.sidebar.header("Filtros")

lista_grupos = sorted(
    df['Grupo Manejo']
    .unique()
)

filtro_grupo = st.sidebar.multiselect(
    "Grupo Manejo",
    lista_grupos,
    default=lista_grupos
)

lista_ecc = sorted(
    df['ECC']
    .unique()
)

filtro_ecc = st.sidebar.multiselect(
    "ECC",
    lista_ecc,
    default=lista_ecc
)

# Aplicar filtros
if filtro_grupo:
    df = df[
        df['Grupo Manejo'].isin(filtro_grupo)
    ]

if filtro_ecc:
    df = df[
        df['ECC'].isin(filtro_ecc)
    ]

# ====================================
# KPIs
# ====================================

total = len(df)

prenha = int(df['PRENHA'].sum())

vazia = int(df['VAZIA'].sum())

aborto = int(df['ABORTO'].sum())

taxa = round(
    (prenha / total) * 100,
    1
) if total > 0 else 0

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total", total)
c2.metric("Prenhas", prenha)
c3.metric("Vazias", vazia)
c4.metric("Taxa Prenhez %", taxa)

# ====================================
# RESUMO POR GRUPO
# ====================================

st.subheader("Resumo por Grupo Manejo")

resumo_grupo = (
    df.groupby('Grupo Manejo')
    .agg({
        'PRENHA': 'sum',
        'VAZIA': 'sum',
        'ABORTO': 'sum'
    })
    .reset_index()
)

resumo_grupo['TOTAL'] = (
    resumo_grupo['PRENHA']
    + resumo_grupo['VAZIA']
    + resumo_grupo['ABORTO']
)

st.dataframe(
    resumo_grupo,
    use_container_width=True
)

# Gráfico grupo

fig_grupo = px.bar(
    resumo_grupo,
    x='Grupo Manejo',
    y=['PRENHA', 'VAZIA', 'ABORTO'],
    barmode='group',
    title='Resultado por Grupo Manejo'
)

st.plotly_chart(
    fig_grupo,
    use_container_width=True
)

# ====================================
# RESUMO POR ECC
# ====================================

st.subheader("Resumo por ECC")

resumo_ecc = (
    df.groupby('ECC')
    .agg({
        'PRENHA': 'sum',
        'VAZIA': 'sum',
        'ABORTO': 'sum'
    })
    .reset_index()
)

resumo_ecc['TOTAL'] = (
    resumo_ecc['PRENHA']
    + resumo_ecc['VAZIA']
    + resumo_ecc['ABORTO']
)

st.dataframe(
    resumo_ecc,
    use_container_width=True
)

# gráfico ECC

fig_ecc = px.bar(
    resumo_ecc,
    x='ECC',
    y=['PRENHA', 'VAZIA', 'ABORTO'],
    barmode='group',
    title='Resultado por ECC'
)

st.plotly_chart(
    fig_ecc,
    use_container_width=True
)

# ====================================
# BASE COMPLETA
# ====================================

st.subheader("Base Completa")

st.dataframe(
    df,
    use_container_width=True
)