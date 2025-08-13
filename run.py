from app import create_app

# Cria a instância da aplicação usando a nossa "fábrica"
app = create_app()

if __name__ == '__main__':
    # Roda o servidor de desenvolvimento do Flask.
    # O debug=True é ótimo para desenvolver, pois recarrega o servidor a cada mudança.
    app.run(host='127.0.0.1', port=5000, debug=True)