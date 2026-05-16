import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================
# CONFIGURAÇÃO
# =========================================

st.set_page_config(
    page_title="BI Reprodutivo",
    page_icon="🐄",
    layout="wide"
)

st.title("🐄 BI REPRODUTIVO")
st.subheader("Diagnóstico • ECC • Grupo Manejo")

# =========================================
# LEITURA DOS ARQUIVOS
# =========================================

@st.cache_data
def carregar_dados():

    diagnostico = pd.read_excel("DIAGNOSTICOS/DIAGNOSTICO.xls")

    grupo = pd.read_excel("GRUPOS/GRUPO_MANEJO.xls")

    medicao = pd.read_excel("MEDICOES/MEDICAO.xls")

    return diagnostico, grupo, medicao


diag_df, grupo_df, med_df = carregar_dados()

# =========================================
# PADRONIZAR COLUNAS
# =========================================

diag_df.columns = diag_df.columns.str.strip()
grupo_df.columns = grupo_df.columns.str.strip()
med_df.columns = med_df.columns.str.strip()

# =========================================
# PADRONIZAR SIGLA
# =========================================

diag_df["Sigla Usual"] = (
    diag_df["Sigla Usual"]
    .astype(str)
    .str.strip()
    .str.upper()
)

grupo_df["Sigla Usual"] = (
    grupo_df["Sigla Usual"]
    .astype(str)
    .str.strip()
    .str.upper()
)

med_df["Sigla Usual"] = (
    med_df["Sigla Usual"]
    .astype(str)
    .str.strip()
    .str.upper()
)



# =========================================
# PREPARAR GRUPO MANEJO
# =========================================

if "Descrição" in grupo_df.columns:
    col_grupo = "Descrição"

elif "Grupo Manejo" in grupo_df.columns:
    col_grupo = "Grupo Manejo"

else:
    st.error(f"Coluna de grupo não encontrada. Colunas existentes: {grupo_df.columns.tolist()}")
    st.stop()

grupo_df = grupo_df[
    ["Sigla Usual", col_grupo]
].copy()

# remover duplicados
grupo_df = grupo_df.drop_duplicates(
    subset=["Sigla Usual"]
)

grupo_df.rename(
    columns={col_grupo: "Grupo Manejo"},
    inplace=True
)



# =========================================
# MERGES
# =========================================

df = diag_df.merge(
    grupo_df,
    on="Sigla Usual",
    how="left"
)

# remover animais duplicados
df = df.drop_duplicates(
    subset=["Sigla Usual"]
)


# =========================================
# STATUS REPRODUTIVO
# =========================================

# identificar coluna correta
if "Estado" in df.columns:
    col_estado = "Estado"

elif "Estado Diagnóstico" in df.columns:
    col_estado = "Estado Diagnóstico"

else:
    st.error(f"Coluna de estado não encontrada. Colunas existentes: {df.columns.tolist()}")
    st.stop()

# limpar estado
df[col_estado] = (
    df[col_estado]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)

# limpar aborto
df["Tipo Aborto"] = (
    df["Tipo Aborto"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)

# criar status
df["STATUS"] = "SEM STATUS"

# PRENHA
df.loc[
    df[col_estado].str.contains("PREN", na=False),
    "STATUS"
] = "PRENHA"

# VAZIA
df.loc[
    df[col_estado].str.contains("VAZ", na=False),
    "STATUS"
] = "VAZIA"

# ABORTO
df.loc[
    df["Tipo Aborto"].str.contains("ABORT", na=False),
    "STATUS"
] = "ABORTO"

# remover sem status
df = df[
    df["STATUS"] != "SEM STATUS"
]


# =========================================
# TRATAR VAZIOS
# =========================================

# =========================================
# TRATAR GRUPO MANEJO
# =========================================

if "Grupo Manejo" not in df.columns:
    df["Grupo Manejo"] = "SEM GRUPO"

df["Grupo Manejo"] = (
    df["Grupo Manejo"]
    .fillna("SEM GRUPO")
    .astype(str)
)

# =========================================
# TRATAR ECC
# =========================================

if "ECC" not in df.columns:
    df["ECC"] = "SEM ECC"

df["ECC"] = (
    df["ECC"]
    .fillna("SEM ECC")
    .astype(str)
)


# =========================================
# SIDEBAR
# =========================================

st.sidebar.header("Filtros")

# Grupo
lista_grupos = sorted(
    df["Grupo Manejo"].unique()
)

filtro_grupo = st.sidebar.multiselect(
    "Grupo Manejo",
    lista_grupos,
    default=lista_grupos
)

# ECC
lista_ecc = sorted(
    df["ECC"].unique()
)

filtro_ecc = st.sidebar.multiselect(
    "ECC",
    lista_ecc,
    default=lista_ecc
)

# Status
lista_status = sorted(
    df["STATUS"].unique()
)

filtro_status = st.sidebar.multiselect(
    "Status",
    lista_status,
    default=lista_status
)

# =========================================
# APLICAR FILTROS
# =========================================

df = df[
    df["Grupo Manejo"].isin(filtro_grupo)
]

df = df[
    df["ECC"].isin(filtro_ecc)
]

df = df[
    df["STATUS"].isin(filtro_status)
]

# =========================================
# KPIs
# =========================================

total = len(df)

prenha = len(
    df[df["STATUS"] == "PRENHA"]
)

vazia = len(
    df[df["STATUS"] == "VAZIA"]
)

aborto = len(
    df[df["STATUS"] == "ABORTO"]
)

taxa = round(
    (prenha / total) * 100,
    1
) if total > 0 else 0

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total", total)
c2.metric("Prenhas", prenha)
c3.metric("Vazias", vazia)
c4.metric("Taxa Prenhez %", taxa)

# =========================================
# RESUMO POR GRUPO
# =========================================

st.subheader("Resumo por Grupo Manejo")

resumo_grupo = (
    df.groupby(
        ["Grupo Manejo", "STATUS"]
    )
    .size()
    .reset_index(name="TOTAL")
)

fig_grupo = px.bar(
    resumo_grupo,
    x="Grupo Manejo",
    y="TOTAL",
    color="STATUS",
    barmode="group"
)

st.plotly_chart(
    fig_grupo,
    use_container_width=True
)

# =========================================
# RESUMO POR ECC
# =========================================

st.subheader("Resumo por ECC")

resumo_ecc = (
    df.groupby(
        ["ECC", "STATUS"]
    )
    .size()
    .reset_index(name="TOTAL")
)

fig_ecc = px.bar(
    resumo_ecc,
    x="ECC",
    y="TOTAL",
    color="STATUS",
    barmode="group"
)

st.plotly_chart(
    fig_ecc,
    use_container_width=True
)

# =========================================
# TABELA COMPLETA
# =========================================

st.subheader("Base Completa")

st.dataframe(
    df,
    use_container_width=True
)