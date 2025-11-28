import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

# --------------------------
# FUNÇÃO PARA CONECTAR GOOGLE
# --------------------------
def conectar_google():

    # Tenta ambiente CLOUD (Streamlit)
    try:
        secrets = st.secrets["gcp_service_account"]  # Só tenta acessar SE existir
        creds_json = json.dumps(dict(secrets))
        creds = Credentials.from_service_account_info(
            json.loads(creds_json),
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(creds)
        st.info("🔗 Conectado via CLOUD (secrets)")
        return client

    except Exception:
        pass

    # Ambiente LOCAL
    try:
        creds = Credentials.from_service_account_file(
            "cred.json",
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(creds)
        st.info("💻 Conectado via cred.json (LOCAL)")
        return client
    except Exception as e:
        st.error("❌ Erro ao conectar no Google:")
        st.error(str(e))
        return None


# --------------------------
# CONECTAR
# --------------------------
client = conectar_google()
if client is None:
    st.stop()

# --------------------------
# ABRIR PLANILHA
# --------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/1pvor4LGYpxE_7RJgJKCxMME2Yb47gNbByG4ZwZSctcE/edit?gid=1806237842"
sheet = client.open_by_url(SHEET_URL)
worksheet = sheet.worksheet("diario")

df = pd.DataFrame(worksheet.get_all_records())


# --------------------------
# STREAMLIT INTERFACE
# --------------------------
st.set_page_config(page_title="Leitura Google Sheets", layout="wide")
st.title("📄 Dados da Aba 'diario'")

# --------------------------
# FORMULÁRIO
# --------------------------
with st.form("form_diario"):

    lista_datas = df["Data"].dropna().unique().tolist()
    data_escolhida = st.selectbox("Selecione uma Data", lista_datas)

    turno = st.selectbox("Turno", ["T1", "T2", "T3"])
    qtde_hcs = st.number_input("Qtde. HCs", min_value=0, step=1)
    motivo_atraso = st.text_area("Motivo do Atraso do ATS")

    submitted = st.form_submit_button("Enviar")

    if submitted:

        # Localizar linha da data
        linhas = worksheet.col_values(1)
        linha_idx = linhas.index(str(data_escolhida)) + 1

        # Colunas por turno
        col_map = {
            "T1": {"hc": "Qtde HC T1", "atr": "Atraso T1?"},
            "T2": {"hc": "Qtde HC T2", "atr": "Atraso T2?"},
            "T3": {"hc": "Qtde HC T3", "atr": "Atraso T3?"}
        }

        col_hc = df.columns.get_loc(col_map[turno]["hc"]) + 1
        col_atraso = df.columns.get_loc(col_map[turno]["atr"]) + 1

        worksheet.update_cell(linha_idx, col_hc, qtde_hcs)
        worksheet.update_cell(linha_idx, col_atraso, motivo_atraso)

        st.success("Registro atualizado com sucesso!")

# --------------------------
# TABELA
# --------------------------
st.subheader("📄 Tabela Completa")
st.dataframe(df)
