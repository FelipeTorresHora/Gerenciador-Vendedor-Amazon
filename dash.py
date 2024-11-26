import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from entrada import ler_arquivos
import os
from datetime import datetime

def main():
    st.set_page_config(page_title="Dashboard de Vendas Amazon", layout="wide")
    
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

if __name__ == "__main__":
    main()
