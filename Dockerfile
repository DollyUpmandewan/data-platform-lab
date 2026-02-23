FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY pipeline ./pipeline
RUN pip install --no-cache-dir . && useradd --create-home worker && mkdir /app/data /app/reports && chown -R worker:worker /app
USER worker
ENTRYPOINT ["python", "-m", "pipeline.cli"]
