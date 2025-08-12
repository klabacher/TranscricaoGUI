import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Banco de dados antigo '{db_path}' removido.")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("Conexão com o novo banco de dados estabelecida.")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    ''')
    print("Tabela 'batches' criada com sucesso.")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transcriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        upload_date TEXT NOT NULL,
        status TEXT NOT NULL,
        batch_id INTEGER,
        transcript_text TEXT,
        audio_hash TEXT,
        FOREIGN KEY (batch_id) REFERENCES batches (id)
    );
    ''')
    print("Tabela 'transcriptions' criada com sucesso.")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transcription_id INTEGER,
        sentiment TEXT,
        topic TEXT,
        summary TEXT,
        full_analysis_json TEXT,
        FOREIGN KEY (transcription_id) REFERENCES transcriptions (id)
    );
    ''')
    print("Tabela 'analyses' criada com sucesso.")

    conn.commit()
    print("\nOperações confirmadas no banco de dados.")

except sqlite3.Error as e:
    print(f"Ocorreu um erro de banco de dados: {e}")

finally:
    if conn:
        conn.close()
        print("Conexão com o banco de dados fechada.")

print("\nBanco de dados inicializado com sucesso!")
