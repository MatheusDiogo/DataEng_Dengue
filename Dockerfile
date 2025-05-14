FROM apache/airflow:3.0.1

WORKDIR /opt/airflow

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dags /opt/airflow/dags

RUN mkdir -p /opt/airflow/data
VOLUME /opt/airflow/data

EXPOSE 8080

CMD ["airflow", "standalone"]