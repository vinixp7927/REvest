import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app, db
from database import Doador, Endereco, Doacao, DoacaoItem
from datetime import datetime, timedelta

with app.test_client() as c:
    with app.app_context():
        # create test user if not exists
        user = Doador.query.filter_by(Email='test_flow@example.com').first()
        if not user:
            user = Doador(Email='test_flow@example.com', Senha='test', Nome='Test User', Numero='1')
            db.session.add(user)
            db.session.commit()
        # ensure address
        addr = Endereco.query.filter_by(ID_Doador=user.ID_Doador).first()
        if not addr:
            addr = Endereco(ID_Doador=user.ID_Doador, Tipo='casa', Rua='Rua Teste', Numero='10', CEP='12345678', Bairro='Bairro', Cidade='Cidade', Estado='SP')
            db.session.add(addr)
            db.session.commit()

        # set session as logged in
        with c.session_transaction() as sess:
            sess['user'] = user.Email
            sess['name'] = user.Nome
            sess['role'] = user.role
            sess['user_id'] = user.ID_Doador

        # GET /doacao to get form_token
        r = c.get('/doacao')
        assert r.status_code == 200
        # extract form_token from session
        with c.session_transaction() as sess:
            form_token = sess.get('form_token')
        # POST /doacao with camisetas = 3
        data = {
            'form_token': form_token,
            'camisetas': '3',
            'calças': '0',
            'blusas': '0',
            'roupas_intimas': '0',
            'tênis': '0',
            'acessórios': '0',
            'address': str(addr.ID_Endereco),
            'date': (datetime.utcnow().date() + timedelta(days=3)).strftime('%Y-%m-%d')
        }
        r2 = c.post('/doacao', data=data, follow_redirects=True)
        assert r2.status_code in (200, 302)

        # Now on doacao_detalhes, get details_token
        r3 = c.get('/doacao/detalhes')
        with c.session_transaction() as sess:
            dtoken = sess.get('details_token')
            pending = sess.get('pending_donation')
        # Prepare details form: three camisetas
        details = {'details_token': dtoken}
        for i in range(3):
            details[f'camisetas_size_{i}'] = 'P'
            details[f'camisetas_target_{i}'] = 'Masculino'
            details[f'camisetas_desc_{i}'] = ''
        r4 = c.post('/doacao/detalhes', data=details, follow_redirects=True)
        print('POST detalhes status', r4.status_code)

        # Check DB for Doacao and DoacaoItem
        doacao = Doacao.query.filter_by(ID_Doador=user.ID_Doador).order_by(Doacao.Data_Criacao.desc()).first()
        if doacao:
            items = DoacaoItem.query.filter_by(ID_Doacao=doacao.ID_Doacao).all()
            print('Doacao ID:', doacao.ID_Doacao, 'Itens:', [(it.Tipo, it.Categoria, it.Tamanho, it.Quantidade) for it in items])
        else:
            print('No donation found')
