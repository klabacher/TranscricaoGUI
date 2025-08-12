<div align="center">
<img src="https://placehold.co/800x200/0D1117/FFFFFF?text=Plataforma+de+Análise+de+Áudio+com+IA" alt="Banner do Projeto">
</div>

<h1 align="center">Plataforma de Análise de Áudio com IA (Cloud-Native)</h1>

<div align="center">
<a href="https://www.python.org" target="_blank"><img src="https://img.shields.io/badge/Python-3.11-blue.svg" alt="Python Version"></a>
<a href="https://flask.palletsprojects.com/" target="_blank"><img src="https://img.shields.io/badge/Flask-2.3-black.svg" alt="Flask Version"></a>
<a href="https://cloud.google.com/appengine" target="_blank"><img src="https://img.shields.io/badge/Google_App_Engine-Deploy-blueviolet.svg" alt="Google App Engine"></a>
<a href="https://cloud.google.com" target="_blank"><img src="https://img.shields.io/badge/Google_Cloud-Native-orange.svg" alt="Google Cloud Native"></a>
<a href="./LICENSE" target="_blank"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
</div>

<p align="center">
Uma plataforma web 100% nativa na nuvem que utiliza os serviços da Google Cloud para transcrever e analisar ficheiros de áudio de forma escalável, robusta e assíncrona.
</p>

✨ Funcionalidades Principais
☁️ Arquitetura Cloud-Native: O projeto foi refatorado para rodar inteiramente na Google Cloud, usando App Engine, Cloud SQL, Cloud Storage e Cloud Tasks.

📊 Dashboard Interativo: Visualize métricas agregadas, distribuição de sentimentos e principais tópicos em gráficos dinâmicos.

🗂️ Processamento Assíncrono e Confiável: Uploads de ficheiros são enviados para o Cloud Storage e uma tarefa é criada no Cloud Tasks, garantindo que o processamento ocorra em background sem sobrecarregar a aplicação.

🤖 Análise com IA da Google:

Transcrição: Utiliza o modelo Google Chirp para transcrições de alta qualidade com diarização de locutor.

Análise de Conteúdo: Emprega o Google Gemini para extrair resumos, sentimentos e tópicos de cada transcrição.

🗄️ Histórico e Detalhes: Navegue pelo histórico de lotes processados, veja o status de cada ficheiro e analise os resultados individuais.

🛠️ Stack Tecnológica
Backend: Flask (Python)

Frontend: HTML5, Tailwind CSS, JavaScript (com Chart.js)

Banco de Dados: Google Cloud SQL (PostgreSQL)

Armazenamento: Google Cloud Storage

Fila de Tarefas: Google Cloud Tasks

Computação: Google App Engine

Modelos de IA: Google Gemini & Google Chirp (via Vertex AI)

🚀 Guia de Configuração e Deploy na Google Cloud
Este guia detalha todos os passos necessários para configurar o ambiente na Google Cloud e fazer o deploy da aplicação.

Passo 1: Pré-requisitos
Uma conta Google Cloud com um Cartão de Crédito associado.

Google Cloud CLI (gcloud) instalado na sua máquina.

Passo 2: Configuração Inicial do Projeto na Google Cloud
Crie um novo projeto no Console do Google Cloud. Anote o ID do Projeto (ex: meu-projeto-ia-12345).

Ative o Faturamento para o projeto. A maioria dos serviços necessários exige que o faturamento esteja ativo.

No console, vá para Faturamento > Vincular uma conta de faturamento.

Ative as APIs necessárias. Para cada API abaixo, vá até a sua página no console e clique em "Ativar":

App Engine Admin API

Cloud SQL Admin API

Cloud Storage API

Cloud Tasks API

Vertex AI API

Cloud Build API (geralmente ativada pelo deploy do App Engine)

Passo 3: Criação dos Recursos na Nuvem
Cloud Storage (Bucket)

Vá para Cloud Storage > Buckets e clique em Criar.

Dê um nome único global para o seu bucket (ex: bucket-transcricoes-meuprojeto).

Escolha a mesma região que usará para os outros serviços (ex: southamerica-east1).

Mantenha as outras configurações como padrão e crie o bucket.

Cloud SQL (PostgreSQL)

Vá para SQL e clique em Criar Instância.

Escolha PostgreSQL.

Dê um ID de Instância (ex: db-transcricoes).

Defina uma senha forte para o utilizador postgres. Guarde esta senha!

Escolha a mesma região dos outros serviços.

Após a criação, clique na instância e copie o Nome da conexão da instância. Ele terá o formato ID_DO_PROJETO:REGIAO:ID_DA_INSTANCIA.

Cloud Tasks (Fila)

Vá para Cloud Tasks e clique em Criar Fila.

Dê o nome (ID da Fila) transcription-queue.

Escolha a mesma região dos outros serviços.

Passo 4: Configuração do Código Local
Clone o repositório do GitHub:

git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
cd SEU_REPOSITORIO

Configure o app.yaml:
Abra o ficheiro app.yaml e substitua os valores na secção env_variables pelos recursos que você acabou de criar.

runtime: python311
entrypoint: gunicorn -b :$PORT --workers 1 --threads 8 --timeout 0 app:app

instance_class: F4_1G
automatic_scaling:
  min_instances: 0
  max_instances: 2

env_variables:
  # SUBSTITUA PELOS SEUS VALORES REAIS
  GCS_BUCKET_NAME: "nome-do-seu-bucket-unico"
  DB_USER: "postgres"
  DB_PASS: "SUA_SENHA_FORTE_DO_BANCO_DE_DADOS"
  DB_NAME: "postgres"
  INSTANCE_CONNECTION_NAME: "SEU_PROJETO:sua-regiao:sua-instancia-sql"

Passo 5: Deploy da Aplicação
Autentique-se com a gcloud CLI:
Abra um terminal na pasta do projeto e execute os comandos para fazer login com a sua conta Google e definir o projeto correto.

gcloud auth login
gcloud config set project SEU_ID_DE_PROJETO

Faça o deploy:
Este comando irá enviar o seu código para o App Engine, que irá construir a imagem e iniciar a sua aplicação.

gcloud app deploy

Acesse a sua aplicação:
Após o deploy ser concluído, o terminal mostrará o URL da sua aplicação. Ele será algo como https://SEU_ID_DE_PROJETO.uc.r.appspot.com.

Parabéns! A sua plataforma está agora a funcionar 100% na nuvem.
