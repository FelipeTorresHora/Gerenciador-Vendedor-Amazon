import pandas as pd
import glob
import os

def ler_arquivos(diretorio_entrada='arquivos_entrada', diretorio_saida='arquivos_processados'):
    # Cria os diretórios se não existirem
    os.makedirs(diretorio_entrada, exist_ok=True)
    os.makedirs(diretorio_saida, exist_ok=True)
    
    # Colunas que queremos manter
    colunas_desejadas = [
        'amazon-order-id',
        'purchase-date',
        'order-status',
        'product-name',
        'sku',
        'asin',
        'item-status',
        'item-price',
        'item-tax',
        'shipping-price',
        'ship-city',
        'ship-state',
        'payment-method-details'
    ]
    
    # Lista todos os arquivos .txt no diretório atual E na pasta de entrada
    arquivos = glob.glob('*.txt') + glob.glob(os.path.join(diretorio_entrada, '*.txt'))
    
    if not arquivos:
        print("Nenhum arquivo .txt encontrado")
        return None
    
    # Lista para armazenar os dataframes
    dfs = []
    dfs_originais = []  # Nova lista para dados originais
    
    # Lê cada arquivo e adiciona à lista
    for arquivo in arquivos:
        try:
            # Lê o arquivo original completo
            df_original = pd.read_csv(arquivo, sep='\t')
            dfs_originais.append(df_original)
            
            # Processa versão filtrada
            df = df_original.copy()
            colunas_existentes = [col for col in colunas_desejadas if col in df.columns]
            df = df[colunas_existentes]
            dfs.append(df)
        except Exception as e:
            print(f"Erro ao processar o arquivo {arquivo}: {str(e)}")
    
    if not dfs:
        print("Nenhum dado foi processado com sucesso")
        return None
    
    # Concatena os dataframes originais
    df_original_completo = pd.concat(dfs_originais, ignore_index=True)
    
    # Salva os dados brutos originais
    caminho_dados_brutos = os.path.join(diretorio_saida, 'dados_combinados.xlsx')
    df_original_completo.to_excel(caminho_dados_brutos, index=False)
    print(f"Dados brutos salvos em: {caminho_dados_brutos}")
    
    # Concatena os dataframes filtrados
    df_final = pd.concat(dfs, ignore_index=True)
    
    # Processa os dados para criar a versão final tratada
    df_tratado = tratar_dados(df_final)
    
    # Salva os dados tratados
    caminho_dados_tratados = os.path.join(diretorio_saida, 'dados_finais.xlsx')
    df_tratado.to_excel(caminho_dados_tratados, index=False)
    print(f"Dados tratados salvos em: {caminho_dados_tratados}")
    
    return df_tratado

def tratar_dados(df):
    """
    Função para tratar os dados do DataFrame com tratamentos específicos para cada coluna
    """
    df = df.copy()
    
    # Converte a coluna de data para datetime (mantém formato original para ordenação)
    df['purchase-date'] = pd.to_datetime(df['purchase-date'])
    
    # Ordena por amazon-order-id, data e status (Shipped tem prioridade)
    df = df.sort_values(
        by=['amazon-order-id', 'purchase-date', 'item-status'],
        ascending=[True, False, True]  # False na data para pegar a mais recente
    )
    
    # Remove duplicatas mantendo o primeiro registro (que será o Shipped mais recente)
    df = df.drop_duplicates(subset=['amazon-order-id'], keep='first')
    
    # Agora formata a data para o padrão brasileiro
    df['purchase-date'] = df['purchase-date'].dt.strftime('%d/%m/%Y %H:%M:%S')
    
    # Trata a coluna order-status
    df['order-status'] = df['order-status'].map({
        'Shipped': 'Enviado',
        'Cancelled': 'Cancelado',
        'Pending': 'Pendente'
    })
    
    # Trata a coluna item-status
    df['item-status'] = df['item-status'].map({
        'Shipped': 'Enviado',
        'Unshipped': 'Não Enviado'
    })
    
    # Converte colunas de preço para número e formata para 2 casas decimais
    colunas_preco = ['item-price', 'item-tax', 'shipping-price']
    for coluna in colunas_preco:
        if coluna in df.columns:
            # Remove caracteres especiais e converte para float
            df[coluna] = df[coluna].astype(str).str.replace('$', '').str.replace(',', '').astype(float)
            # Formata para 2 casas decimais
            df[coluna] = df[coluna].round(2)
    
    # Padroniza nomes de estados
    estados_map = {
        'Espirito Santo': 'ES',
        'Rondônia': 'RO'
    }
    df['ship-state'] = df['ship-state'].replace(estados_map)
    
    # Trata a coluna payment-method-details
    df['payment-method-details'] = df['payment-method-details'].map({
        'Installments': 'Parcelado',
        'CreditCard': 'Cartão de Crédito',
        'Other': 'Outros'
    })
    
    # Remove linhas duplicadas
    df = df.drop_duplicates()
    
    # Limpa espaços em branco extras em todas as colunas de texto
    colunas_texto = df.select_dtypes(include=['object']).columns
    for coluna in colunas_texto:
        df[coluna] = df[coluna].str.strip()
    
    # Substitui valores vazios ou '----------' por None/NaN
    df = df.replace(['', '----------'], pd.NA)
    
    return df

def salvar_precos_compra(produtos_precos):
    """
    Salva os preços de compra dos produtos em um arquivo Excel
    """
    # Converte todos os valores para float antes de salvar
    produtos_precos = {k: float(v) for k, v in produtos_precos.items()}
    df_precos = pd.DataFrame(list(produtos_precos.items()), columns=['product-name', 'preco_compra'])
    caminho_precos = os.path.join('arquivos_processados', 'precos_compra.xlsx')
    df_precos.to_excel(caminho_precos, index=False)

def carregar_precos_compra():
    """
    Carrega os preços de compra dos produtos do arquivo Excel
    """
    caminho_precos = os.path.join('arquivos_processados', 'precos_compra.xlsx')
    if os.path.exists(caminho_precos):
        df_precos = pd.read_excel(caminho_precos)
        # Garante que a coluna preco_compra seja float
        df_precos['preco_compra'] = pd.to_numeric(df_precos['preco_compra'], errors='coerce')
        return df_precos.set_index('product-name')['preco_compra'].to_dict()
    return {}

# Executa a função e mostra as informações
df = ler_arquivos()
