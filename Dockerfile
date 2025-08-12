# --- Estágio 1: Build - Instalação de dependências Python ---
# Usamos uma imagem base mais leve e eficiente
FROM python:3.11-slim-bookworm AS builder

# Define variáveis de ambiente para otimizar a instalação do pip
ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Instala dependências do sistema primeiro
RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia apenas o ficheiro de requisitos para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências em uma ordem lógica para evitar conflitos
# 1. Instala PyTorch primeiro, pois é uma dependência pesada e específica.
# 2. Instala as bibliotecas de IA que podem ter dependências conflitantes.
# 3. Instala o resto dos requisitos do ficheiro.
# 4. FORÇA a instalação da versão correta do google-cloud-speech por último, sobrepondo qualquer outra versão.
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install openai-whisper faster-whisper "transformers[torch]" accelerate sentencepiece && \
    pip install -r requirements.txt && \
    pip install --upgrade "google-cloud-speech>=2.20.0"

# --- Estágio 2: Final - Criação da imagem de produção ---
FROM python:3.11-slim-bookworm

WORKDIR /app

# Copia as dependências do sistema do estágio de build
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Copia os pacotes Python instalados do estágio de build
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copia os ficheiros da aplicação para o container
# Esta linha é para produção. Para desenvolvimento, o docker-compose.override.yml usará um volume.
COPY . .

EXPOSE 5000

# Comando de produção (será sobreposto em desenvolvimento pelo override)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]