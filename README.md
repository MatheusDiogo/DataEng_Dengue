# DataEng_Dengue
Engenharia de Dados - DATASUS Dengue

## Diagrama do Sistema

```mermaid
flowchart TD
    %% Estilo dos nós
    classDef airflow fill:#cce5ff,stroke:#007bff,stroke-width:1px;
    classDef data fill:#d4edda,stroke:#28a745,stroke-width:1px;
    classDef module fill:#ffeeba,stroke:#ffc107,stroke-width:1px;
    classDef external fill:#e2e3e5,stroke:#6c757d,stroke-width:1px;
    classDef container fill:#f8d7da,stroke:#dc3545,stroke-width:1px;
    classDef notify fill:#f5c6cb,stroke:#dc3545,stroke-width:1px;

    %% Componentes externos
    DATASUS["DATASUS - FTP/HTTP Endpoint"]:::external

    %% Orquestração - Apache Airflow
    subgraph Airflow
        Scheduler["Airflow Scheduler"]:::airflow
        Webserver["Webserver UI"]:::airflow
        Worker["Worker / Executor"]:::airflow
    end

    %% DAG principal
    Scheduler --> DAG["ETL DAG"]

    %% Módulos do DAG
    DAG --> Verifica["verificar_atualizacao.py"]:::module
    Verifica --> |Atualiza| UltimaDataTxt["ultima_data.txt"]:::data
    Verifica -->|Se há novos dados| Extract["extract.py"]:::module
    
    Extract -->|Extrai dados de| DATASUS
    Extract --> |Executa| Dimensoes["dimensoes.py"]:::module
    Extract -->|Salva dados em| SQLiteDB["SQLite: dados_sinan.db"]:::data
    
    Dimensoes --> JSONUF["municipios.json"]:::data
    Dimensoes --> JSONMun["uf.json"]:::data
    Dimensoes -->|Transforma e carrega em| SQLiteDB

    Verifica --> Email["enviar_email.py"]:::module
    Email -->|Envia resumo via| SMTP["SMTP Server"]:::notify

    %% Volumes compartilhados
    subgraph Data
        SQLiteDB["SQLite: dados_sinan.db"]:::data
        JSONUF["municipios.json"]:::data
        JSONMun["uf.json"]:::data
        UltimaDataTxt["ultima_data.txt"]:::data
    end

    %% Containerização
    Dockerfile["Dockerfile"]:::container
    Compose["docker-compose.yaml"]:::container
    Dockerfile -->|Cria imagem| Airflow
    Compose -->|Orquestra serviços e volumes| Airflow
