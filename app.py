import io
import os
import streamlit as st
from openai import OpenAI
import pypdf

# Configuração inicial da página Streamlit
st.set_page_config(
    page_title="Chamados T.I. - Microsoft Foundry", page_icon="🤖", layout="wide"
)

# -------------------------------------------------------------------------
# 1. INTERFACE E ESTILO (CSS CUSTOMIZADO)
# -------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }
    
    .stChatFloatingInputContainer, div.block-container {
        border-radius: 12px;
    }
    
    .header-title {
        font-size: 24px;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0px;
    }
    
    .header-subtitle {
        font-size: 14px;
        color: #666;
        margin-bottom: 20px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------------
# 2. CONFIGURAÇÃO DA API (MICROSOFT FOUNDRY)
# -------------------------------------------------------------------------
API_KEY = "6t2pTNsmNafDyo53MDAFIrvvQRBZXP7dLcr5j3TLxMS34LQVq3ZUJQQJ99CHACHYHv6XJ3w3AAAAACOGT7os"
MODEL_NAME = "gpt-4.1-mini"
ENDPOINT = "https://marcelomaffeis-05082026-resource.services.ai.azure.com/"

try:
    client = OpenAI(api_key=API_KEY, base_url=ENDPOINT)
except Exception as e:
    st.error(f"Erro ao inicializar o cliente da API: {e}")

# -------------------------------------------------------------------------
# 3. UPLOAD DE ARQUIVOS E SISTEMA RAG (BARRA LATERAL)
# -------------------------------------------------------------------------
st.sidebar.title("📁 Configuração RAG")
st.sidebar.markdown(
    "Envie um arquivo para servir como contexto para as respostas do bot."
)

uploaded_file = st.sidebar.file_uploader(
    "Escolha um arquivo PDF ou TXT", type=["pdf", "txt"]
)

if "file_text" not in st.session_state:
    st.session_state.file_text = ""

if uploaded_file is not None:
    extracted_text = ""
    if uploaded_file.type == "application/pdf":
        try:
            reader = pypdf.PdfReader(uploaded_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
            st.sidebar.success(
                f"PDF carregado com sucesso! ({len(reader.pages)} páginas)"
            )
        except Exception as e:
            st.sidebar.error(f"Erro ao processar o PDF: {e}")

    elif uploaded_file.type == "text/plain":
        try:
            extracted_text = uploaded_file.getvalue().decode("utf-8")
            st.sidebar.success("Arquivo TXT carregado com sucesso!")
        except Exception as e:
            st.sidebar.error(f"Erro ao ler o arquivo TXT: {e}")

    st.session_state.file_text = extracted_text
else:
    if st.sidebar.button("Limpar Contexto do Arquivo"):
        st.session_state.file_text = ""
        st.rerun()

if st.session_state.file_text:
    st.sidebar.info(
        f"📊 Contexto Ativo: ~{len(st.session_state.file_text)} caracteres carregados."
    )
else:
    st.sidebar.warning("Nenhum arquivo ativo. O bot responderá sem contexto RAG.")

# -------------------------------------------------------------------------
# 4. LÓGICA DE CHAT E INTERFACE PRINCIPAL
# -------------------------------------------------------------------------
st.markdown(
    '<p class="header-title">💻 Chamados T.I. - Assistente Inteligente</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="header-subtitle">Suporte interno desenvolvido com Streamlit e Microsoft AI Foundry</p>',
    unsafe_allow_html=True,
)

with st.container():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Digite sua dúvida ou chamado aqui..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        base_system_prompt = (
            "Você é um assistente virtual especialista em suporte de TI, prestativo e educado."
        )
        if st.session_state.file_text:
            system_prompt = (
                f"{base_system_prompt}\n\n"
                "Utilize estritamente as informações contidas no seguinte CONTEXTO DO DOCUMENTO para responder à pergunta do usuário. "
                "Se a resposta não estiver explícita no contexto, informe educadamente que o documento fornecido não contém essa informação.\n\n"
                f"--- CONTEXTO DO DOCUMENTO ---\n{st.session_state.file_text}\n--- FIM DO CONTEXTO ---"
            )
        else:
            system_prompt = (
                f"{base_system_prompt} Responda da melhor forma possível ao usuário."
            )

        messages_payload = [{"role": "system", "content": system_prompt}]
        for msg in st.session_state.messages:
            messages_payload.append({"role": msg["role"], "content": msg["content"]})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME, messages=messages_payload, stream=True
                )
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content_piece = chunk.choices[0].delta.content
                        full_response += content_piece
                        message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            except Exception as e:
                full_response = (
                    f"Desculpe, ocorreu um erro de conexão com a API do Microsoft Foundry: {e}"
                )
                message_placeholder.markdown(full_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
