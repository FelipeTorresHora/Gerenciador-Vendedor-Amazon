import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from entrada import *
import os
from datetime import datetime

def main():
    st.set_page_config(page_title="Dashboard de Vendas Amazon", layout="wide")
    
    # Adiciona menu na barra lateral
    menu = st.sidebar.selectbox(
        "Menu",
        ["Dashboard", "Dashboard de Lucros", "Gestão de Preços de Compra"]
    )
    
    if menu == "Dashboard":
        mostrar_dashboard()
    elif menu == "Dashboard de Lucros":
        mostrar_dashboard_lucros()
    else:
        mostrar_gestao_precos()

def mostrar_gestao_precos():
    st.title("Gestão de Preços de Compra")
    
    # Carrega preços existentes
    precos_compra = carregar_precos_compra()
    
    # Carrega produtos únicos do DataFrame
    df = ler_arquivos()
    if df is not None:
        # Converte todos os produtos para string e remove valores nulos
        produtos = df['product-name'].astype(str).replace('nan', '').unique()
        produtos = sorted([p for p in produtos if p])  # Remove strings vazias e ordena
        
        if not produtos:
            st.warning("Nenhum produto encontrado nos dados.")
            return
        
        # Formulário para adicionar/editar preços
        with st.form("form_precos"):
            produto_selecionado = st.selectbox("Selecione o Produto", produtos)
            preco_atual = precos_compra.get(produto_selecionado, 0.0)
            novo_preco = st.number_input(
                "Preço de Compra (R$)",
                value=float(preco_atual),
                min_value=0.0,
                step=0.01
            )
            
            if st.form_submit_button("Salvar Preço"):
                precos_compra[produto_selecionado] = novo_preco
                salvar_precos_compra(precos_compra)
                st.success("Preço salvo com sucesso!")
        
        # Exibe tabela com todos os preços
        st.subheader("Preços Cadastrados")
        df_precos = pd.DataFrame(list(precos_compra.items()), columns=['Produto', 'Preço de Compra'])
        st.dataframe(df_precos)

