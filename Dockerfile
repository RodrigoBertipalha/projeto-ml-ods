FROM python:3.11-slim@sha256:61e01f72680f86a5279ad510818ab7b2ee9f049822589d4e34e33e044360356c

ENV SEED=42
WORKDIR /app

# libexpat1 é necessária para importar o rasterio.
RUN apt-get update && apt-get install -y --no-install-recommends make libexpat1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY Makefile ./
COPY configs/ ./configs/
COPY src/ ./src/

CMD ["python", "-c", "import os; import duckdb, geobr, geopandas, numpy, pandas, pyarrow, rasterio; print('Ambiente pronto. SEED=' + os.environ['SEED'] + '. Pipeline de treinamento ainda não implementado.')"]
