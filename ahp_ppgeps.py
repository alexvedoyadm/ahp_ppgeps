import streamlit as st
import pandas as pd
import numpy as np

def calcular_matriz_comparacao(df, num_critérios):
    matriz_comparacao = np.identity(num_critérios)

    for index, row in df.iterrows():
        crit1, crit2 = map(int, row["Critérios/Alternativas"].split())
        importancia, valor = row["Importância/Valor"]
        
        if importancia == "+":
            matriz_comparacao[crit1 - 1, crit2 - 1] = valor
            matriz_comparacao[crit2 - 1, crit1 - 1] = 1 / valor
        elif importancia == "-":
            matriz_comparacao[crit1 - 1, crit2 - 1] = 1 / valor
            matriz_comparacao[crit2 - 1, crit1 - 1] = valor

    soma_colunas = matriz_comparacao.sum(axis=0)
    matriz_comparacao_com_soma = np.vstack((matriz_comparacao, soma_colunas))

    return matriz_comparacao_com_soma

def calcular_matriz_pesos(matriz_comparacao, soma_colunas):
    num_critérios = matriz_comparacao.shape[0]
    matriz_pesos = np.zeros((num_critérios, num_critérios))

    for i in range(num_critérios):
        for j in range(num_critérios):
            matriz_pesos[i, j] = matriz_comparacao[i, j] / soma_colunas[j]

    return matriz_pesos

def calcular_media_harmonica(valores):
    inversos = 1 / valores
    return len(valores) / np.sum(inversos)

def calcular_ich(matriz_comparacao, num_critérios, mh_s):
    ich = ((mh_s - num_critérios) * (num_critérios + 1)) / (num_critérios * (num_critérios - 1))
    return ich

def calcular_hri(num_critérios):
    tabela_hri = {
        3: 0.550,
        4: 0.859,
        5: 1.061,
        6: 1.205,
        7: 1.310,
        8: 1.381,
        9: 1.437,
        10: 1.484,
        15: 1.599,
        20: 1.650,
        25: 1.675,
    }
    return tabela_hri.get(num_critérios, "N/A")

def calcular_rc(ich, hri):
    return ich / hri

def calcular_rc_max(tamanho_matriz):
    tabela_rc_max = {
        "3 x 3": 0.05,
        "4 x 4": 0.08,
    }
    return tabela_rc_max.get(tamanho_matriz, 0.10)

def pagina_numero_critérios():
    st.title("Passo 1: Número de Critérios")
    num_critérios = st.number_input("Quantos critérios você vai avaliar?", min_value=2, max_value=7, step=1)

    if st.button("Ok"):
        if 3 <= num_critérios <= 7:
            st.session_state.num_critérios = num_critérios
            st.session_state.pagina_atual = "importancia_valor"
        else:
            st.warning("A quantidade de critérios deve variar apenas entre 3 e 7.")

def pagina_importancia_valor():
    st.title("Passo 2: Importância e Valor")

    if "num_critérios" not in st.session_state:
        st.warning("Por favor, insira o número de critérios na página anterior.")
        return

    num_critérios = st.session_state.num_critérios
    data = {"Critérios/Alternativas": [], "Importância/Valor": []}

    for i in range(1, num_critérios + 1):
        for j in range(i + 1, num_critérios + 1):
            importancia = st.selectbox(f" C{i} é mais importante, menos importante, ou igual C{j} ?", ["+", "-", "="])
            valor = st.number_input(f"De 0 (zero) a 9 (nove), quão importante é esse critério? C{i} C{j}", min_value=1, max_value=9, step=1)
            data["Critérios/Alternativas"].append(f"{i} {j}")
            data["Importância/Valor"].append((importancia, valor))

    if st.button("Ok"):
        df = pd.DataFrame(data)
        matriz_comparacao_com_soma = calcular_matriz_comparacao(df, num_critérios)
        matriz_comparacao = matriz_comparacao_com_soma[:-1, :]
        soma_colunas = matriz_comparacao_com_soma[-1, :]
        matriz_pesos = calcular_matriz_pesos(matriz_comparacao, soma_colunas)

        tabela_comparacao = criar_tabela(matriz_comparacao, soma_colunas)
        tabela_pesos = criar_tabela(matriz_pesos)

        st.title("Matrizes de Comparação e Pesos")
        st.subheader("Matriz de Comparação:")
        st.dataframe(tabela_comparacao)
        st.subheader("Matriz de Pesos:")
        st.dataframe(tabela_pesos)

        st.subheader("Pesos:")
        tabela_media_pesos = calcular_media_pesos(matriz_pesos)
        st.dataframe(tabela_media_pesos)

        mh_s = calcular_media_harmonica(soma_colunas)
        num_critérios = st.session_state.num_critérios
        ich = calcular_ich(matriz_comparacao, num_critérios, mh_s)
        hri = calcular_hri(num_critérios)
        rc = calcular_rc(ich, hri)
        tamanho_matriz = f"{num_critérios} x {num_critérios}"
        rc_max = calcular_rc_max(tamanho_matriz)

        st.title("Avaliação de Consistência")
        avaliacao_consistencia = {
            "Avaliação Consistência": ["MH(s)", "N", "ICH", "HRI", "RC", "RCMáx"],
            "Valor": [mh_s, num_critérios, ich, hri, rc, rc_max],
        }

        st.table(pd.DataFrame(avaliacao_consistencia).T)

def criar_tabela(matriz, soma_colunas=None):
    num_critérios = matriz.shape[0]
    tabela = pd.DataFrame(
        matriz,
        columns=[f"C{i+1}" for i in range(num_critérios)],
        index=[f"C{i+1}" for i in range(num_critérios)],
    )

    if soma_colunas is not None:
        tabela.loc["Soma das Colunas"] = soma_colunas

    return tabela

def calcular_media_pesos(matriz_pesos):
    num_critérios = matriz_pesos.shape[0]
    media_pesos = matriz_pesos.mean(axis=1)
    tabela_media_pesos = pd.DataFrame(
        media_pesos,
        columns=["Média de Pesos"],
        index=[f"C{i+1}" for i in range(num_critérios)],
    )
    return tabela_media_pesos

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "numero_critérios"

if st.session_state.pagina_atual == "numero_critérios":
    pagina_numero_critérios()
elif st.session_state.pagina_atual == "importancia_valor":
    pagina_importancia_valor()
