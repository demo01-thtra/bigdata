FROM python:3.11-slim

# Java is required for PySpark
RUN apt-get update && \
    apt-get install -y --no-install-recommends default-jdk-headless curl && \
    rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/default-java

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Spark Kafka connector JARs
RUN mkdir -p /opt/spark-jars && \
    curl -sL -o /opt/spark-jars/spark-sql-kafka-0-10_2.12-3.5.3.jar \
      https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.3/spark-sql-kafka-0-10_2.12-3.5.3.jar && \
    curl -sL -o /opt/spark-jars/spark-token-provider-kafka-0-10_2.12-3.5.3.jar \
      https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.3/spark-token-provider-kafka-0-10_2.12-3.5.3.jar && \
    curl -sL -o /opt/spark-jars/kafka-clients-3.5.0.jar \
      https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.0/kafka-clients-3.5.0.jar && \
    curl -sL -o /opt/spark-jars/commons-pool2-2.12.0.jar \
      https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.12.0/commons-pool2-2.12.0.jar

COPY spark_job.py .

CMD ["python", "-u", "spark_job.py"]
