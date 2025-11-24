import sys
import os

# Ensure project root is on sys.path so we can import app and database modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app, db
from database import Doador, Doacao, DoacaoItem, Endereco, Ticket, SolicitacaoExclusao

TARGET_EMAIL = 'viniciusasouza2020@gmail.com'

try:
    with app.app_context():
        u = Doador.query.filter_by(Email=TARGET_EMAIL).first()
        if not u:
            print(f"Usuário {TARGET_EMAIL} não encontrado.")
            sys.exit(0)

        print(f"Encontrado: {u.Email} (ID={u.ID_Doador}). Deletando registros relacionados...")

        # Delete related Doacao records (Doacao.itens has cascade delete-orphan)
        doacoes = Doacao.query.filter_by(ID_Doador=u.ID_Doador).all()
        for d in doacoes:
            db.session.delete(d)

        # Delete tickets, enderecos and solicitacoes
        Ticket.query.filter_by(ID_Doador=u.ID_Doador).delete()
        Endereco.query.filter_by(ID_Doador=u.ID_Doador).delete()
        SolicitacaoExclusao.query.filter_by(ID_Doador=u.ID_Doador).delete()

        # Finally delete the user
        db.session.delete(u)
        db.session.commit()
        print('Usuário e dados relacionados deletados com sucesso.')
except Exception as e:
    print('Erro ao deletar usuário:', e)
    try:
        db.session.rollback()
    except Exception:
        pass
