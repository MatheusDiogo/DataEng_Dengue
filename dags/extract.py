from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import duckdb
import zipfile
import os
import numpy as np
from functions.verificar_atualizacao import verificar_atualizacao
from functions.dimensoes import dimensoes
from functions.download_arquivo import download_arquivo

def extrair_dados():
    if verificar_atualizacao():
        url = 'https://arquivosdadosabertos.saude.gov.br/ftp/SINAN/Dengue/csv/DENGBR25.csv.zip'
        caminho_zip = '/opt/airflow/data/DENGBR25.csv.zip'

        # Baixa o arquivo direto para o disco, sem carregar na memória
        download_arquivo(url, caminho_zip)

        print("Dados baixados no disco com Sucesso!")

        with zipfile.ZipFile(caminho_zip, 'r') as zip_file:
            csv_interno = zip_file.namelist()[0]
            caminho_csv_extraido = os.path.join('/opt/airflow/data', csv_interno)
            zip_file.extract(csv_interno, path='/opt/airflow/data')
            
            query = f"""
                SELECT *
                FROM read_csv_auto('{caminho_csv_extraido}', delim=',', header=True, encoding='latin-1')
                WHERE SG_UF_NOT = '26' OR UF = '26' OR COUFINF = '26'
            """
            # Usar o DuckDB para ler do arquivo no disco
            conn = duckdb.connect('/opt/airflow/data/dados_sinan.db')

            df_pe = conn.execute(query).fetchdf()

            # Salvar como parquet (Boa ideia para suubir em um lake)
            #df_pe.to_parquet('/opt/airflow/data/dengue_PE.parquet')

            # Cria o SCHEMA das tabelas
            conn.execute("CREATE SCHEMA IF NOT EXISTS dengue") # Cria o schema dengue se não existir. Dessa forma, pode-se criar tabelas de outros estados no mesmo schema (Mais otimizado)

            # Registra o DataFrame como uma tabela temporária
            conn.register('df_pe', df_pe)

            # Substitui a tabela se já existir
            conn.execute("DROP TABLE IF EXISTS dengue.dengue_pe")

            # Cria a tabela com os dados do DataFrame
            conn.execute("CREATE TABLE dengue.dengue_pe AS SELECT * FROM df_pe")

            print(conn.sql("SELECT * FROM dengue.dengue_pe").to_df().head()) # Validar extração

            # Fecha a conexão
            conn.close()

        # Apaga os arquivos para liberar espaço
        try:
            os.remove(caminho_zip)
            os.remove(caminho_csv_extraido)
            print("Arquivos temporários removidos com sucesso.")
        except Exception as e:
            print(f"Erro ao remover arquivos temporários: {e}")    

def transformar_dados():
    print("Iniciando transformação")
    
    # Cria uma conexão com o DuckDB e carrega a tabela
    conn = duckdb.connect('/opt/airflow/data/dados_sinan.db')

    cinan_df = conn.sql("SELECT * FROM dengue.dengue_pe").to_df()

    print("Dados do banco carregados com sucesso!")

    # Criando tabelas de dimensoes
    dimensoes(conn)

    print("Dimensoes criadas com sucesso!")

    # Colunas onde 1 = Sim e 2 Não
    colunas_sn = [
        'FEBRE', 'MIALGIA', 'CEFALEIA', 'EXANTEMA', 'VOMITO',
        'NAUSEA', 'DOR_COSTAS', 'CONJUNTVIT', 'ARTRITE', 'ARTRALGIA',
        'PETEQUIA_N', 'LEUCOPENIA', 'LACO', 'DOR_RETRO', 'DIABETES',
        'HEMATOLOG', 'HEPATOPAT', 'RENAL', 'HIPERTENSA', 'ACIDO_PEPT',
        'AUTO_IMUNE', 'ALRM_HIPOT', 'ALRM_PLAQ', 'ALRM_VOM', 'ALRM_SANG',
        'ALRM_HEMAT', 'ALRM_ABDOM', 'ALRM_LETAR', 'ALRM_HEPAT', 'ALRM_LIQ',
        'GRAV_PULSO', 'GRAV_CONV', 'GRAV_ENCH', 'GRAV_INSUF', 'GRAV_TAQUI',
        'GRAV_EXTRE', 'GRAV_HIPOT', 'GRAV_HEMAT', 'GRAV_MELEN', 'GRAV_METRO',
        'GRAV_SANG', 'GRAV_AST', 'GRAV_MIOC', 'GRAV_CONSC', 'GRAV_ORGAO',
        'MANI_HEMOR', 'EPISTAXE', 'GENGIVO', 'METRO', 'PETEQUIAS',
        'HEMATURA', 'SANGRAM', 'LACO_N', 'PLASMATICO', 'EVIDENCIA',
        'PLAQ_MENOR', 'CON_FHD', 'COMPLICA', 'DOENCA_TRA', 'HOSPITALIZ'
    ]

    # Vamos transformar em Bool para facilitar calculos e outras transformações do time de análise
    for col in colunas_sn:
        cinan_df[col] = cinan_df[col].map({'1': True, '2': False, '9': np.nan}).astype('boolean') # Nesssa conversão Nan continua Nan

    # Substitui a tabela se já existir
    conn.execute("DROP TABLE IF EXISTS dengue.dengue_pe_fat")
        
    conn.execute("CREATE TABLE dengue.dengue_pe_fat AS SELECT * FROM cinan_df")

    # Fecha a conexão
    conn.close()

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1, 7),
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

dag = DAG(
    dag_id='dados_dengue_pe',
    default_args=default_args,
    schedule="0 7 * * *", # Precisamos ver a hora do servidor/máquina que a aplicação ficará para sincronizar com o início do expediente.
    catchup=False,
)

task_checar_datasus = PythonOperator(
    task_id="extrair_dados",
    python_callable=extrair_dados,
    dag=dag
)

task_transformar_dados = PythonOperator(
    task_id="transformar_dados",
    python_callable=transformar_dados,
    dag=dag
)

# Definindo a ordem de execução
task_checar_datasus >> task_transformar_dados