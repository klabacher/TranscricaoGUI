import sys
import requests # Não esqueça de instalar com: pip install requests
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QListWidget, QListWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt
import os

public_url_gui = os.getenv("PUBLIC_URL_GUI")
public_url_api = os.getenv("PUBLIC_URL_API", "http://127.0.0.1:8000")

# URL base da sua API. Se você rodar em outra porta, mude aqui.
API_URL = public_url_api
class TodoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Lista de Tarefas - API Conectada')
        self.setGeometry(100, 100, 500, 400)
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # --- Widgets ---
        self.task_list = QListWidget()
        
        self.input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Digite uma nova tarefa...")
        self.add_button = QPushButton("Adicionar")
        
        self.input_layout.addWidget(self.task_input)
        self.input_layout.addWidget(self.add_button)
        
        self.button_layout = QHBoxLayout()
        self.complete_button = QPushButton("Marcar como Concluída")
        self.delete_button = QPushButton("Remover Tarefa")
        
        self.button_layout.addWidget(self.complete_button)
        self.button_layout.addWidget(self.delete_button)
        
        # --- Adicionando widgets ao layout principal ---
        self.layout.addWidget(self.task_list)
        self.layout.addLayout(self.input_layout)
        self.layout.addLayout(self.button_layout)
        
        # --- Conectando os sinais (eventos de clique) ---
        self.add_button.clicked.connect(self.add_task)
        self.task_input.returnPressed.connect(self.add_task)
        self.complete_button.clicked.connect(self.complete_task)
        self.delete_button.clicked.connect(self.delete_task)
        
        # Carrega as tarefas da API ao iniciar
        self.load_tasks()

    def handle_api_error(self, response):
        """Mostra uma mensagem de erro mais detalhada da API."""
        try:
            detail = response.json().get('detail', response.text)
        except Exception:
            detail = response.text
        QMessageBox.warning(self, "Erro na API", f"Ocorreu um erro: {detail}")

    def load_tasks(self):
        """Busca as tarefas da API e atualiza a lista na tela."""
        self.task_list.clear()
        try:
            # CORREÇÃO: O endpoint correto é /tarefas/
            response = requests.get(f"{API_URL}/tarefas/")
            if response.status_code == 200:
                tasks = response.json()
                for task in tasks:
                    item = QListWidgetItem(task['descricao'])
                    item.setData(Qt.ItemDataRole.UserRole, task) 
                    
                    if task['concluida']:
                        font = item.font()
                        font.setStrikeOut(True)
                        item.setFont(font)
                        item.setForeground(Qt.GlobalColor.gray)
                    
                    self.task_list.addItem(item)
            else:
                self.handle_api_error(response)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Erro de Conexão", f"Não foi possível conectar à API: {e}\n\nVerifique se a API está rodando em {API_URL}.")

    def add_task(self):
        """Envia uma nova tarefa para a API."""
        task_text = self.task_input.text().strip()
        if task_text:
            try:
                # CORREÇÃO: O endpoint correto é /tarefas/ e o corpo é o objeto TarefaCreate
                new_task_data = {"descricao": task_text, "concluida": False}
                response = requests.post(f"{API_URL}/tarefas/", json=new_task_data)
                if response.status_code == 200:
                    self.task_input.clear()
                    self.load_tasks()
                else:
                    self.handle_api_error(response)
            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Erro de Conexão", f"Não foi possível adicionar a tarefa: {e}")

    def complete_task(self):
        """Marca a tarefa selecionada como concluída na API."""
        current_item = self.task_list.currentItem()
        if not current_item:
            return

        task_data = current_item.data(Qt.ItemDataRole.UserRole)
        task_id = task_data['id']
        
        try:
            # CORREÇÃO: O endpoint correto é /tarefas/{tarefa_id}/concluir
            response = requests.put(f"{API_URL}/tarefas/{task_id}/concluir")
            if response.status_code == 200:
                self.load_tasks()
            else:
                self.handle_api_error(response)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Erro de Conexão", f"Não foi possível concluir a tarefa: {e}")

    def delete_task(self):
        """Envia um pedido para remover a tarefa selecionada da API."""
        current_item = self.task_list.currentItem()
        if not current_item:
            return

        task_data = current_item.data(Qt.ItemDataRole.UserRole)
        task_id = task_data['id']
        
        reply = QMessageBox.question(self, 'Confirmar Remoção', 
                                     f"Tem certeza que quer remover a tarefa: \"{task_data['descricao']}\"?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # CORREÇÃO: O endpoint correto é /tarefas/{tarefa_id}
                response = requests.delete(f"{API_URL}/tarefas/{task_id}")
                if response.status_code == 200:
                    self.load_tasks()
                else:
                    self.handle_api_error(response)
            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Erro de Conexão", f"Não foi possível remover a tarefa: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    todo_app = TodoApp()
    todo_app.show()
    sys.exit(app.exec())