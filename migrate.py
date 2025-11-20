import os
from app import app, db
from database import Doador, Endereco, Doacao, Ticket
from werkzeug.security import generate_password_hash

with app.app_context():
    # Apagar todas as tabelas existentes
    db.drop_all()
    
    # Criar todas as tabelas com a nova estrutura
    db.create_all()
    
    # Criar usuários iniciais
    initial_users = [
        Doador(Email='user@example.com', Senha=generate_password_hash('123456'), Nome='Maria Silva', CEP='01234-567', Numero='123', role='user'),
        Doador(Email='revest@gmail.com', Senha=generate_password_hash('admin1987'), Nome='Administrador', CEP='00000-000', Numero='0', role='admin'),
        Doador(Email='coletor@gmail.com', Senha=generate_password_hash('coletor1987'), Nome='Coletor', CEP='00000-000', Numero='0', role='coletor')
    ]

    for user in initial_users:
        db.session.add(user)
    
    db.session.commit()
    print("Banco de dados recriado com sucesso!")
    print("Usuários iniciais criados!")