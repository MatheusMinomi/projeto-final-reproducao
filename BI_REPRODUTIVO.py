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

@st.cache_data(ttl=0)

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

def limpar_sigla(coluna):

    return (
        coluna
        .fillna("")
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.strip()
    )

diag_df["Sigla Usual"] = limpar_sigla(
    diag_df["Sigla Usual"]
)

grupo_df["Sigla Usual"] = limpar_sigla(
    grupo_df["Sigla Usual"]
)

med_df["Sigla Usual"] = limpar_sigla(
    med_df["Sigla Usual"]
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
# PREPARAR ECC
# =========================================

# localizar coluna do ECC
if "Valor" in med_df.columns:
    col_ecc = "Valor"

else:

    # pega segunda coluna automaticamente
    col_ecc = med_df.columns[1]

med_df = med_df[
    ["Sigla Usual", col_ecc]
].copy()

# limpar sigla
med_df["Sigla Usual"] = (
    med_df["Sigla Usual"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
    .str.replace(".0", "", regex=False)
)

# limpar ECC
med_df[col_ecc] = (
    med_df[col_ecc]
    .fillna("")
    .astype(str)
    .str.strip()
)

# remover vazios
med_df = med_df[
    med_df[col_ecc] != ""
]

# remover duplicados
med_df = med_df.drop_duplicates(
    subset=["Sigla Usual"]
)

# renomear
med_df.rename(
    columns={col_ecc: "ECC"},
    inplace=True
)

# =========================================
# MERGES
# =========================================

# remover duplicados antes do merge
diag_df = diag_df.drop_duplicates(
    subset=["Sigla Usual"]
)

grupo_df = grupo_df.drop_duplicates(
    subset=["Sigla Usual"]
)

med_df = med_df.drop_duplicates(
    subset=["Sigla Usual"]
)

# merge grupo
df = diag_df.merge(
    grupo_df,
    on="Sigla Usual",
    how="left"
)

# merge ecc
df = df.merge(
    med_df,
    on="Sigla Usual",
    how="left"
)

# garantir grupo
if "Grupo Manejo" not in df.columns:
    df["Grupo Manejo"] = "SEM GRUPO"

# garantir ECC
if "ECC" not in df.columns:
    df["ECC"] = "SEM ECC"

# tratar grupo
df["Grupo Manejo"] = (
    df["Grupo Manejo"]
    .fillna("SEM GRUPO")
    .astype(str)
)

# tratar ECC
df["ECC"] = (
    df["ECC"]
    .fillna("SEM ECC")
    .astype(str)
)

# remover duplicados finais
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
# COMPARAÇÃO SAFRA ANTERIOR
# =========================================

taxa_estacao_passada = 81.25


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

# comparação safra passada
taxa_estacao_passada = 81.25

diferenca = round(
    taxa - taxa_estacao_passada,
    2
)

# meta estação atual
meta_estacao = 82.69

diferenca_meta = round(
    taxa - meta_estacao,
    2
)

# colunas KPI
c1, c2, c3, c4 = st.columns(4)

col1, col2, col3 = st.columns(3)

with col1:

    st.markdown(f"""
    <div style="
        background-color:#f8fafc;
        border-left:8px solid #2563eb;
        padding:25px;
        border-radius:18px;
        box-shadow:0 2px 8px rgba(0,0,0,0.08);
    ">

    <h3 style="color:#2563eb;">
        TOTAL
    </h3>

    <h1 style="
        font-size:50px;
        color:#1e293b;
    ">
        {total}
    </h1>

    <p>
        animais diagnosticados
    </p>

    </div>
    """, unsafe_allow_html=True)

with col2:

    st.markdown(f"""
    <div style="
        background-color:#f0fdf4;
        border-left:8px solid #16a34a;
        padding:25px;
        border-radius:18px;
        box-shadow:0 2px 8px rgba(0,0,0,0.08);
    ">

    <h3 style="color:#16a34a;">
        PRENHAS
    </h3>

    <h1 style="
        font-size:50px;
        color:#166534;
    ">
        {prenha}
    </h1>

    <p>
        diagnósticos positivos
    </p>

    </div>
    """, unsafe_allow_html=True)

with col3:

    st.markdown(f"""
    <div style="
        background-color:#fef2f2;
        border-left:8px solid #dc2626;
        padding:25px;
        border-radius:18px;
        box-shadow:0 2px 8px rgba(0,0,0,0.08);
    ">

    <h3 style="color:#dc2626;">
        VAZIAS
    </h3>

    <h1 style="
        font-size:50px;
        color:#991b1b;
    ">
        {vazia}
    </h1>

    <p>
        diagnósticos negativos
    </p>

    </div>
    """, unsafe_allow_html=True)


# CARD EXECUTIVO TAXA PRENHEZ

st.markdown(f"""
<div style="border:2px solid #9333ea;
border-radius:20px;
padding:30px;
margin-bottom:20px;">

<div style="display:flex;
justify-content:space-around;
text-align:center;">

<div>
<h2 style="color:#6b21a8;">
Taxa Prenhez %
</h2>

<div style="font-size:55px;
font-weight:bold;
color:#6b21a8;">
{taxa}%
</div>

<p style="color:red;
font-size:18px;">
{diferenca} p.p. vs 24/25
</p>
</div>

<div>
<h2 style="color:#6b21a8;">
Meta 25/26
</h2>

<div style="font-size:55px;
font-weight:bold;
color:#6b21a8;">
{meta_estacao}%
</div>

<p>
meta da estação
</p>
</div>

<div>
<h2 style="color:#6b21a8;">
Diferença p/ meta
</h2>

<div style="font-size:55px;
font-weight:bold;
color:red;">
{diferenca_meta} p.p.
</div>

<p>
abaixo da meta
</p>
</div>

</div>
</div>
""", unsafe_allow_html=True)





# =========================================
# TABELA RESUMO POR GRUPO
# =========================================

resumo_manejo = (
    df.groupby(["Grupo Manejo", "STATUS"])
    .size()
    .unstack(fill_value=0)
)

# garantir colunas
for col in ["PRENHA", "VAZIA", "ABORTO"]:

    if col not in resumo_manejo.columns:
        resumo_manejo[col] = 0

# total
resumo_manejo["TOTAL"] = (
    resumo_manejo["PRENHA"]
    + resumo_manejo["VAZIA"]
    + resumo_manejo["ABORTO"]
)

# taxa prenhez
resumo_manejo["TAXA PRENHEZ %"] = (
    resumo_manejo["PRENHA"]
    / resumo_manejo["TOTAL"]
    * 100
).round(1)

# organizar
resumo_manejo = resumo_manejo.reset_index()

# exibir
st.subheader("Resumo Reprodutivo por Grupo Manejo")

st.dataframe(
    resumo_manejo,
    use_container_width=True
)

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
# TABELA RESUMO POR ECC
# =========================================

resumo_tabela_ecc = (
    df.groupby(["ECC", "STATUS"])
    .size()
    .unstack(fill_value=0)
)

# garantir colunas
for col in ["PRENHA", "VAZIA", "ABORTO"]:

    if col not in resumo_tabela_ecc.columns:
        resumo_tabela_ecc[col] = 0

# total
resumo_tabela_ecc["TOTAL"] = (
    resumo_tabela_ecc["PRENHA"]
    + resumo_tabela_ecc["VAZIA"]
    + resumo_tabela_ecc["ABORTO"]
)

# taxa prenhez
resumo_tabela_ecc["TAXA PRENHEZ %"] = (
    resumo_tabela_ecc["PRENHA"]
    / resumo_tabela_ecc["TOTAL"]
    * 100
).round(1)

# organizar
resumo_tabela_ecc = resumo_tabela_ecc.reset_index()

# exibir
st.subheader("Resumo Reprodutivo por ECC")

st.dataframe(
    resumo_tabela_ecc,
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