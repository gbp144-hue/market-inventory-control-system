import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from google import genai
import streamlit as st
import plotly.express as px

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

USUARIO = "admin"
SENHA = "1234"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:

    st.title("🔐 Login - Mercado Carra")

    usuario_input = st.text_input("Usuário")
    senha_input = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        if usuario_input == USUARIO and senha_input == SENHA:
            st.session_state.autenticado = True
            st.success("Login bem-sucedido!")
            st.rerun()

        else:
            st.error("Usuário ou senha incorretos.")

    st.stop()

st.set_page_config(page_title="Mercado Carra - ERP", layout="centered")

st.title("🛒 Mercado Carra - ERP")
st.markdown("Seja Bem-Vindo ao Mercado Carra!")

BD_PATH = "Estoque.db"

def init_bd():
    conexao = sqlite3.connect(BD_PATH)
    cursor = conexao.cursor() 
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        codigo INTEGER UNIQUE,
        descricao TEXT,
        quantidade INTEGER,
        unidade_de_medida TEXT,
        preco REAL,
        total REAL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora TEXT,
        codigo_produto INTEGER,
        descricao_produto TEXT,
        quantidade_vendida INTEGER,
        valor_total REAL
    )
    ''')
    conexao.commit()
    conexao.close()

init_bd()

def gerar_pdf_nota_multipla(venda_id, data_hora, itens_carrinho, valor_total_geral):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(200, 10, txt="MERCADO CARRA - COMPROVANTE DE VENDA", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 6, txt="CNPJ: 00.000.000/0001-00 - Santos / SP", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, txt="----------------------------------------------------------------------------------", ln=True, align="C")
    
    pdf.ln(2)
    pdf.cell(200, 8, txt=f"Comprovante de Venda ID: #{venda_id}", ln=True)
    pdf.cell(200, 8, txt=f"Data/Hora: {data_hora}", ln=True)
    pdf.cell(200, 8, txt="----------------------------------------------------------------------------------", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(90, 8, txt="Produto", border=0)
    pdf.cell(30, 8, txt="Qtd", border=0, align="C")
    pdf.cell(35, 8, txt="Preço Un.", border=0, align="R")
    pdf.cell(35, 8, txt="Total", border=0, align="R")
    pdf.ln(8)
    
    pdf.set_font("Arial", "", 10)
    for item in itens_carrinho:
        pdf.cell(90, 7, txt=str(item['descricao']), border=0)
        pdf.cell(30, 7, txt=str(item['quantidade']), border=0, align="C")
        pdf.cell(35, 7, txt=f"R$ {item['preco']:.2f}", border=0, align="R")
        pdf.cell(35, 7, txt=f"R$ {item['subtotal']:.2f}", border=0, align="R")
        pdf.ln(7)
        
    pdf.cell(200, 8, txt="----------------------------------------------------------------------------------", ln=True)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(130, 10, txt="VALOR TOTAL DA COMPRA:", border=0)
    pdf.cell(60, 10, txt=f"R$ {valor_total_geral:.2f}", border=0, align="R")
    
    pdf.ln(15)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(200, 8, txt="Obrigado pela preferência! Volte sempre ao Mercado Carra.", ln=True, align="C")
    
    return bytes(pdf.output())

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📦 Tarefa de Depósito", 
    "🔍 Estoque Disponível", 
    "🛒 Carrinho", 
    "📊 Relatório de Vendas",
    "🤖 Assistente IA"
])

# --- ABA 1: Materiais---
with aba1:
    st.subheader("Gerenciamento de Materiais no Inventário")
    
    with st.form("form_cadastro", clear_on_submit=True):
        codigo = st.number_input("Código do Produto", min_value=1, step=1)
        descricao = st.text_input("Descrição do Material")
        quantidade = st.number_input("Quantidade em Estoque", min_value=0, step=1)
        unidade = st.text_input("Unidade de Medida (ex: UN, KG, L)")
        preco = st.number_input("Preço Unitário (R$)", min_value=0.0, format="%.2f")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted_salvar = st.form_submit_button("Salvar/Atualizar")
        with col_btn2:
            submitted_excluir = st.form_submit_button("🗑️ Excluir")

        if submitted_salvar:
            if descricao.strip() and unidade.strip():
                total = quantidade * preco
                conexao = sqlite3.connect(BD_PATH)
                cursor = conexao.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO produtos (codigo, descricao, quantidade, unidade_de_medida, preco, total)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (codigo, descricao, quantidade, unidade, preco, total))
                conexao.commit()
                conexao.close()
                st.success(f"Produto '{descricao}' cadastrado ou atualizado com sucesso!")
            else:
                st.error("Por favor, preencha a descrição e a unidade de medida para salvar.")

        if submitted_excluir:
            conexao = sqlite3.connect(BD_PATH)
            cursor = conexao.cursor()
            cursor.execute("SELECT descricao FROM produtos WHERE codigo = ?", (codigo,))
            produto_existe = cursor.fetchone()
            
            if produto_existe:
                cursor.execute("DELETE FROM produtos WHERE codigo = ?", (codigo,))
                conexao.commit()
                conexao.close()
                st.success(f"Produto com código {codigo} ({produto_existe[0]}) foi excluído do inventário com sucesso!")
            else:
                conexao.close()
                st.error(f"Nenhum produto encontrado com o código {codigo} para exclusão.")

# --- ABA 2: CONSULTAR ESTOQUE ---
with aba2:
    st.subheader("Estoque")
     
    conexao = sqlite3.connect(BD_PATH)
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM produtos")
    dados = cursor.fetchall()
    conexao.close()
     
    if dados:
        df = pd.DataFrame(dados, columns=["Código", "Descrição", "Quantidade", "Unidade", "Preço Unitário (R$)", "Total (R$)"])
        st.dataframe(df, use_container_width=True)
        
        total_itens = df["Quantidade"].sum()
        valor_total_estoque = df["Total (R$)"].sum()
        col1, col2 = st.columns(2)
        col1.metric("Volume Total em Estoque", total_itens)
        col2.metric("Valor Patrimonial do Estoque", f"R$ {valor_total_estoque:,.2f}")
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Relatório de Estoque (CSV/Excel)",
            data=csv,
            file_name='relatorio_estoque_mercadocarra.csv',
            mime='text/csv',
        )
    else:
        st.info("Nenhum produto cadastrado no banco de dados ainda.")    

with aba3:
    st.subheader("Carrinho de Compras")
    
    conexao = sqlite3.connect(BD_PATH)
    cursor = conexao.cursor()
    cursor.execute("SELECT codigo, descricao, quantidade, unidade_de_medida, preco FROM produtos WHERE quantidade > 0")
    produtos_disponiveis = cursor.fetchall()
    conexao.close()
    
    if produtos_disponiveis:
        # Criamos um dicionário de opções para o selectbox
        opcoes_produtos = {f"{p[0]} - {p[1]} (Disp: {p[2]} {p[3]}) - R$ {p[4]:.2f}": p for p in produtos_disponiveis}
        
        # Mapeamento reverso para achar a chave pelo código digitado
        codigo_para_opcao = {str(p[0]): chave for chave, p in opcoes_produtos.items()}
        
        st.markdown("---")
        
        # 1. Campo de pesquisa por código / leitor de código de barras
        codigo_digitado = st.text_input("🔍 Pesquisar por Código do Produto", placeholder="Digite o código e pressione Enter ou selecione abaixo")
        
        # Se o usuário digitou um código válido, filtramos a escolha inicial
        escolha_padrao = 0
        if codigo_digitado in codigo_para_opcao:
            chave_encontrada = codigo_para_opcao[codigo_digitado]
            # Encontra o índice da opção correspondente na lista
            lista_chaves = list(opcoes_produtos.keys())
            if chave_encontrada in lista_chaves:
                escolha_padrao = lista_chaves.index(chave_encontrada)

        # 2. Selectbox atualizado (agora pode ser pré-selecionado via código)
        escolha = st.selectbox("Selecione o Produto para Adicionar", list(opcoes_produtos.keys()), index=escolha_padrao)
        
        produto_selecionado = opcoes_produtos[escolha]
        db_codigo, db_desc, db_qtd_est, db_unidade, db_preco = produto_selecionado
        
        qtd_venda = st.number_input("Quantidade", min_value=1, max_value=int(db_qtd_est), step=1, key="qtd_input")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("➕ Adicionar ao Carrinho"):
                item_existente = next((item for item in st.session_state.carrinho if item['codigo'] == db_codigo), None)
                if item_existente:
                    if (item_existente['quantidade'] + qtd_venda) <= db_qtd_est:
                        item_existente['quantidade'] += qtd_venda
                        item_existente['subtotal'] = item_existente['quantidade'] * db_preco
                        st.success("Quantidade atualizada!")
                    else:
                        st.error("Quantidade total excede o estoque disponível!")
                else:
                    st.session_state.carrinho.append({
                        "codigo": db_codigo,
                        "descricao": db_desc,
                        "quantidade": qtd_venda,
                        "preco": db_preco,
                        "subtotal": qtd_venda * db_preco
                    })
                    st.success("Adicionado ao Carrinho!")
                st.rerun()
                
        with col_b:
            if st.button("🗑️ Limpar Carrinho"):
                st.session_state.carrinho = []
                st.rerun()

        if st.session_state.carrinho:
            st.markdown("---")
            st.markdown("### 🛒 Itens no Carrinho")
            df_carrinho = pd.DataFrame(st.session_state.carrinho)
            st.dataframe(df_carrinho[["codigo", "descricao", "quantidade", "preco", "subtotal"]], use_container_width=True)
            
            total_geral = sum(item['subtotal'] for item in st.session_state.carrinho)
            st.metric("Valor Total da Nota", f"R$ {total_geral:,.2f}")
            
            if st.button("✅ Finalizar Venda"):
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                conexao = sqlite3.connect(BD_PATH)
                cursor = conexao.cursor()
                
                cursor.execute("INSERT INTO vendas (data_hora, codigo_produto, descricao_produto, quantidade_vendida, valor_total) VALUES (?, ?, ?, ?, ?)",
                               (data_atual, 0, "VENDA MULTIPLA (CARRINHO)", len(st.session_state.carrinho), total_geral))
                venda_id = cursor.lastrowid
                
                for item in st.session_state.carrinho:
                    cursor.execute("SELECT quantidade, preco FROM produtos WHERE codigo = ?", (item['codigo'],))
                    res = cursor.fetchone()
                    if res:
                        est_atual, preco_item = res
                        novo_est = est_atual - item['quantidade']
                        novo_tot = novo_est * preco_item
                        cursor.execute("UPDATE produtos SET quantidade = ?, total = ? WHERE codigo = ?", (novo_est, novo_tot, item['codigo']))
                        
                        cursor.execute("INSERT INTO vendas (data_hora, codigo_produto, descricao_produto, quantidade_vendida, valor_total) VALUES (?, ?, ?, ?, ?)",
                                       (data_atual, item['codigo'], item['descricao'], item['quantidade'], item['subtotal']))
                
                conexao.commit()
                conexao.close()
                
                pdf_bytes = gerar_pdf_nota_multipla(venda_id, data_atual, st.session_state.carrinho, total_geral)
                
                st.success("Venda finalizada!")
                
                st.download_button(
                    label="📄 Baixar Nota Fiscal Consolidada em PDF",
                    data=pdf_bytes,
                    file_name=f"nota_fiscal_multipla_{venda_id}.pdf",
                    mime="application/pdf"
                )
                
                st.session_state.carrinho = []
        else:
            st.info("O carrinho está vazio. Adicione itens.")
    else:
        st.warning("Não há produtos disponíveis em estoque.")


# --- ABA 4: HISTÓRICO E RELATÓRIOS ---
with aba4:
    st.subheader("📊 Relatório de Vendas e Desempenho")
    
    conexao = sqlite3.connect(BD_PATH)
    cursor = conexao.cursor()
    cursor.execute("SELECT data_hora, codigo_produto, descricao_produto, quantidade_vendida, valor_total FROM vendas")
    dados_vendas = cursor.fetchall()
    conexao.close()
    
    if dados_vendas:
        df_vendas = pd.DataFrame(dados_vendas, columns=["Data/Hora", "Código", "Produto", "Qtd Vendida", "Valor Total (R$)"])
        
        # Filtra apenas os itens reais vendidos (removendo a linha de controle "VENDA MULTIPLA")
        df_vendas_itens = df_vendas[df_vendas["Código"] != 0]
        
        # Métricas principais no topo
        faturamento_total = df_vendas_itens["Valor Total (R$)"].sum()
        total_itens_vendidos = df_vendas_itens["Qtd Vendida"].sum()
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Faturamento Acumulado", f"R$ {faturamento_total:,.2f}")
        col_m2.metric("Total de Itens Vendidos", int(total_itens_vendidos))
        
        st.markdown("---")
        
        # Se houver vendas reais, exibe os gráficos lado a lado
        if not df_vendas_itens.empty:
            st.markdown("### 📈 Indicadores Visuais")
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.markdown("#### Produtos Mais Vendidos (Quantidade)")
                df_qtd_prod = df_vendas_itens.groupby("Produto")["Qtd Vendida"].sum().reset_index()
                fig_qtd = px.bar(
                    df_qtd_prod, 
                    x="Produto", 
                    y="Qtd Vendida", 
                    text="Qtd Vendida",
                    color="Qtd Vendida",
                    labels={"Produto": "Produto", "Qtd Vendida": "Qtd Total"}
                )
                st.plotly_chart(fig_qtd, use_container_width=True)
                
            with col_g2:
                st.markdown("#### Faturamento por Produto (R$)")
                df_fat_prod = df_vendas_itens.groupby("Produto")["Valor Total (R$)"].sum().reset_index()
                fig_fat = px.pie(
                    df_fat_prod, 
                    names="Produto", 
                    values="Valor Total (R$)",
                    hole=0.4
                )
                st.plotly_chart(fig_fat, use_container_width=True)
            
            st.markdown("---")
        
        # Tabela completa de histórico de vendas
        st.markdown("### 📋 Histórico Detalhado de Transações")
        st.dataframe(df_vendas, use_container_width=True)
        
        # Botão de download
        csv_vendas = df_vendas.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Histórico de Vendas (CSV/Excel)",
            data=csv_vendas,
            file_name='historico_vendas_mercadocarra.csv',
            mime='text/csv',
        )
    else:
        st.info("Nenhuma venda registrada até o momento.")

# ---- ABA 5: ASSISTENTE DE IA -----
with aba5:
    st.subheader("Assistente de IA")
    st.markdown("Tire as suas dúvidas sobre o estoque, vendas e produtos. Pergunte qualquer coisa relacionada ao sistema.") 

    # Padronizado para 'mensagens_chat'
    if "mensagens_chat" not in st.session_state:
        st.session_state.mensagens_chat = []

    # Exibe o histórico de mensagens
    for message in st.session_state.mensagens_chat:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Ex: Qual produto tem menos estoque hoje?"):
        st.session_state.mensagens_chat.append({"role": "user", "content": prompt})
         
        with st.chat_message("user"):
            st.markdown(prompt)

        # Coleta dados do banco
        conexao = sqlite3.connect(BD_PATH)
        df_prod = pd.read_sql_query("SELECT * FROM produtos", conexao)
        df_vendas = pd.read_sql_query("SELECT * FROM vendas", conexao) 
        conexao.close()

        contexto = f""" 
        Você é um assistente de IA para o sistema de gerenciamento de estoque e vendas do Mercado Carra.
        Aqui estão os dados do estoque e das vendas:
        
        PRODUTOS EM ESTOQUE:
        {df_prod.to_string(index=False)}

        HISTORICO DE VENDAS:
        {df_vendas.to_string(index=False)}
        
        Responda as perguntas do usuário com base nesses dados. Se a pergunta não puder ser respondida com os dados fornecidos, informe que não é possível responder no momento.
        """

        with st.chat_message("assistant"):
            with st.spinner("Analisando os dados e gerando resposta..."):
                try: 
                    prompt_completo = f"{contexto}\n\nPergunta do Gestor: {prompt}"
                    
                    # Chamada atualizada com o modelo gemini-3.8-flash
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt_completo,
                    )
                    
                    resposta_ia = response.text
                    st.markdown(resposta_ia)

                    st.session_state.mensagens_chat.append({"role": "assistant", "content": resposta_ia})
                except Exception as e:
                    st.error(f"Erro ao comunicar com a IA: {e}")
