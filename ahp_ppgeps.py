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

def pagina_numero_critérios():
    st.title("Para quantos critérios você quer atribuir pesos?")
    num_critérios = st.number_input("Você deve utilizar entre 3 e 7 critérios", min_value=3, max_value=7, step=1)

    if st.button("Ok"):
        if 3 <= num_critérios <= 7:
            st.session_state.num_critérios = num_critérios
            st.session_state.pagina_atual = "importancia_valor"
        else:
            st.warning("A quantidade de critérios deve variar apenas entre 3 e 7.")

def pagina_importancia_valor():
    st.title("Aqui você deverá definir a relação de importância entre os critérios.")

    if "num_critérios" not in st.session_state:
        st.warning("Por favor, insira o número de critérios na página anterior.")
        return

    num_critérios = st.session_state.num_critérios
    data = {"Critérios/Alternativas": [], "Importância/Valor": []}

    for i in range(1, num_critérios + 1):
        for j in range(i + 1, num_critérios + 1):
            importancia = st.selectbox(f" C{i} é mais importante, menos importante, ou tem a mesma importância que C{j} ?", ["+", "-", "="])
            valor = st.slider(f"Qual a relação de importância entre os critérios C{i} C{j}?", 1, 9, 5)
            descricao_slider = {
                1: "Importância igual (Contribuição idêntica das alternativas ou critérios)",
                2: "Importância entre Igual e Fraca",
                3: "Importância Fraca (Julgamento levemente superior para uma alternativa ou critério)",
                4: "Importância entre Fraca e Forte",
                5: "Importância Forte (Julgamento fortemente a favor de uma alternativa ou critério)",
                6: "Importância entre Forte e Muito Forte",
                7: "Importância Muito Forte (Dominância reconhecida de uma alternativa ou critério)",
                8: "Importância entre Muito Forte e Absoluta",
                9: "Importância absoluta (Dominância comprovada de uma alternativa ou critério)"
            }
            st.write(descricao_slider[valor])
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

        st.write("___")
        st.subheader("Matriz de Comparação:")
        st.dataframe(tabela_comparacao)
        st.write("___")
        st.subheader("Matriz de Pesos:")
        st.dataframe(tabela_pesos)
        st.write("___")
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

        st.write("___")
        st.title("Avaliação de Consistência", help="O Índice de Consistência é obtido por meio da Razão de Consistência de Saaty (1980).")
        avaliacao_consistencia = {
            "Avaliação Consistência": ["MH(s)", "N", "ICH", "HRI", "RC", "RCMáx"],
            "Valor": [mh_s, num_critérios, ich, hri, rc, rc_max],

        }

        # Estilização da tabela
        st.markdown('<style>table {border-collapse: collapse;} th, td {border: 1px solid black; padding: 8px; text-align: center;} th {background-color: #f2f2f2;}</style>', unsafe_allow_html=True)

        # Ocultando a primeira linha
        st.table(pd.DataFrame(avaliacao_consistencia).set_index('Avaliação Consistência'))

# Configuração da página Streamlit
st.set_page_config(
    page_title="AHP PPGEPS",
    page_icon="✅",
    layout="wide",
)

# Execução do aplicativo
if __name__ == "__main__":
    st.title("Analytic Hierarchy Process (AHP)")
    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = "numero_critérios"

    if st.session_state.pagina_atual == "numero_critérios":
        pagina_numero_critérios()
    elif st.session_state.pagina_atual == "importancia_valor":
        pagina_importancia_valor()
