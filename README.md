````markdown
<div align="center">
  <h1 align="center">Plataforma de Análise de Áudio com IA</h1>
  <p align="center">
    Uma aplicação web moderna em Python e Flask, refatorada para máxima organização, escalabilidade e melhores práticas de desenvolvimento.
  </p>
</div>

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/Flask-2.3-000000?style=for-the-badge&logo=flask" alt="Flask Version">
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-d71f00?style=for-the-badge&logo=sqlalchemy" alt="SQLAlchemy Version">
  <img src="https://img.shields.io/badge/Frontend-TailwindCSS-38B2AC?style=for-the-badge&logo=tailwind-css" alt="Tailwind CSS">
</div>

## ✨ Visão Geral do Projeto

Esta plataforma é uma ferramenta poderosa para transcrever e analisar arquivos de áudio ou texto. Construída sobre uma arquitetura de microsserviços desacoplada, ela permite o processamento assíncrono de arquivos, análise de sentimento, identificação de tópicos e resumo de conteúdo através de modelos de Inteligência Artificial de ponta, como o **Google Gemini** e o **Chirp**.

O projeto foi completamente refatorado de uma base de código monolítica para uma estrutura moderna, organizada e escalável, seguindo as melhores práticas da indústria.

### Funcionalidades Principais

* **Upload em Lotes**: Envie múltiplos arquivos de áudio (`.wav`, `.mp3`, etc.) ou texto (`.txt`) de uma só vez.
* **Seleção de Provedor**: Escolha dinamicamente qual motor de IA usar para a transcrição (ex: Google Chirp ou uma API externa).
* **Processamento Assíncrono**: As tarefas de transcrição e análise rodam em background (usando `threading`), permitindo que o usuário continue navegando sem travamentos.
* **Análise com Gemini**: Utiliza o poder do Google Gemini para extrair insights valiosos de cada transcrição, incluindo:
    * Análise de Sentimento (Positivo, Negativo, Neutro)
    * Identificação do Tópico Principal
    * Resumo Executivo
* **Dashboard Interativo**: Visualize os resultados em um dashboard dinâmico com gráficos de sentimento, tópicos e um histórico detalhado de todas as análises.

## 🛠️ Stack Tecnológica

| Categoria        | Tecnologia                               | Propósito                                       |
| :--------------- | :--------------------------------------- | :---------------------------------------------- |
| **Backend** | Python 3.11, Flask, Gunicorn             | Lógica da aplicação e servidor web              |
| **Banco de Dados** | SQLAlchemy ORM, Flask-SQLAlchemy         | Interação com o banco de dados (SQLite/Postgres) |
| **Frontend** | HTML5, Tailwind CSS, JavaScript, Chart.js| Interface do usuário e visualização de dados   |
| **DevOps** | Docker (opcional), Variáveis de Ambiente (`.env`) | Containerização e gerenciamento de configuração |
| **IA & APIs** | Google Vertex AI (Gemini, Chirp), Requests | Serviços de IA e comunicação com APIs externas  |

## 🚀 Como Executar o Projeto

Siga os passos abaixo para ter a aplicação rodando na sua máquina local.

### 1. Pré-requisitos

* Python 3.10 ou superior.
* Conta no Google Cloud com a API Vertex AI ativada.
* Uma chave de acesso de Service Account em formato JSON (se for rodar localmente).

### 2. Configuração do Ambiente

**a. Clone o repositório:**
```bash
git clone <URL_DO_SEU_REPOSITORIO>
cd plataforma_analise_ia
````

**b. Crie e configure o arquivo de ambiente:**
Copie o arquivo de exemplo. Este passo é crucial para armazenar suas chaves de API de forma segura.

```bash
cp .env.example .env
```

Agora, abra o arquivo `.env` com seu editor de texto e preencha as variáveis com suas credenciais. Para autenticação com o Google Cloud, a forma mais fácil é adicionar a seguinte linha:

```
# no seu arquivo .env
GOOGLE_APPLICATION_CREDENTIALS="caminho/para/sua/chave-de-servico.json"
```

**Importante:** Adicione o nome da sua chave `.json` e o arquivo `.env` ao seu `.gitignore` para nunca enviá-los a um repositório público\!

**c. Crie e ative um ambiente virtual:**
É uma boa prática isolar as dependências do seu projeto.

```bash
# Criar o ambiente
python -m venv venv

# Ativar no Linux/macOS
source venv/bin/activate

# Ativar no Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```

**d. Instale as dependências:**

```bash
pip install -r requirements.txt
```

### 3\. Inicialize o Banco de Dados

Com o ambiente virtual ativado, use o comando customizado do Flask que criamos para gerar o banco de dados:

```bash
flask init-db
```

Este comando irá ler seus `models.py` e criar um arquivo `database.db` (SQLite) na raiz do projeto.

### 4\. Rode a Aplicação

Finalmente, inicie o servidor de desenvolvimento do Flask:

```bash
flask run
```

Ou simplesmente:

```bash
python run.py
```

Acesse a aplicação no seu navegador em **http://127.0.0.1:5000**.

## 🏛️ Arquitetura do Software

A codebase foi reestruturada para seguir padrões de design que promovem a separação de responsabilidades (SoC).

  * **`run.py`**: Ponto de entrada da aplicação.
  * **`config.py`**: Centraliza todas as configurações, lendo do arquivo `.env`.
  * **`/app`**: O coração da aplicação Flask.
      * **`__init__.py`**: Utiliza o padrão **Application Factory** (`create_app`) para inicializar o app, extensões e blueprints.
      * **`models.py`**: Define a estrutura do banco de dados usando classes do **SQLAlchemy ORM**, eliminando a necessidade de SQL bruto.
      * **`routes.py`**: Contém todas as rotas da API (endpoints), atuando como a camada de controle (Controller). As rotas são organizadas com **Flask Blueprints**.
      * **`services.py`**: Contém toda a lógica de negócio (o "cérebro"). As rotas chamam funções daqui para fazer o trabalho pesado, como processar arquivos, chamar APIs de IA e interagir com o banco de dados.
      * **`/templates`** e **`/static`**: Contêm os arquivos de frontend (HTML, CSS, JS), mantendo a interface do usuário completamente separada do backend.

Este design torna o código mais limpo, mais fácil de testar, manter e escalar.

```
