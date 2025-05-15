FROM apache/airflow:3.0.1

# Define o diretório de trabalho
WORKDIR /opt/airflow

# Instala dependências extras do Python (sem reinstalar o Airflow)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia os DAGs para o diretório padrão
COPY dags /opt/airflow/dags

# Cria e monta volume para dados (se necessário)
RUN mkdir -p /opt/airflow/data
VOLUME /opt/airflow/data

# Expõe a porta padrão da interface web do Airflow
EXPOSE 8080

# Define o usuário que executa o container (já definido na imagem oficial como 'airflow')
USER airflow
