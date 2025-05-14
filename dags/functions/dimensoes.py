import duckdb
import pandas as pd
import json

def dimensoes(conn):
    # Abrindo e carregando os dados alternativos
    # Como não são dados triviais, nem de dificil acesso, fiz manualmente.
    with open('/opt/airflow/data/municipios.json', 'r', encoding='utf-8') as m:
        municipios = json.load(m)

    with open('/opt/airflow/data/uf.json', 'r', encoding='utf-8') as u:
        ufs = json.load(u)

    # Dicionários manuais convertidos em DataFrames
    dim_raca = pd.DataFrame([
        {"CS_RACA": "1", "NOME_RACA": "Branca"},
        {"CS_RACA": "2", "NOME_RACA": "Preta"},
        {"CS_RACA": "3", "NOME_RACA": "Amarela"},
        {"CS_RACA": "4", "NOME_RACA": "Parda"},
        {"CS_RACA": "5", "NOME_RACA": "Indígena"},
        {"CS_RACA": "9", "NOME_RACA": "Ignorado"}
    ])

    dim_gestante = pd.DataFrame([
        {"CS_GESTANT": "1", "NOME_GESTANT": "1º Trimestre"},
        {"CS_GESTANT": "2", "NOME_GESTANT": "2º Trimestre"},
        {"CS_GESTANT": "3", "NOME_GESTANT": "3º Trimestre"},
        {"CS_GESTANT": "4", "NOME_GESTANT": "Idade gestacional ignorada"},
        {"CS_GESTANT": "5", "NOME_GESTANT": "Não"},
        {"CS_GESTANT": "6", "NOME_GESTANT": "Não se aplica"},
        {"CS_GESTANT": "9", "NOME_GESTANT": "Ignorado"}
    ])

    dim_escolaridade = pd.DataFrame([
        {"CS_ESCOL_N": k, "NOME_ESCOL": v} for k, v in {
            "9": "Ignorado/Branco", "99": "Ignorado/Branco",
            "0": "Analfabeto", "00": "Analfabeto",
            "1": "1ª a 4ª série incompleta do EF", "01": "1ª a 4ª série incompleta do EF",
            "2": "4ª série completa do EF", "02": "4ª série completa do EF",
            "3": "5ª a 8ª série incompleta do EF", "03": "5ª a 8ª série incompleta do EF",
            "4": "Ensino fundamental completo", "04": "Ensino fundamental completo",
            "5": "Ensino médio incompleto", "05": "Ensino médio incompleto",
            "6": "Ensino médio completo", "06": "Ensino médio completo",
            "7": "Educação superior incompleta", "07": "Educação superior incompleta",
            "8": "Educação superior completa", "08": "Educação superior completa",
            "10": "Não se aplica"
        }.items()
    ])

    dim_municipios = pd.DataFrame([
        {"ID_MUNICIP": k, "NOME_MUNICIP": v} for k, v in municipios.items()
    ])

    dim_ufs = pd.DataFrame([
        {"SG_UF": k, "UF_NOME": v} for k, v in ufs.items()
    ])

    # Salva as tabelas de dimensão no banco
    conn.register("dim_raca", dim_raca)
    conn.register("dim_gestante", dim_gestante)
    conn.register("dim_escolaridade", dim_escolaridade)
    conn.register("dim_municipios", dim_municipios)
    conn.register("dim_ufs", dim_ufs)

    conn.execute("CREATE OR REPLACE TABLE dengue.dim_raca AS SELECT * FROM dim_raca")
    conn.execute("CREATE OR REPLACE TABLE dengue.dim_gestante AS SELECT * FROM dim_gestante")
    conn.execute("CREATE OR REPLACE TABLE dengue.dim_escolaridade AS SELECT * FROM dim_escolaridade")
    conn.execute("CREATE OR REPLACE TABLE dengue.dim_municipios AS SELECT * FROM dim_municipios")
    conn.execute("CREATE OR REPLACE TABLE dengue.dim_ufs AS SELECT * FROM dim_ufs")