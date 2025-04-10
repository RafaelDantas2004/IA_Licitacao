import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from datetime import datetime
import openai
import re

# Título do app
st.title("IA Buscadora de Editais - Gestão de Processos no DF")

# Campo para digitar a chave da OpenAI
api_key = st.text_input("Digite sua chave da OpenAI:", type="password")

# Verifica se a chave foi informada
if not api_key:
    st.warning("Insira sua chave da OpenAI para continuar.")
    st.stop()

# Configura a chave da OpenAI
openai.api_key = api_key

# Lista de sites e seções específicas onde estão os editais
SITES = {
    "Portal de Compras DF": "https://portal.compras.df.gov.br/licitacao",
    "TJDFT": "https://www.tjdft.jus.br/transparencia/licitacoes-contratos-e-instrumentos-de-cooperacao/licitacoes-1",
    "Secretaria de Economia": "https://www.economia.df.gov.br/category/licitacoes/",
    "Secretaria de Governo (Administrações Regionais)": "https://www.segov.df.gov.br/licitacao-nas-ras/"
}

# Palavras-chave para filtrar links inicialmente
KEYWORDS = [
    "gestao de processos",
    "gestão de processos",
    "bpm",
    "mapeamento de processos",
    "modelagem de processos",
    "Planejamento Estratégico",
    "Marketing",
    "Pesquisa de mercado",
    "Análise de dados"
]

# IA: Classificador simples com GPT-4.0 Mini
def classificar_com_ia(texto_link):
    prompt = f"""
    Classifique se o seguinte texto se refere a um edital de gestão de processos. Responda apenas com SIM ou NAO.
    Texto: \"{texto_link}\"
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response['choices'][0]['message']['content'].strip().upper()
    except Exception as e:
        return "ERRO"

# Função para extrair links e filtrar com IA
def buscar_editais(site, url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        resultados = []
        for link in soup.find_all('a', href=True):
            texto = link.get_text(strip=True).lower()
            href = link.get('href')
            full_link = href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/')

            if re.search(r'\.(pdf|docx|doc)$', href.lower()) and any(p in texto for p in KEYWORDS):
                classificacao = classificar_com_ia(texto)
                if classificacao == "SIM":
                    resultados.append({
                        "Site": site,
                        "Texto": link.get_text(strip=True),
                        "Link": full_link,
                        "Data da busca": datetime.today().strftime('%Y-%m-%d')
                    })
        return resultados
    except Exception as e:
        st.error(f"Erro ao acessar {url}: {e}")
        return []

# Botão para iniciar a busca
if st.button("Buscar editais agora"):
    todos_resultados = []
    with st.spinner('Buscando e classificando editais com IA...'):
        for site, url in SITES.items():
            resultados = buscar_editais(site, url)
            todos_resultados.extend(resultados)

    if todos_resultados:
        df_resultados = pd.DataFrame(todos_resultados)
        st.success(f"Foram encontrados {len(df_resultados)} editais relevantes!")
        st.dataframe(df_resultados)

        # Download como CSV
        csv = df_resultados.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Baixar resultados em CSV",
            data=csv,
            file_name='editais_gestao_processos_df.csv',
            mime='text/csv'
        )
    else:
        st.warning("Nenhum edital relevante encontrado com base na classificação por IA.")

# Rodapé
st.caption("Desenvolvido com 💡 por sua IA consultora usando ChatGPT-4.0 Mini.")
