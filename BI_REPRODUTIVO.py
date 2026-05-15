import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="BI Reprodutivo",
    layout="wide"
)

st.title("📊 BI REPRODUTIVO")

# =========================
# LOCALIZAR ARQUIVOS
# =========================

pasta = Path(".")

arquivos_diag = list(Path("DIAGNOSTICOS").glob("*.xls*"))
arquivos_grupo = list(Path("GRUPOS").glob("*.xls*"))
arquivos_medicao = list(Path("MEDICOES").glob("*.xls*"))
if not arquivos_diag:
    st.error("Arquivo DIAGNOSTICO não encontrado.")
    st.stop()

if not arquivos_grupo:
    st.error("Arquivo GRUPO_MANEJO não encontrado.")
    st.stop()

diag_path = arquivos_diag[0]
grupo_path = arquivos_grupo[0]

# =========================
# LER PLANILHAS
# =========================

diag_df = pd.read_excel(diag_path)
grupo_df = pd.read_excel(grupo_path)


col_estado = "Estado"
col_aborto = "Tipo Aborto"

# =========================
# MAPEAR GRUPO MANEJO
# =========================
# Detectar colunas do grupo manejo
grupo_sigla_col = [c for c in grupo_df.columns if 'sigla' in str(c).lower()][0]

grupo_manejo_col = [c for c in grupo_df.columns if 'grupo' in str(c).lower()][0]
mapa = grupo_df[[grupo_sigla_col, grupo_manejo_col]].dropna()
mapa = mapa.drop_duplicates(subset=[grupo_sigla_col])
# Detectar coluna SIGLA do diagnóstico
diag_sigla_col = [c for c in diag_df.columns if 'sigla' in str(c).lower()][0]
diag_df['Grupo Manejo'] = diag_df[diag_sigla_col].map(
    mapa.set_index(grupo_sigla_col)[grupo_manejo_col]
)

diag_df['Grupo Manejo'] = diag_df['Grupo Manejo'].fillna('SEM GRUPO')

# =========================
# STATUS REPRODUTIVO
# =========================
if 'Estado Diagnóstico' in diag_df.columns:
    col_status = 'Estado Diagnóstico'
else:
    col_status = 'Estado'

diag_df['STATUS'] = (
    diag_df[col_status]
    .fillna('')
    .astype(str)
    .str.strip()
    .str.upper()
)

diag_df['PRENHA'] = diag_df['STATUS'].str.contains('PREN', na=False)
diag_df['VAZIA'] = diag_df['STATUS'].str.contains('VAZ', na=False)

diag_df['ABORTO'] = (
    diag_df[col_aborto]
    .astype(str)
    .str.upper()
    .str.contains('ABORTO', na=False)
)

# =========================
# RESUMO GRUPOS
# =========================

resumo = diag_df.groupby('Grupo Manejo').agg(
    PRENHA=('PRENHA', 'sum'),
    VAZIA=('VAZIA', 'sum'),
    ABORTO=('ABORTO', 'sum')
).reset_index()
# Linha total
total_row = pd.DataFrame([{
    'Grupo Manejo': 'TOTAL',
    'PRENHA': resumo['PRENHA'].sum(),
    'VAZIA': resumo['VAZIA'].sum(),
    'ABORTO': resumo['ABORTO'].sum()
}])

resumo = pd.concat(
    [resumo, total_row],
    ignore_index=True
)
resumo['TOTAL'] = (
    resumo['PRENHA'] +
    resumo['VAZIA'] +
    resumo['ABORTO']
)

resumo['TAXA_PRENHEZ_%'] = (
    resumo['PRENHA'] /
    (resumo['PRENHA'] + resumo['VAZIA'])
    * 100
).round(1)

# =========================
# DASHBOARD
# =========================

st.subheader("Resumo Reprodutivo por Grupo")

st.dataframe(resumo, use_container_width=True)

# =========================
# GRÁFICO PRENHA/VÁZIA/ABORTO
# =========================

grafico_df = resumo.melt(
    id_vars='Grupo Manejo',
    value_vars=['PRENHA', 'VAZIA', 'ABORTO'],
    var_name='Status',
    value_name='Quantidade'
)

fig = px.bar(
    grafico_df,
    x='Grupo Manejo',
    y='Quantidade',
    color='Status',
    barmode='group',
    title='Resultado Reprodutivo por Grupo'
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# TAXA PRENHEZ
# =========================

fig2 = px.bar(
    resumo,
    x='Grupo Manejo',
    y='TAXA_PRENHEZ_%',
    title='Taxa de Prenhez (%)',
    text='TAXA_PRENHEZ_%'
)

st.plotly_chart(fig2, use_container_width=True)

# =========================
# ECC
# =========================

if arquivos_medicao:

    med_path = arquivos_medicao[0]

    med_df = pd.read_excel(med_path)

    # Colunas corretas
    med_sigla_col = "Sigla Usual"
    ecc_col = "Valor"

    # Padronizar siglas
    diag_df[diag_sigla_col] = (
        diag_df[diag_sigla_col]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    med_df[med_sigla_col] = (
        med_df[med_sigla_col]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Remover duplicidade
    med_df = med_df.drop_duplicates(
        subset=[med_sigla_col]
    )

    # Merge ECC
    diag_df = diag_df.merge(
        med_df[[med_sigla_col, ecc_col]],
        left_on=diag_sigla_col,
        right_on=med_sigla_col,
        how='left'
    )

    # Renomear
    diag_df.rename(
        columns={ecc_col: 'ECC'},
        inplace=True
    )

    # Resumo ECC
    ecc_resumo = diag_df.groupby('ECC').agg(
        PRENHA=('PRENHA', 'sum'),
        VAZIA=('VAZIA', 'sum'),
        ABORTO=('ABORTO', 'sum')
    ).reset_index()

    # Linha total ECC
    total_ecc = pd.DataFrame([{
        'ECC': 'TOTAL',
        'PRENHA': ecc_resumo['PRENHA'].sum(),
        'VAZIA': ecc_resumo['VAZIA'].sum(),
        'ABORTO': ecc_resumo['ABORTO'].sum()
    }])

    ecc_resumo = pd.concat(
        [ecc_resumo, total_ecc],
        ignore_index=True
    )

    st.subheader("ECC x Resultado Reprodutivo")

    st.dataframe(ecc_resumo, use_container_width=True)

    ecc_melt = ecc_resumo[
        ecc_resumo['ECC'] != 'TOTAL'
    ].melt(
        id_vars='ECC',
        value_vars=['PRENHA', 'VAZIA', 'ABORTO'],
        var_name='Status',
        value_name='Quantidade'
    )

    fig3 = px.bar(
        ecc_melt,
        x='ECC',
        y='Quantidade',
        color='Status',
        barmode='group',
        title='Resultado por ECC'
    )

    st.plotly_chart(fig3, use_container_width=True)
# =========================
# EXPORTAR EXCEL
# =========================

resumo.to_excel("RESUMO_GRUPOS.xlsx", index=False)

st.success("RESUMO_GRUPOS.xlsx gerado com sucesso.")