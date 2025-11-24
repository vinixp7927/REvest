import sys
import os

# Ensure project root is on sys.path so we can import app and database modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app, db
from database import Doador, Doacao, DoacaoItem, Endereco, Ticket, SolicitacaoExclusao

try:
    with app.app_context():
        u = Doador.query.filter_by(Email='test_flow@example.com').first()
        if u:
            print(f"Found user: {u.Email} (ID={u.ID_Doador}). Deleting related records first...")
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
            print('User and related data deleted successfully')
        else:
            print('User not found')
except Exception as e:
    print('Error while deleting user:', e)