def mostrar_dashboard():
    # Título principal
    st.title("Dashboard de Vendas Amazon")
    
    # Área de upload de arquivos
    st.header("Upload de Arquivos")
    uploaded_files = st.file_uploader(
        "Arraste ou selecione os arquivos TXT",
        type=['txt'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Salva os arquivos uploadados
        for file in uploaded_files:
            with open(os.path.join('arquivos_entrada', file.name), 'wb') as f:
                f.write(file.getbuffer())
        
        # Processa os arquivos
        df = ler_arquivos()
        
        if df is not None:
            # Converte a coluna de data
            df['purchase-date'] = pd.to_datetime(df['purchase-date'], format='%d/%m/%Y %H:%M:%S')
            
            # Sidebar com filtros
            st.sidebar.header("Filtros")
            
            # Filtro de período
            min_date = df['purchase-date'].min()
            max_date = df['purchase-date'].max()
            start_date, end_date = st.sidebar.date_input(
                "Selecione o período",
                value=[min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )
            
            # Filtro de status
            status_options = ['Todos'] + list(df['order-status'].unique())
            selected_status = st.sidebar.selectbox("Status do Pedido", status_options)
            
            # Aplica filtros
            mask = (df['purchase-date'].dt.date >= start_date) & (df['purchase-date'].dt.date <= end_date)
            if selected_status != 'Todos':
                mask = mask & (df['order-status'] == selected_status)
            
            filtered_df = df[mask]
            
            # Layout em colunas para métricas principais
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_vendas = filtered_df['item-price'].sum()
                st.metric("Total de Vendas", f"R$ {total_vendas:,.2f}")
            
            with col2:
                valor_medio = filtered_df['item-price'].mean()
                st.metric("Valor Médio por Pedido", f"R$ {valor_medio:,.2f}")
            
            with col3:
                media_diaria = filtered_df.groupby(filtered_df['purchase-date'].dt.date)['item-price'].sum().mean()
                st.metric("Média de Faturamento Diário", f"R$ {media_diaria:,.2f}")
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Vendas por Período")
                vendas_periodo = filtered_df.groupby(filtered_df['purchase-date'].dt.date)['item-price'].sum().reset_index()
                fig_vendas = px.line(vendas_periodo, x='purchase-date', y='item-price',
                                   title="Evolução das Vendas",
                                   labels={'purchase-date': 'Data', 'item-price': 'Valor Total'})
                st.plotly_chart(fig_vendas, use_container_width=True)
            
            with col2:
                st.subheader("Status dos Pedidos")
                status_count = filtered_df['order-status'].value_counts()
                fig_status = px.pie(values=status_count.values, names=status_count.index,
                                  title="Distribuição por Status")
                st.plotly_chart(fig_status, use_container_width=True)
            
            # Produtos mais vendidos
            st.subheader("Top 10 Produtos Mais Vendidos")
            produtos_vendidos = filtered_df['product-name'].value_counts().head(10)
            fig_produtos = px.bar(x=produtos_vendidos.index, y=produtos_vendidos.values,
                                title="Produtos Mais Vendidos",
                                labels={'x': 'Produto', 'y': 'Quantidade'})
            st.plotly_chart(fig_produtos, use_container_width=True)
            
            # Tabela detalhada
            st.subheader("Dados Detalhados")
            st.dataframe(filtered_df)
            
    else:
        st.info("Por favor, faça o upload dos arquivos TXT para visualizar as análises.")

def mostrar_dashboard_lucros():
    st.title("Dashboard de Lucros")
    
    # Área de upload de arquivos
    uploaded_files = st.file_uploader(
        "Arraste ou selecione os arquivos TXT",
        type=['txt'],
        accept_multiple_files=True,
        key="upload_lucros"  # Chave única para este uploader
    )
    
    if uploaded_files:
        # Processa os arquivos
        df = ler_arquivos()
        precos_compra = carregar_precos_compra()
        
        if df is not None:
            # Converte a coluna de data
            df['purchase-date'] = pd.to_datetime(df['purchase-date'], format='%d/%m/%Y %H:%M:%S')
            
            # Calcula lucro por produto
            df['preco_compra'] = df['product-name'].map(precos_compra)
            df['lucro'] = df['item-price'] - df['preco_compra']
            
            # Sidebar com filtros
            st.sidebar.header("Filtros")
            
            # Filtro de período
            min_date = df['purchase-date'].min()
            max_date = df['purchase-date'].max()
            start_date, end_date = st.sidebar.date_input(
                "Selecione o período",
                value=[min_date, max_date],
                min_value=min_date,
                max_value=max_date,
                key="date_lucros"  # Chave única para este date_input
            )
            
            # Aplica filtros
            mask = (df['purchase-date'].dt.date >= start_date) & (df['purchase-date'].dt.date <= end_date)
            filtered_df = df[mask]
            
            # Métricas de lucro
            col1, col2, col3 = st.columns(3)
            
            with col1:
                lucro_total = filtered_df['lucro'].sum()
                st.metric("Lucro Total", f"R$ {lucro_total:,.2f}")
            
            with col2:
                lucro_medio = filtered_df['lucro'].mean()
                st.metric("Lucro Médio por Venda", f"R$ {lucro_medio:,.2f}")
            
            with col3:
                margem_media = (filtered_df['lucro'] / filtered_df['item-price'] * 100).mean()
                st.metric("Margem Média", f"{margem_media:.1f}%")
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Evolução do Lucro")
                lucro_diario = filtered_df.groupby(filtered_df['purchase-date'].dt.date)['lucro'].sum().reset_index()
                fig_lucro = px.line(lucro_diario, x='purchase-date', y='lucro',
                                  title="Evolução do Lucro Diário",
                                  labels={'purchase-date': 'Data', 'lucro': 'Lucro (R$)'})
                st.plotly_chart(fig_lucro, use_container_width=True)
            
            with col2:
                st.subheader("Top 10 Produtos por Lucro")
                lucro_produto = filtered_df.groupby('product-name')['lucro'].sum().sort_values(ascending=False).head(10)
                fig_produtos = px.bar(x=lucro_produto.index, y=lucro_produto.values,
                                    title="Produtos Mais Lucrativos",
                                    labels={'x': 'Produto', 'y': 'Lucro Total (R$)'})
                st.plotly_chart(fig_produtos, use_container_width=True)
            
            # Tabela de análise de lucro
            st.subheader("Análise Detalhada de Lucro por Produto")
            analise_produtos = filtered_df.groupby('product-name').agg({
                'lucro': ['sum', 'mean'],
                'item-price': 'mean',
                'preco_compra': 'first',
                'product-name': 'count'
            }).reset_index()
            
            analise_produtos.columns = ['Produto', 'Lucro Total', 'Lucro Médio', 'Preço Médio Venda', 'Preço Compra', 'Quantidade Vendida']
            analise_produtos['Margem (%)'] = (analise_produtos['Lucro Médio'] / analise_produtos['Preço Médio Venda'] * 100).round(2)
            analise_produtos = analise_produtos.sort_values('Lucro Total', ascending=False)
            
            st.dataframe(analise_produtos)
    
    else:
        st.info("Por favor, faça o upload dos arquivos TXT para visualizar as análises de lucro.")

if __name__ == "__main__":
    main()
