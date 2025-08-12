<div align="center">
<img src="https://placehold.co/800x200/0D1117/FFFFFF?text=Plataforma+de+Análise+de+Áudio+com+IA" alt="Banner do Projeto">
</div>

<h1 align="center">Plataforma de Análise de Áudio com IA</h1>

<div align="center">
<a href="https://www.python.org" target="_blank"><img src="https://img.shields.io/badge/Python-3.11-blue.svg" alt="Python Version"></a>
<a href="https://flask.palletsprojects.com/" target="_blank"><img src="https://img.shields.io/badge/Flask-2.3-black.svg" alt="Flask Version"></a>
<a href="https://www.docker.com/" target="_blank"><img src="https://img.shields.io/badge/Docker-Ready-blue.svg" alt="Docker Ready"></a>
<a href="https://cloud.google.com" target="_blank"><img src="https://img.shields.io/badge/Google_Cloud-Integrated-orange.svg" alt="Google Cloud Integrated"></a>
<a href="./https://www.google.com/search?q=LICENSE" target="_blank"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
</div>

<p align="center">
Uma plataforma web full-stack que utiliza múltiplos modelos de Inteligência Artificial para transcrever arquivos de áudio e texto, realizar análises avançadas e apresentar os insights em um dashboard interativo.
</p>

✨ Funcionalidades Principais
📊 Dashboard Interativo: Visualize métricas agregadas, distribuição de sentimentos e principais tópicos em gráficos dinâmicos.

🗂️ Processamento em Lotes: Faça o upload de múltiplos arquivos de áudio (.wav, .mp3, .ogg) ou texto (.txt) de uma só vez.

🤖 Múltiplos Modelos de IA:

Transcrição: Escolha entre modelos locais de alta performance (OpenAI Whisper, Faster-Whisper) e modelos de nuvem (Google Chirp) com diarização de locutor.

Análise: Utiliza o poder do Google Gemini para extrair resumo, sentimento, tópico principal e itens de ação de cada transcrição.

🗄️ Histórico e Detalhes: Navegue pelo histórico de lotes processados, veja o status de cada arquivo e analise os resultados individuais num modal detalhado.

☁️ Seguro e Escalável: A aplicação é totalmente "containerizada" com Docker e pronta para deploy na nuvem (Google App Engine).

🛠️ Tecnologias Utilizadas
Backend: Flask (Python)

Frontend: HTML5, Tailwind CSS, JavaScript (com Chart.js)

Banco de Dados: SQLite (para desenvolvimento), com suporte para PostgreSQL (em produção)

Modelos de IA:

Google Gemini 1.5 Flash

Google Chirp

OpenAI Whisper

Faster-Whisper

Infraestrutura: Docker, Docker Compose, Gunicorn

Plataforma de Nuvem: Google Cloud (App Engine, Vertex AI)

🚀 Como Executar o Projeto Localmente
Siga os passos abaixo para ter a aplicação a rodar na sua máquina.

1. Pré-requisitos
Git

Docker Desktop

Google Cloud CLI

2. Configuração do Ambiente
Clone o repositório:

git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
cd SEU_REPOSITORIO

Autentique-se no Google Cloud:
Este comando abrirá um navegador para fazer login e dará à aplicação as permissões necessárias para usar as APIs da Google.

gcloud auth application-default login

Crie o arquivo de variáveis de ambiente:
Crie um arquivo chamado .env na raiz do projeto e adicione a sua chave da API do Google AI Studio (Gemini).

# Substitua pela sua chave real
GOOGLE_API_KEY="AIzaSy...xxxxxxxx"

Inicialize o banco de dados local:
Este script criará o arquivo database.db com todas as tabelas necessárias.

python init_db.py

3. Execute com Docker
Construa a imagem e inicie o contêiner:
O Docker cuidará de instalar todas as dependências e iniciar o servidor.

docker-compose up --build

Acesse a aplicação:
Abra o seu navegador e acesse: http://127.0.0.1:5000

🕹️ Como Usar
Navegue para a aba Lotes.

Selecione um ou mais arquivos de áudio/texto.

Opcionalmente, dê um nome para o lote.

Clique em "Enviar para Análise".

Acompanhe o status do processamento na tabela de lotes.

Quando concluído, volte para a aba Dashboard para ver os insights atualizados. Clique numa análise na tabela inferior para ver os detalhes completos.

🖼️ Screenshots
<div align="center">
<img src="http://googleusercontent.com/file_content/11" alt="Dashboard da Aplicação" style="width: 80%; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
</div>

📄 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.
