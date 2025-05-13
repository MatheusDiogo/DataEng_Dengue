FROM apache/airflow:3.0.1

WORKDIR /opt/airflow

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dags /opt/airflow/dags
COPY functions /opt/airflow/functions

RUN mkdir -p /opt/airflow/output
VOLUME /opt/airflow/output

EXPOSE 8080

CMD ["airflow", "standalone"]