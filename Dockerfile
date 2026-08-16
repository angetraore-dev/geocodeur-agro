# ===== ÉTAPE 1 : Builder =====
FROM python:3.10-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===== ÉTAPE 2 : Image finale =====
FROM python:3.10-slim

LABEL authors="angetraore-dev"
LABEL description="Géocodeur Agro-Pastoral - Côte d'Ivoire"
LABEL version="1.0"

ENV DEBIAN_FRONTEND=noninteractive

# Installer uniquement les dépendances runtime
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Copier les packages installés depuis l'étape builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

RUN useradd -m -u 1000 streamlit

WORKDIR /app
COPY . .

RUN chown -R streamlit:streamlit /app
USER streamlit

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]