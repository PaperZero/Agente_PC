from groq import Groq
import streamlit as st
from dotenv import load_dotenv
import os
import re

# Ajusta o tamanho dos valores exibidos na grid de resultados.
st.markdown(
    "<style>div[data-testid='stMetricValue'] { font-size: 1.6rem; }</style>",
    unsafe_allow_html=True,
)

# Carrega variáveis de ambiente (caso utilize arquivo .env localmente)
load_dotenv()

st.title("💻 Assistente de Hardware para Jogos e Programas")
st.write("Informe o jogo ou programa alvo (e opcionalmente o orçamento) para receber a recomendação ideal das peças.")

# Inicializa o cliente Groq utilizando a chave de API das variáveis de ambiente
client = Groq(api_key=os.getenv('API_KEY_GROQ'))

# Entradas do usuário
jogo_alvo = st.text_input("Digite o jogo ou programa alvo (ex: Cyberpunk 2077, Blender, CS2):")
orcamento = st.text_input("Digite o orçamento disponível em R$ (opcional - deixe em branco para o menor preço possível):")

if st.button("Gerar Recomendação de Peças"):
    if not jogo_alvo:
        st.warning("Por favor, preencha pelo menos o jogo ou programa alvo.")
    else:
        # Define a estratégia com base no preenchimento ou não do orçamento
        if orcamento.strip() == "":
            criterio_orcamento = (
                "O usuário NÃO informou um orçamento. "
                "Portanto, monte a configuração com as PEÇAS MAIS BARATAS POSSÍVEIS do mercado brasileiro "
                "que consigam rodar o jogo/programa informado de forma aceitável. "
                "ATENÇÃO: Considere exclusivamente peças NOVAS (NÃO inclua peças usadas ou de segunda mão)."
                "Não escolha placas de video inferiores a placa 1050 TI, exceto se for uma placa de video integrada no processador"
            )
        else:
            criterio_orcamento = f"Orçamento disponível: {orcamento}. Mantenha o custo total estritamente dentro desse limite."

        # Prompt do Sistema restrito focado em retornar linhas claras para parsing
        SYSTEM_PROMPT = (
            "Você é um especialista em hardware de computadores no mercado brasileiro. "
            "Com base no jogo/programa informado e nas diretrizes de orçamento, recomende uma configuração de PC completa "
            "(Processador, Placa de Vídeo, Placa-Mãe, Memória RAM, Armazenamento, Fonte e Gabinete). "
            "REGRAS ESTRITAS DE FORMATO E PREÇO: "
            "1. Todos os preços DEVEM ser expressos exclusivamente em Real Brasileiro (R$). "
            "2. Retorne cada peça no formato exato: 'Categoria: Nome da Peça - R$ Preço' (Exemplo: 'Processador: AMD Ryzen 5 5600 - R$ 800,00'). "
            "3. NUNCA inclua links de compra, URLs ou nomes de lojas específicas. "
            "4. Não adicione textos extras, apenas a lista das peças."
        )

        user_content = f"Jogo/Programa alvo: {jogo_alvo}. {criterio_orcamento}"

        with st.spinner("Analisando o hardware ideal..."):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    model="openai/gpt-oss-120b",
                    temperature=0.7
                )

                resposta = chat_completion.choices[0].message.content
                
                st.subheader("Configuração Recomendada:")
                
                # Processamento do texto para estruturar em uma Grid (Colunas)
                linhas = [linha.strip() for linha in resposta.split("\n") if linha.strip()]
                
                pecas_extraidas = []
                valor_total = 0
                for linha in linhas:
                    # Remove marcadores de lista comuns se houver
                    linha_limpa = re.sub(r"^[\*\-\d\.\)]+\s*", "", linha)
                    if ":" in linha_limpa:
                        partes = linha_limpa.split(":", 1)
                        categoria = partes[0].strip()
                        detalhe = partes[1].strip()
                        pecas_extraidas.append((categoria, detalhe))
                        preco = re.search(r"R\$\s*([\d.]+(?:,\d{1,2})?)", detalhe)
                        if preco:
                            valor_total += float(
                                preco.group(1).replace(".", "").replace(",", ".")
                            )
                    elif linha_limpa:
                        pecas_extraidas.append(("Peça", linha_limpa))

                if pecas_extraidas:
                    # Exibe os itens em uma grid de 1 colunas
                    cols_por_linha = 1
                    for i in range(0, len(pecas_extraidas), cols_por_linha):
                        cols = st.columns(cols_por_linha)
                        for j in range(cols_por_linha):
                            if i + j < len(pecas_extraidas):
                                cat, det = pecas_extraidas[i + j]
                                with cols[j]:
                                    st.metric(label=cat, value=det)

                    total_formatado = f"{valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    st.metric(label="Valor Final", value=f"R$ {total_formatado}")
                else:
                    # Caso o formato retornado não siga o padrão esperado, exibe como texto normal
                    st.write(resposta)
                
            except Exception as e:
                st.error(f"Ocorreu um erro ao conectar com a API da Groq: {e}")
