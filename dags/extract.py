from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import duckdb
import zipfile
import io
import pandas as pd
import numpy as np
from functions.verificar_atualizacao import verificar_atualizacao
from functions.dimensoes import dimensoes

def extrair_dados():
    if verificar_atualizacao():
        url = 'https://arquivosdadosabertos.saude.gov.br/ftp/SINAN/Dengue/csv/DENGBR25.csv.zip'

        # Faz o download com stream
        response = requests.get(url, stream=True)

        # Verifica se o download foi bem-sucedido
        if response.status_code == 200:
            zip_bytes = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_bytes) as zip_file:
                csv_name = zip_file.namelist()[0]
                with zip_file.open(csv_name) as csv_file:
                    # Algumas colunas têm tipos mistos, então vamos forçar o tipo delas para string
                    colunas_com_tipos_mistos = [21,22,44,45,46,50,52,54,56,62,74,85,101]
                    dtype_dict = {col: 'str' for col in colunas_com_tipos_mistos}

                    chunks = pd.read_csv(csv_file, sep=',', encoding='latin1', dtype=dtype_dict, chunksize=50000)
                    df_pe = pd.concat([chunk[chunk['SG_UF_NOT'] == 26] for chunk in chunks])

            # Cria uma conexão com o DuckDB e cria a tabela
            conn = duckdb.connect('/opt/airflow/data/dados_sinan.db')
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

        else:
            raise Exception(f"Erro ao acessar API: {response.status_code}")

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