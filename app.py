from datetime import datetime
import secrets
from flask import Flask, render_template, redirect, url_for, session, request, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
import json

# Importações do banco de dados
from database import db, Doador, Roupa, Instituicao, Administrador, Beneficiario, Administra, Recebe, Doacao, DoacaoItem, Endereco, Ticket, SolicitacaoExclusao


from pathlib import Path

# Use resolved pathlib paths to avoid issues with relative paths or symlinks
basedir = Path(__file__).resolve().parent
template_dir = basedir / 'templates'
static_dir = basedir / 'static'

app = Flask(__name__, template_folder=str(template_dir), static_folder=str(static_dir))
app.secret_key = 'secret_key_revest'

# Configuração do Banco de Dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'revest.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco de dados com o app
db.init_app(app)

# Criar tabelas
with app.app_context():
    db.create_all()
    # Diagnostic output to help verify templates/static are available in deployed environments
    try:
        tpl_exists = template_dir.exists()
        tpl_list = [p.name for p in template_dir.glob('*.html')] if tpl_exists else []
    except Exception:
        tpl_exists = False
        tpl_list = []
    print("✅ Banco de dados inicializado")
    print(f"Templates dir: {template_dir} (exists={tpl_exists}), sample files={tpl_list[:8]}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    try:
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        
        user = Doador.query.filter_by(Email=email).first()
        # Primeiro, tentar autenticar como Doador
        if user:
            # suportar senhas hashed e legacy plain-text
            try:
                valid = check_password_hash(user.Senha, password)
            except Exception:
                valid = (user.Senha == password)

            if valid:
                # Verificar se usuário está banido
                if user.is_banned:
                    return render_template('index.html', login_error="Esta conta está banida", active_tab='login')
                session['user'] = user.Email
                session['name'] = user.Nome
                session['role'] = user.role
                session['user_id'] = user.ID_Doador
                return redirect(url_for('dashboard'))

        # Se não autenticou como Doador, tentar Administrador
        admin = Administrador.query.filter_by(Email=email).first()
        if admin:
            try:
                valid_admin = check_password_hash(admin.Senha, password)
            except Exception:
                valid_admin = (admin.Senha == password)

            if valid_admin:
                session['user'] = admin.Email
                session['name'] = admin.Nome
                session['role'] = 'admin'
                session['user_id'] = admin.ID_Admin
                return redirect(url_for('admin'))
        return render_template('index.html', login_error="Credenciais inválidas", active_tab='login')
    except Exception as e:
        print(f"Erro no login: {e}")
        return render_template('index.html', login_error="Erro interno no servidor", active_tab='login')

def format_cpf(cpf_raw: str) -> str | None:
    """Formata o CPF para 000.000.000-00 e valida se tem 11 dígitos numéricos."""
    if not cpf_raw:
        return None
    digits = re.sub(r"\D", "", cpf_raw)
    if len(digits) != 11:
        return None
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def sanitize_input(value: str | None, max_length: int = 2000) -> str:
    """Remove caracteres de controle e limita tamanho para evitar payloads inesperados."""
    if not value or not isinstance(value, str):
        return ''
    # remover caracteres não imprimíveis
    cleaned = re.sub(r'[\x00-\x1f\x7f]', '', value)
    return cleaned[:max_length]


def normalize_cep(cep_raw: str | None) -> str | None:
    """Remove tudo que não for dígito e garante exatamente 8 dígitos, caso contrário retorna None."""
    if not cep_raw:
        return None
    digits = re.sub(r"\D", "", cep_raw)
    return digits if len(digits) == 8 else None


@app.before_request
def block_muted_users_on_post():
    """Bloqueia ações POST de usuários silenciados (exceto administradores)."""
    try:
        if request.method == 'POST' and 'user_id' in session:
            uid = session.get('user_id')
            user = Doador.query.get(uid)
            if user and getattr(user, 'is_muted', False) and session.get('role') != 'admin':
                return render_template('error.html', message='Você está silenciado e não pode realizar essa ação')
    except Exception:
        # Em caso de erro, não bloquear (evitar false positives que quebrem fluxo)
        pass


@app.route('/register', methods=['POST'])
def register():
    try:
        name = request.form.get('fullName', '').strip()
        email = request.form.get('regEmail', '').strip().lower()
        password = request.form.get('regPassword', '').strip()
        confirm_password = request.form.get('confirmPassword', '').strip()
        cpf_input = request.form.get('cpf', '').strip()
        cep_raw = request.form.get('cep', '').strip() or None
        cep = normalize_cep(cep_raw)
        numero = request.form.get('numero', '').strip()

        # Campos obrigatórios: nome, email, senha, confirmação, CPF e número
        if not name or not email or not password or not confirm_password or not cpf_input or not numero:
            return render_template('index.html', register_error="Todos os campos obrigatórios precisam ser preenchidos.")

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return render_template('index.html', register_error="E-mail inválido.")

        if len(password) < 6:
            return render_template('index.html', register_error="A senha deve ter pelo menos 6 caracteres.")

        if password != confirm_password:
            return render_template('index.html', register_error="As senhas não coincidem.")

        # Formatar e validar CPF
        cpf_formatado = format_cpf(cpf_input)
        if not cpf_formatado:
            return render_template('index.html', register_error="CPF inválido. Use 11 dígitos numéricos.")

        # Verificar duplicidade de e-mail e CPF
        if Doador.query.filter_by(Email=email).first():
            return render_template('index.html', register_error="E-mail já cadastrado.")
        if Doador.query.filter_by(CPF=cpf_formatado).first():
            return render_template('index.html', register_error="CPF já cadastrado.")

        # Armazenar senha com hash
        hashed = generate_password_hash(password)

        new_user = Doador(
            Email=email,
            Senha=hashed,
            Nome=name,
            CPF=cpf_formatado,
            CEP=cep,
            Numero=numero
        )

        db.session.add(new_user)
        db.session.commit()

        session['user'] = email
        session['name'] = name
        session['role'] = 'user'
        session['user_id'] = new_user.ID_Doador

        return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Erro no registro: {e}")
        db.session.rollback()
        return render_template('index.html', register_error="Erro interno no servidor")

@app.route('/dashboard')

def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    # Verificar se usuário está banido
    user = Doador.query.get(session['user_id'])
    if user and user.is_banned:
        session.clear()
        return redirect(url_for('home'))
    
    donation_count = Doacao.query.filter_by(ID_Doador=session['user_id']).count()
    
    return render_template('dashboard.html', donation_count=donation_count)

@app.route('/doacao', methods=['GET','POST'])
def doacao():
    from flask import request, redirect, url_for, render_template, flash, session
    # Requer usuário logado para ver/selecionar endereços
    if 'user' not in session:
        return redirect(url_for('home'))

    if request.method == 'GET':
        session['form_token'] = secrets.token_hex(16)
        # Buscar endereços do usuário atual para popular o select
        try:
            user_id = session.get('user_id')
            addresses = Endereco.query.filter_by(ID_Doador=user_id).all() if user_id else []
        except Exception:
            addresses = []

        # calcular min_date (2 dias a partir de hoje) compatível com input type=date
        from datetime import datetime, timedelta
        min_date_obj = datetime.utcnow().date() + timedelta(days=2)
        min_date = min_date_obj.strftime('%Y-%m-%d')

        return render_template('doacao.html', form_token=session['form_token'], addresses=addresses, min_date=min_date)

    token = request.form.get('form_token')
    if not token or token != session.get('form_token'):
        flash('Formulário inválido. Tente novamente.', 'warning')
        return redirect(url_for('doacao'))

    def q(name):
        try:
            v = int(request.form.get(name, '0'))
            return v if v > 0 else 0
        except:
            return 0

    quant = {
        'roupas': q('roupas'),
        'calças': q('calças'),
        'blusas': q('blusas'),
        'roupas_intimas': q('roupas_intimas'),
        'tênis': q('tênis'),
        'acessórios': q('acessórios'),
    }
    total = sum(quant.values())
    if total < 3:
        flash('Adicione pelo menos 3 itens no total.', 'info')
        return redirect(url_for('doacao'))

    session['pending_donation'] = {
        'quant': quant,
        'address_id': request.form.get('address'),
        'date': request.form.get('date')
    }
    session.pop('form_token', None)
    session['details_token'] = secrets.token_hex(16)
    return redirect(url_for('doacao_detalhes'))

@app.route('/confirmacao', methods=['POST'])
def confirmacao():
    if 'user' not in session:
        return redirect(url_for('home'))

    try:
        token = request.form.get('form_token')
        saved = session.pop('form_token', None)
        if not token or token != saved:
            return redirect(url_for('doacao'))

        user_id = session['user_id']
        user = Doador.query.get(user_id)
        if user and user.is_banned:
            session.clear()
            return redirect(url_for('home'))
        if user and user.is_muted:
            return render_template('error.html', message="Você está silenciado e não pode fazer doações")

        form = request.form.to_dict()
        itens = {k: int(v) for k, v in form.items() if k not in ['address', 'date', 'form_token'] and v.isdigit() and int(v) > 0}
        if not itens:
            return redirect(url_for('doacao'))

        endereco_id = int(form['address'])
        data_coleta = form['date']
        address = Endereco.query.get(endereco_id)
        if not address or address.ID_Doador != user_id:
            return redirect(url_for('doacao'))

        nova_doacao = Doacao(
            ID_Doador=user_id,
            Endereco_Id=endereco_id,
            Data_Coleta=datetime.strptime(data_coleta, '%Y-%m-%d').date(),
            Status='pendente'
        )

        db.session.add(nova_doacao)
        db.session.commit()

        return redirect(url_for('confirmacao_sucesso', donation_id=nova_doacao.ID_Doacao))

    except Exception as e:
        print(f"Erro na confirmação: {e}")
        db.session.rollback()
        return redirect(url_for('doacao'))

@app.route('/confirmacao/sucesso/<int:donation_id>')
def confirmacao_sucesso(donation_id):
    if 'user' not in session:
        return redirect(url_for('home'))

    try:
        doacao = Doacao.query.get_or_404(donation_id)
        address = Endereco.query.get(doacao.Endereco_Id)

        doacao_data = {
            "id": doacao.ID_Doacao,
            "user": session['user'],
            "name": session['name'],
            "itens": doacao.itens,
            "status": doacao.Status,
            "data": doacao.Data_Coleta.strftime('%Y-%m-%d'),
            "endereco": f"{address.Tipo} - {address.Rua}, {address.Numero}",
            "cep": address.CEP,
            "full_address": f"{address.Rua}, {address.Numero} - {address.Bairro}, {address.Cidade}/{address.Estado}"
        }
        return render_template('confirmacao.html', doacao=doacao_data)
    except Exception as e:
        print(f"Erro na confirmação: {e}")
        db.session.rollback()
        return redirect(url_for('doacao'))

@app.route('/conta')
def conta():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    user_addresses = Endereco.query.filter_by(ID_Doador=session['user_id']).all()
    return render_template('conta.html', addresses=user_addresses)

@app.route('/add_address', methods=['POST'])
def add_address():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    try:
        user_id = session['user_id']
        
        if request.form.get('default') == 'on':
            # Remove default de outros endereços
            Endereco.query.filter_by(ID_Doador=user_id).update({'is_default': False})
        
        cep_raw = request.form.get('cep', '').strip() or None
        cep_clean = normalize_cep(cep_raw)
        if cep_raw and not cep_clean:
            flash('CEP inválido. Informe 8 dígitos numéricos.', 'danger')
            return redirect(url_for('conta_endereco_get'))

        new_address = Endereco(
            ID_Doador=user_id,
            Tipo=request.form.get('type'),
            Rua=request.form.get('street'),
            Numero=request.form.get('number'),
            CEP=cep_clean,
            Bairro=request.form.get('neighborhood'),
            Cidade=request.form.get('city'),
            Estado=request.form.get('state'),
            Complemento=request.form.get('complement'),
            is_default=request.form.get('default') == 'on'
        )

        db.session.add(new_address)
        db.session.commit()
        return redirect(url_for('conta_endereco_get'))
    except Exception as e:
        print(f"Erro ao adicionar endereço: {e}")
        db.session.rollback()
        return redirect(url_for('conta_endereco_get'))

@app.route('/edit_address/<int:address_id>', methods=['GET', 'POST'])
def edit_address(address_id):
    if 'user' not in session:
        return redirect(url_for('home'))

    try:
        address = Endereco.query.get_or_404(address_id)
        
        if address.ID_Doador != session['user_id']:
            return redirect(url_for('conta_endereco_get'))

        if request.method == 'POST':
            if request.form.get('default') == 'on':
                Endereco.query.filter_by(ID_Doador=session['user_id']).update({'is_default': False})
            
            address.Tipo = request.form.get('type')
            address.Rua = request.form.get('street')
            address.Numero = request.form.get('number')
            # normalize and validate cep
            cep_raw = request.form.get('cep', '').strip() or None
            cep_clean = normalize_cep(cep_raw)
            if cep_raw and not cep_clean:
                flash('CEP inválido. Informe 8 dígitos numéricos.', 'danger')
                return redirect(url_for('edit_address', address_id=address_id))
            address.CEP = cep_clean
            address.Bairro = request.form.get('neighborhood')
            address.Cidade = request.form.get('city')
            address.Estado = request.form.get('state')
            address.Complemento = request.form.get('complement')
            address.is_default = request.form.get('default') == 'on'

            db.session.commit()
            return redirect(url_for('conta_endereco_get'))

        return render_template('edit_address.html', address=address)
    except Exception as e:
        print(f"Erro ao editar endereço: {e}")
        return redirect(url_for('conta_endereco_get'))

@app.route('/delete_address/<int:address_id>')
def delete_address(address_id):
    if 'user' not in session:
        return redirect(url_for('home'))

    try:
        address = Endereco.query.get_or_404(address_id)
        
        if address.ID_Doador == session['user_id']:
            db.session.delete(address)
            db.session.commit()

        return redirect(url_for('conta_endereco_get'))
    except Exception as e:
        print(f"Erro ao deletar endereço: {e}")
        return redirect(url_for('conta_endereco_get'))

@app.route('/admin')
def admin():
    print(f"DEBUG: session['user'] = {session.get('user')}, session['role'] = {session.get('role')}")
    if 'user' not in session or session.get('role') != 'admin':
        print("DEBUG: Redirecionando para home por falta de autenticação ou role incorreta.")
        return redirect(url_for('home'))
    
    try:
        total = Doacao.query.count()
        pendentes = Doacao.query.filter_by(Status='pendente').count()
        aprovadas = Doacao.query.filter_by(Status='aprovada').count()
        coletadas = Doacao.query.filter_by(Status='coletada').count()

        # Buscar todas as doações pendentes e montar dados completos para o template
        pending_raw = Doacao.query.filter_by(Status='pendente').all()
        donations = []
        for d in pending_raw:
            doador = Doador.query.get(d.ID_Doador)
            address = Endereco.query.get(d.Endereco_Id)
            itens = d.itens if hasattr(d, 'itens') else []
            donations.append({
                'id': d.ID_Doacao,
                'name': doador.Nome if doador else 'Desconhecido',
                'cep': address.CEP if address else '',
                'endereco': f"{address.Tipo} - {address.Rua}, {address.Numero}" if address else 'Endereço não disponível',
                'itens': itens,
                'status': d.Status,
                'data': d.Data_Coleta.strftime('%Y-%m-%d') if d.Data_Coleta else '',
            })
        return render_template('admin.html', total=total, pendentes=pendentes, aprovadas=aprovadas, coletadas=coletadas, donations=donations)
    except Exception as e:
        print(f"Erro ao carregar painel admin: {e}")
        return redirect(url_for('home'))

@app.route('/cancel_donation/<int:donation_id>')
def cancel_donation(donation_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    
    try:
        donation = Doacao.query.get_or_404(donation_id)
        db.session.delete(donation)
        db.session.commit()
        
        return redirect(url_for('admin'))
    except Exception as e:
        print(f"Erro ao cancelar: {e}")
        return redirect(url_for('admin'))

@app.route('/historico')
def historico():
    if 'user' not in session:
        return redirect(url_for('home'))

    try:
        user_donations = Doacao.query.filter_by(ID_Doador=session['user_id'])\
                                      .order_by(Doacao.Data_Coleta.desc())\
                                      .all()
        
        # Preparar dados para o template
        doacoes_data = []
        for donation in user_donations:
            address = Endereco.query.get(donation.Endereco_Id)
            if address:
                endereco_str = f"{address.Tipo} - {address.Rua}, {address.Numero}"
            else:
                endereco_str = 'Endereço não disponível'

            doacoes_data.append({
                "id": donation.ID_Doacao,
                "itens": donation.itens,
                "status": donation.Status,
                "data": donation.Data_Coleta.strftime('%Y-%m-%d') if donation.Data_Coleta else '',
                "endereco": endereco_str
            })
        
        return render_template('historico.html', doacoes=doacoes_data)
    except Exception as e:
        print(f"Erro no histórico: {e}")
        return redirect(url_for('dashboard'))

@app.route('/cancelar_doacao/<int:donation_id>', methods=['POST'])
def cancelar_doacao(donation_id):
    if 'user' not in session:
        return redirect(url_for('home'))
    
    try:
        donation = Doacao.query.get_or_404(donation_id)
        
        if donation.ID_Doador == session['user_id'] and donation.Status == 'pendente':
            donation.Status = 'cancelada'
            db.session.commit()
        
        return redirect(url_for('historico'))
    except Exception as e:
        print(f"Erro ao cancelar doação: {e}")
        return redirect(url_for('historico'))

@app.route('/limpar_historico', methods=['POST'])
def limpar_historico():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    try:
        user_id = session['user_id']
        
        # Deletar todas as doações do usuário
        Doacao.query.filter_by(ID_Doador=user_id).delete(synchronize_session=False)
        db.session.commit()
        
        print(f"Histórico de doações limpo para usuário {user_id}")
        return redirect(url_for('historico'))
    except Exception as e:
        print(f"Erro ao limpar histórico: {e}")
        db.session.rollback()
        return redirect(url_for('historico'))

@app.route('/ticket', methods=['GET', 'POST'])
def ticket():
    if 'user' not in session:
        return redirect(url_for('home'))

    # Verificar se usuário está banido ou silenciado
    user = Doador.query.get(session['user_id'])
    if user and user.is_banned:
        session.clear()
        return redirect(url_for('home'))
    if user and user.is_muted:
        return render_template('error.html', message="Você está silenciado e não pode enviar tickets")

    if request.method == 'POST':
        try:
            subject = sanitize_input(request.form.get('subject'), max_length=200)
            message = sanitize_input(request.form.get('message'), max_length=2000)

            if subject and message:
                new_ticket = Ticket(
                    ID_Doador=session['user_id'],
                    Assunto=subject,
                    Mensagem=message,
                    Status='aberto',
                    Data_Criacao=datetime.now()
                )
                db.session.add(new_ticket)
                db.session.commit()
                return redirect(url_for('ticket_success'))
        except Exception as e:
            print(f"Erro no ticket: {e}")

    # Buscar todos os tickets do usuário, ordenados por data (mais recentes primeiro)
    try:
        tickets_com_historico = Ticket.query.filter_by(ID_Doador=session['user_id']).order_by(Ticket.Data_Criacao.desc()).all()
        tickets_abertos = len([t for t in tickets_com_historico if t.Status == 'aberto'])
    except Exception as e:
        print(f"Erro ao buscar tickets: {e}")
        tickets_com_historico = []
        tickets_abertos = 0

    return render_template('ticket.html', tickets_com_historico=tickets_com_historico, tickets_abertos=tickets_abertos)

@app.route('/ticket/success')
def ticket_success():
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('ticket_success.html')

@app.route('/ticket/delete/<int:ticket_id>', methods=['POST'])
def delete_ticket(ticket_id):
    """Deleta um ticket individual"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Não autenticado'}), 401
    
    try:
        ticket = Ticket.query.get_or_404(ticket_id)
        
        # Verificar se o ticket pertence ao usuário logado
        if ticket.ID_Doador != session['user_id']:
            return jsonify({'success': False, 'error': 'Não autorizado'}), 403
        
        db.session.delete(ticket)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Ticket excluído com sucesso'})
    except Exception as e:
        print(f"Erro ao deletar ticket: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ticket/delete-all', methods=['POST'])
def delete_all_tickets():
    """Deleta todos os tickets do usuário"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Não autenticado'}), 401
    
    try:
        # Buscar todos os tickets do usuário
        tickets = Ticket.query.filter_by(ID_Doador=session['user_id']).all()
        
        # Deletar cada um
        for ticket in tickets:
            db.session.delete(ticket)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{len(tickets)} ticket(s) excluído(s) com sucesso'})
    except Exception as e:
        print(f"Erro ao deletar todos os tickets: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/coletor')
def coletor():
    if 'user' not in session or session.get('role') != 'coletor':
        return redirect(url_for('home'))

    try:
        # Pegar todas as coletas (pendentes e coletadas)
        coletas_todas = Doacao.query.filter(Doacao.Status.in_(['aprovada', 'coletada'])).all()

        # Separar em pendentes e finalizadas
        coletas_pendentes = []
        coletas_finalizadas = []
        
        for coleta in coletas_todas:
            user = Doador.query.get(coleta.ID_Doador)
            address = Endereco.query.get(coleta.Endereco_Id)
            
            # Verificar se tem dados de usuário e endereço
            if not user or not address:
                continue
                
            coleta_info = {
                "id": coleta.ID_Doacao,
                "name": user.Nome,
                "itens": coleta.itens,
                "status": coleta.Status,
                "data": coleta.Data_Coleta.strftime('%Y-%m-%d'),
                "endereco": f"{address.Tipo} - {address.Rua}, {address.Numero}",
                "cep": address.CEP,
                "full_address": f"{address.Rua}, {address.Numero} - {address.Bairro}, {address.Cidade}/{address.Estado}"
            }
            
            if coleta.Status == 'aprovada':
                coletas_pendentes.append(coleta_info)
            elif coleta.Status == 'coletada':
                coletas_finalizadas.append(coleta_info)

        # Verificar se tem solicitação de exclusão pendente
        solicitacao_pendente = SolicitacaoExclusao.query.filter_by(
            ID_Doador=session['user_id'],
            Tipo='coletor',
            Status='pendente'
        ).first()

        return render_template('coletor.html', 
                             coletas_pendentes=coletas_pendentes,
                             coletas_finalizadas=coletas_finalizadas,
                             solicitacao_pendente=solicitacao_pendente)
    except Exception as e:
        print(f"Erro no coletor: {e}")
        return redirect(url_for('dashboard'))

@app.route('/marcar_coletada/<int:donation_id>')
def marcar_coletada(donation_id):
    if 'user' not in session or session.get('role') != 'coletor':
        return redirect(url_for('home'))
 
    try:
        donation = Doacao.query.get_or_404(donation_id)

        if donation.Status == 'aprovada':
            donation.Status = 'coletada'
            db.session.commit()

        return redirect(url_for('coletor'))
    except Exception as e:
        print(f"Erro ao marcar coletada: {e}")
        return redirect(url_for('coletor'))

@app.route('/historico_coletor')
def historico_coletor():
    """Página de histórico com coletas finalizadas e opção de solicitar exclusão"""
    if 'user' not in session or session.get('role') != 'coletor':
        return redirect(url_for('home'))

    try:
        # Pegar todas as coletas coletadas
        coletas_coletadas = Doacao.query.filter_by(Status='coletada').all()

        # Preparar dados para o template
        coletas_finalizadas = []
        
        for coleta in coletas_coletadas:
            user = Doador.query.get(coleta.ID_Doador)
            address = Endereco.query.get(coleta.Endereco_Id)
            
            # Verificar se tem dados de usuário e endereço
            if not user or not address:
                continue
                
            coleta_info = {
                "id": coleta.ID_Doacao,
                "name": user.Nome,
                "itens": coleta.itens,
                "status": coleta.Status,
                "data": coleta.Data_Coleta.strftime('%Y-%m-%d'),
                "endereco": f"{address.Tipo} - {address.Rua}, {address.Numero}",
                "cep": address.CEP,
                "full_address": f"{address.Rua}, {address.Numero} - {address.Bairro}, {address.Cidade}/{address.Estado}"
            }
            coletas_finalizadas.append(coleta_info)

        # Verificar se tem solicitação de exclusão pendente
        solicitacao_pendente = SolicitacaoExclusao.query.filter_by(
            ID_Doador=session['user_id'],
            Tipo='coletor',
            Status='pendente'
        ).first()

        return render_template('historico_coletor.html',
                             coletas_finalizadas=coletas_finalizadas,
                             solicitacao_pendente=solicitacao_pendente)
    except Exception as e:
        print(f"Erro ao buscar histórico do coletor: {e}")
        return redirect(url_for('coletor'))

# NOVAS ROTAS DE MODERAÇÃO

@app.route('/moderacao')
def moderacao():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    
    search_query = request.args.get('search', '')
    view_type = request.args.get('view', 'all')
    
    # Query base
    query = Doador.query
    
    # Filtros
    if search_query:
        query = query.filter(
            (Doador.Nome.ilike(f'%{search_query}%')) | 
            (Doador.Email.ilike(f'%{search_query}%'))
        )
    
    if view_type == 'banned':
        query = query.filter(Doador.is_banned == True)
    elif view_type == 'muted':
        query = query.filter(Doador.is_muted == True)
    
    users = query.order_by(Doador.Data_Criacao.desc()).all()
    
    # Estatísticas
    total_users = Doador.query.count()
    banned_users = Doador.query.filter_by(is_banned=True).count()
    muted_users = Doador.query.filter_by(is_muted=True).count()
    coletor_users = Doador.query.filter_by(role='coletor').count()
    
    return render_template('moderacao.html', 
                         users=users,
                         search_query=search_query,
                         total_users=total_users,
                         banned_users=banned_users,
                         muted_users=muted_users,
                         coletor_users=coletor_users)

@app.route('/moderacao/promover', methods=['POST'])
def promover_usuario():
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Não autorizado'})
    
    data = request.get_json() or {}
    try:
        user_id = int(data.get('user_id'))
    except Exception:
        return jsonify({'success': False, 'error': 'user_id inválido'})
    new_role = data.get('new_role')
    
    user = Doador.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'})
    
    # Proteger o admin principal
    if user.Email == 'revest@gmail.com':
        return jsonify({'success': False, 'error': 'Não é possível alterar o ADMIN principal'})
    
    user.role = new_role
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/moderacao/banir', methods=['POST'])
def banir_usuario():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    
    try:
        user_id = int(request.form.get('user_id'))
    except Exception:
        return redirect(url_for('moderacao'))
    ban_reason = request.form.get('ban_reason')
    
    user = Doador.query.get(user_id)
    if not user:
        return redirect(url_for('moderacao'))
    
    # Proteger o admin principal
    if user.Email == 'revest@gmail.com':
        return redirect(url_for('moderacao'))
    
    user.is_banned = True
    user.ban_reason = ban_reason
    user.banned_at = datetime.utcnow()
    user.banned_by = session['user_id']
    
    db.session.commit()
    
    return redirect(url_for('moderacao'))

@app.route('/moderacao/desbanir', methods=['POST'])
def desbanir_usuario():
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Não autorizado'})
    
    data = request.get_json() or {}
    try:
        user_id = int(data.get('user_id'))
    except Exception:
        return jsonify({'success': False, 'error': 'user_id inválido'})
    
    user = Doador.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'})
    
    user.is_banned = False
    user.ban_reason = None
    user.banned_at = None
    user.banned_by = None
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/moderacao/silenciar', methods=['POST'])
def silenciar_usuario():
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Não autorizado'})
    
    data = request.get_json() or {}
    try:
        user_id = int(data.get('user_id'))
    except Exception:
        return jsonify({'success': False, 'error': 'user_id inválido'})
    
    user = Doador.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'})
    
    # Proteger o admin principal
    if user.Email == 'revest@gmail.com':
        return jsonify({'success': False, 'error': 'Não é possível silenciar o ADMIN principal'})
    
    user.is_muted = True
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/moderacao/dessilenciar', methods=['POST'])
def dessilenciar_usuario():
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Não autorizado'})
    
    data = request.get_json() or {}
    try:
        user_id = int(data.get('user_id'))
    except Exception:
        return jsonify({'success': False, 'error': 'user_id inválido'})
    
    user = Doador.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'})
    
    user.is_muted = False
    db.session.commit()
    
    return jsonify({'success': True})



@app.route('/doacao/detalhes', methods=['GET','POST'])
def doacao_detalhes():
    from flask import request, redirect, url_for, render_template, flash, session
    pend = session.get('pending_donation')
    if not pend:
        return redirect(url_for('doacao'))

    if request.method == 'GET':
        ranges = {k: range(v) for k, v in pend['quant'].items() if v > 0}
        return render_template('doacao_detalhes.html',
                               ranges=ranges,
                               quantidades=pend['quant'],
                               details_token=session.get('details_token'))

    dtoken = request.form.get('details_token')
    if not dtoken or dtoken != session.get('details_token'):
        flash('Sessão expirada. Refaça a doação.', 'warning')
        return redirect(url_for('doacao'))

    # Proteger contra double-submit: invalidar token imediatamente após validação
    session.pop('details_token', None)

    quant = pend['quant']
    total = sum(quant.values())
    if total < 3:
        return redirect(url_for('doacao'))

    # Use o usuário atual da sessão; não usar fallback para evitar inscrições sem endereço
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('home'))

    # Validar endereço salvo no pending_donation
    try:
        endereco_id = int(pend.get('address_id')) if pend.get('address_id') else None
    except Exception:
        endereco_id = None

    if not endereco_id:
        flash('Endereço inválido. Selecione um endereço válido.', 'warning')
        return redirect(url_for('doacao'))

    address = Endereco.query.get(endereco_id)
    if not address or address.ID_Doador != user_id:
        flash('Endereço não encontrado ou não pertence a você.', 'warning')
        return redirect(url_for('doacao'))

    from datetime import datetime as _dt
    data_coleta = _dt.strptime(pend['date'], '%Y-%m-%d').date() if pend.get('date') else _dt.utcnow().date()

    # Parse submitted form keys into item records (only prefixes/indices expected by pending_donation)
    pattern = re.compile(r'^(?P<prefix>.+?)_(?P<field>size|target|desc)_(?P<index>\d+)$')
    items_map = {}
    for key in request.form.keys():
        m = pattern.match(key)
        if not m:
            continue
        prefix = m.group('prefix')
        field = m.group('field')
        idx = int(m.group('index'))
        items_map.setdefault((prefix, idx), {})[field] = request.form.get(key, '').strip()

    valid_prefixes = set(quant.keys())
    items = []
    for prefix in sorted({p for (p, i) in items_map.keys()}):
        if prefix not in valid_prefixes:
            continue
        max_idx = int(quant.get(prefix, 0))
        indices = sorted(i for (p, i) in items_map.keys() if p == prefix)
        for idx in indices:
            if idx >= max_idx:
                continue
            data = items_map.get((prefix, idx), {})
            cat = (data.get('target') or '').strip()
            size = (data.get('size') or '').strip() or None
            desc = (data.get('desc') or '').strip() or None
            if cat:
                items.append({
                    'Tipo': prefix,
                    'Categoria': cat,
                    'Tamanho': size,
                    'Descricao': desc,
                    'Quantidade': 1
                })

    if not items:
        flash('Por favor, preencha pelo menos 1 item com categoria!', 'warning')
        return redirect(url_for('doacao_detalhes'))

    # Create donation and items atomically
    try:
        nova = Doacao(ID_Doador=user_id,
                      Endereco_Id=endereco_id,
                      Data_Coleta=data_coleta,
                      Status='pendente')
        db.session.add(nova)
        db.session.flush()

        # Inserção idempotente: se já existir item igual (Tipo,Categoria,Tamanho)
        # para esta doação, incrementar Quantidade em vez de criar duplicata.
        for it in items:
            existing = DoacaoItem.query.filter_by(
                ID_Doacao=nova.ID_Doacao,
                Tipo=it['Tipo'],
                Categoria=it['Categoria'],
                Tamanho=it['Tamanho']
            ).first()
            if existing:
                try:
                    existing.Quantidade = (existing.Quantidade or 0) + int(it.get('Quantidade', 1))
                except Exception:
                    existing.Quantidade = 1
            else:
                db.session.add(DoacaoItem(
                    ID_Doacao=nova.ID_Doacao,
                    Tipo=it['Tipo'],
                    Tamanho=it['Tamanho'],
                    Categoria=it['Categoria'],
                    Descricao=it['Descricao'],
                    Quantidade=it['Quantidade']
                ))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar doação: {e}")
        flash('Erro interno ao processar doação. Tente novamente.', 'warning')
        return redirect(url_for('doacao_detalhes'))

    # Clear pending session tokens and redirect to confirmation
    session.pop('pending_donation', None)
    session.pop('details_token', None)
    return redirect(url_for('confirmacao_sucesso', donation_id=nova.ID_Doacao))

# ===== ROTAS PARA SOLICITAÇÃO DE EXCLUSÃO DE HISTÓRICO =====

@app.route('/admin/aprovacoes')
def admin_aprovacoes():
    """Painel unificado de aprovações: exclusões de histórico e tickets"""
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    
    try:
        # Solicitações de exclusão pendentes
        solicitacoes_exclusao_pendentes = SolicitacaoExclusao.query.filter_by(Status='pendente').all()
        
        # Tickets pendentes
        tickets_pendentes = Ticket.query.filter_by(Status='aberto').all()
        
        return render_template('admin_aprovacoes.html',
                             solicitacoes_exclusao_pendentes=solicitacoes_exclusao_pendentes,
                             tickets_pendentes=tickets_pendentes)
    except Exception as e:
        print(f"Erro ao buscar aprovações: {e}")
        return redirect(url_for('admin'))

@app.route('/admin/responder_ticket/<int:ticket_id>', methods=['POST'])
def responder_ticket(ticket_id):
    """Admin responde um ticket de suporte"""
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Não autorizado'}), 403
    
    try:
        ticket = Ticket.query.get_or_404(ticket_id)
        resposta = request.form.get('resposta', '').strip()
        
        if not resposta:
            return jsonify({'success': False, 'error': 'Resposta vazia'}), 400
        
        # Marcar como respondido
        ticket.Status = 'respondido'
        ticket.Data_Atualizacao = datetime.utcnow()
        
        # Salvar a resposta (pode adicionar uma tabela RespostaTicket depois se necessário)
        # Por enquanto, vamos adicionar a resposta na mensagem
        ticket.Mensagem = f"{ticket.Mensagem}\n\n--- RESPOSTA DO ADMIN ---\n{resposta}"
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Resposta enviada com sucesso'})
    except Exception as e:
        print(f"Erro ao responder ticket: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/ticket/delete/<int:ticket_id>', methods=['POST'])
def admin_delete_ticket(ticket_id):
    """Admin deleta um ticket"""
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Não autorizado'}), 403
    
    try:
        ticket = Ticket.query.get_or_404(ticket_id)
        
        db.session.delete(ticket)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Ticket excluído com sucesso'})
    except Exception as e:
        print(f"Erro ao deletar ticket (admin): {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/ticket/delete-all/<int:user_id>', methods=['POST'])
def admin_delete_all_tickets(user_id):
    """Admin deleta todos os tickets de um usuário"""
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Não autorizado'}), 403
    
    try:
        # Buscar todos os tickets do usuário
        tickets = Ticket.query.filter_by(ID_Doador=user_id).all()
        
        # Deletar cada um
        for ticket in tickets:
            db.session.delete(ticket)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{len(tickets)} ticket(s) excluído(s) com sucesso'})
    except Exception as e:
        print(f"Erro ao deletar todos os tickets do usuário (admin): {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== ROTAS PARA SOLICITAÇÃO DE EXCLUSÃO DE HISTÓRICO =====

@app.route('/solicitar_exclusao_historico/<tipo>', methods=['POST'])
def solicitar_exclusao_historico(tipo):
    """Coletor ou Doador pode solicitar exclusão de histórico"""
    if 'user' not in session:
        return redirect(url_for('home'))
    
    if tipo not in ['doador', 'coletor']:
        return redirect(url_for('dashboard'))
    
    # Verificar se já tem solicitação pendente
    solicitacao_existente = SolicitacaoExclusao.query.filter_by(
        ID_Doador=session['user_id'],
        Tipo=tipo,
        Status='pendente'
    ).first()
    
    if solicitacao_existente:
        return render_template('historico.html' if tipo == 'doador' else 'coletor.html', 
                             error="Já existe uma solicitação de exclusão pendente")
    
    try:
        nova_solicitacao = SolicitacaoExclusao(
            ID_Doador=session['user_id'],
            Tipo=tipo
        )
        db.session.add(nova_solicitacao)
        db.session.commit()
        
        success_msg = "Solicitação enviada! Aguarde aprovação do administrador."
        if tipo == 'doador':
            return redirect(url_for('historico'))
        else:
            return redirect(url_for('coletor'))
    except Exception as e:
        print(f"Erro ao solicitar exclusão: {e}")
        db.session.rollback()
        return redirect(url_for('historico' if tipo == 'doador' else 'coletor'))

@app.route('/admin/solicitacoes_exclusao')
def admin_solicitacoes_exclusao():
    """Admin vê todas as solicitações de exclusão pendentes"""
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    
    try:
        solicitacoes_pendentes = SolicitacaoExclusao.query.filter_by(Status='pendente').all()
        solicitacoes_respondidas = SolicitacaoExclusao.query.filter(
            SolicitacaoExclusao.Status.in_(['aprovada', 'rejeitada'])
        ).order_by(SolicitacaoExclusao.Data_Resposta.desc()).limit(50).all()
        
        return render_template('admin_solicitacoes_exclusao.html',
                             solicitacoes_pendentes=solicitacoes_pendentes,
                             solicitacoes_respondidas=solicitacoes_respondidas)
    except Exception as e:
        print(f"Erro ao buscar solicitações: {e}")
        return redirect(url_for('admin'))

@app.route('/admin/responder_exclusao/<int:solicitacao_id>/<acao>', methods=['POST'])
def responder_exclusao(solicitacao_id, acao):
    """Admin aprova ou rejeita a solicitação de exclusão"""
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Não autorizado'}), 403
    
    if acao not in ['aprovar', 'rejeitar']:
        return jsonify({'success': False, 'error': 'Ação inválida'}), 400
    
    try:
        solicitacao = SolicitacaoExclusao.query.get_or_404(solicitacao_id)
        
        if solicitacao.Status != 'pendente':
            return jsonify({'success': False, 'error': 'Solicitação já foi respondida'}), 400
        
        if acao == 'aprovar':
            solicitacao.Status = 'aprovada'
            
            # Deletar histórico do usuário
            Doacao.query.filter_by(ID_Doador=solicitacao.ID_Doador).delete(synchronize_session=False)
            
        else:  # rejeitar
            motivo = request.form.get('motivo', 'Solicitação rejeitada pelo administrador')
            solicitacao.Status = 'rejeitada'
            solicitacao.Motivo = motivo
        
        solicitacao.Data_Resposta = datetime.utcnow()
        solicitacao.ID_Admin_Resposta = session['user_id']
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Solicitação {acao}a com sucesso'})
    except Exception as e:
        print(f"Erro ao responder solicitação: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/approve_donation/<int:donation_id>')
def approve_donation(donation_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    try:
        donation = Doacao.query.get_or_404(donation_id)
        if donation.Status == 'pendente':
            donation.Status = 'aprovada'
            db.session.commit()
        return redirect(url_for('admin'))
    except Exception as e:
        print(f"Erro ao aprovar doação: {e}")
        return redirect(url_for('admin'))



# === Rotas de Conta (importadas da 0.0.9.5 e ajustadas) ===
# --- Rotas de Conta ---
@app.route('/conta/suporte', methods=['POST'])
def suporte_conta():
    try:
        if 'user_id' not in session:
            flash('Você precisa estar logado para enviar suporte.', 'danger')
            return redirect(url_for('login'))
        user_id = session['user_id']
        mensagem = request.form.get('mensagem')
        if not mensagem:
            flash('Mensagem não pode ser vazia.', 'danger')
            return redirect(url_for('dashboard'))
        ticket = Ticket(
            ID_Doador=user_id,
            Assunto='conta/suporte',
            Mensagem=mensagem,
            Status='aberto',
            Data_Criacao=datetime.utcnow()
        )
        db.session.add(ticket)
        db.session.commit()
        flash('Ticket de suporte enviado com sucesso.', 'success')
        print('Redirecionando para conta_suporte_get')
        return redirect(url_for('conta_suporte_get'))
    except Exception as e:
        print(f'Erro ao enviar suporte: {e}')
        flash('Ocorreu um erro ao enviar o ticket de suporte.', 'danger')
        return redirect(url_for('conta_suporte_get'))
@app.route('/conta/editar', methods=['GET'])
def conta_editar_get():
    return render_template('conta.html', form_type='editar')


@app.route('/conta/senha', methods=['GET', 'POST'])
def conta_senha():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    if request.method == 'GET':
        return render_template('conta.html', form_type='senha')

    # POST - processar alteração de senha
    try:
        user_id = session['user_id']
        current = request.form.get('current_password', '')
        new = request.form.get('new_password', '')
        confirm = request.form.get('confirm_new_password', '')

        if not current or not new or not confirm:
            flash('Preencha todos os campos.', 'danger')
            return redirect(url_for('conta_senha'))

        if new != confirm:
            flash('A nova senha e a confirmação não coincidem.', 'danger')
            return redirect(url_for('conta_senha'))

        if len(new) < 6:
            flash('A nova senha deve ter pelo menos 6 caracteres.', 'danger')
            return redirect(url_for('conta_senha'))

        user = Doador.query.get(user_id)
        if not user:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('home'))

        try:
            if not check_password_hash(user.Senha, current):
                flash('Senha atual incorreta.', 'danger')
                return redirect(url_for('conta_senha'))
        except Exception:
            # Se senha foi armazenada em texto (legacy), comparar diretamente
            if user.Senha != current:
                flash('Senha atual incorreta.', 'danger')
                return redirect(url_for('conta_senha'))

        user.Senha = generate_password_hash(new)
        db.session.commit()
        flash('Senha alterada com sucesso.', 'success')
        return redirect(url_for('conta_editar_get'))
    except Exception as e:
        print(f"Erro ao alterar senha: {e}")
        db.session.rollback()
        flash('Erro interno ao alterar senha.', 'danger')
        return redirect(url_for('conta_senha'))

@app.route('/conta/endereco', methods=['GET'])
def conta_endereco_get():
    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar endereços.', 'danger')
        return redirect(url_for('login'))
    enderecos = Endereco.query.filter_by(ID_Doador=session['user_id']).all()
    # repassa parâmetro `next` (se houver) para o template, para o formulário POST preservar o destino
    next_url = request.args.get('next')
    return render_template('conta.html', form_type='endereco', enderecos=enderecos, next=next_url)

@app.route('/conta/suporte', methods=['GET'])
def conta_suporte_get():
    return render_template('conta.html', form_type='suporte')

@app.route('/conta/deletar', methods=['GET'])
def conta_deletar_get():
    return render_template('conta.html', form_type='deletar')
    return redirect(url_for('dashboard'))

@app.route('/conta/endereco', methods=['POST'])
def editar_endereco():
    if 'user_id' not in session:
        flash('Você precisa estar logado para editar o endereço.', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    tipo = request.form.get('type')
    rua = request.form.get('street')
    numero = request.form.get('number')
    bairro = request.form.get('neighborhood')
    cidade = request.form.get('city')
    estado = request.form.get('state')
    cep_raw = request.form.get('cep')
    cep = normalize_cep(cep_raw)
    complemento = request.form.get('complement')

    # Validação dos campos obrigatórios
    if not (tipo and rua and numero and bairro and cidade and estado and cep):
        flash('Preencha todos os campos obrigatórios do endereço.', 'danger')
        return redirect(url_for('conta_endereco_get'))

    # Se já existe um endereço padrão e o usuário NÃO marcou como padrão,
    # isso significa que ele está adicionando um novo endereço (não quer sobrescrever o padrão).
    is_default_flag = request.form.get('default') == 'on'
    endereco_default = Endereco.query.filter_by(ID_Doador=user_id, is_default=True).first()

    try:
        if endereco_default and not is_default_flag:
            # Criar novo endereço e NÃO alterar o padrão existente
            novo = Endereco(
                ID_Doador=user_id,
                Tipo=tipo,
                Rua=rua,
                Numero=numero,
                Bairro=bairro,
                Cidade=cidade,
                Estado=estado,
                CEP=cep,
                Complemento=complemento,
                is_default=False
            )
            db.session.add(novo)
            db.session.commit()
            session['endereco'] = f"{rua}, {numero} - {bairro}, {cidade}/{estado}"
            session['cep'] = cep
            flash('Endereço adicionado com sucesso.', 'success')
            next_url = request.args.get('next') or request.form.get('next')
            if next_url and isinstance(next_url, str) and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('conta_endereco_get'))

        # Caso contrário: ou não havia padrão ainda, ou o usuário marcou como padrão -> atualizar/criar como padrão
        if is_default_flag:
            Endereco.query.filter_by(ID_Doador=user_id).update({'is_default': False})

        if endereco_default and is_default_flag:
            endereco = endereco_default
            endereco.Tipo = tipo
            endereco.Rua = rua
            endereco.Numero = numero
            endereco.CEP = cep
            endereco.Bairro = bairro
            endereco.Cidade = cidade
            endereco.Estado = estado
            endereco.Complemento = complemento
            endereco.is_default = True
        else:
            # Criar novo endereço (será padrão apenas se is_default_flag for True)
            endereco = Endereco(
                ID_Doador=user_id,
                Tipo=tipo,
                Rua=rua,
                Numero=numero,
                Bairro=bairro,
                Cidade=cidade,
                Estado=estado,
                CEP=cep,
                Complemento=complemento,
                is_default=is_default_flag
            )
            db.session.add(endereco)

        db.session.commit()
        session['endereco'] = f"{rua}, {numero} - {bairro}, {cidade}/{estado}"
        session['cep'] = cep
        flash('Endereço salvo com sucesso.', 'success')
        next_url = request.args.get('next') or request.form.get('next')
        if next_url and isinstance(next_url, str) and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('conta_endereco_get'))
    except Exception as e:
        print(f"Erro ao salvar/atualizar endereço (editar_endereco): {e}")
        db.session.rollback()
        flash('Erro ao salvar endereço. Tente novamente.', 'danger')
        return redirect(url_for('conta_endereco_get'))

@app.route('/conta/deletar', methods=['POST'])
def deletar_conta():
    if 'user_id' not in session:
        flash('Você precisa estar logado para excluir a conta.', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    senha = request.form.get('password')
    senha_confirm = request.form.get('password_confirm')
    # validar campos fornecidos
    if not senha or not senha_confirm:
        flash('Preencha os campos de senha.', 'danger')
        return redirect(url_for('conta_deletar_get'))
    if senha != senha_confirm:
        flash('As senhas não conferem.', 'danger')
        return redirect(url_for('conta_deletar_get'))
    user = Doador.query.filter_by(ID_Doador=user_id).first()
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('dashboard'))
    if user.role in ['admin', 'coletor']:
        flash('Admins e coletor principal não podem ser excluídos.', 'danger')
        return redirect(url_for('dashboard'))
    # proteger caso user.Senha seja None
    try:
        if not user.Senha or not check_password_hash(user.Senha, senha):
            flash('Senha incorreta.', 'danger')
            return redirect(url_for('conta_deletar_get'))
    except Exception:
        flash('Erro ao verificar a senha. Tente novamente.', 'danger')
        return redirect(url_for('conta_deletar_get'))
    # O modelo Doacao não possui campos `admin_id` nem `coletor_id`.
    # Deletar apenas doações cujo ID_Doador corresponde ao usuário.
    Doacao.query.filter(Doacao.ID_Doador == user_id).delete(synchronize_session=False)
    Ticket.query.filter_by(ID_Doador=user_id).delete()
    Endereco.query.filter_by(ID_Doador=user_id).delete()
    # Remover também solicitações de exclusão pendentes/registradas para este usuário
    SolicitacaoExclusao.query.filter_by(ID_Doador=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    session.clear()
    flash('Conta excluída com sucesso.', 'success')
    return redirect(url_for('home'))



@app.route('/conta/editar', methods=['POST'])
def editar_conta():
    if 'user_id' not in session:
        flash('Você precisa estar logado para editar a conta.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip().lower()

    if not nome or not email:
        flash('Nome e e-mail são obrigatórios.', 'danger')
        return redirect(url_for('conta_editar_get'))

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash('E-mail inválido.', 'danger')
        return redirect(url_for('conta_editar_get'))

    user = Doador.query.filter_by(ID_Doador=user_id).first()
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('dashboard'))

    # Se o e-mail mudou, verificar se já existe
    if email != user.Email and Doador.query.filter_by(Email=email).first():
        flash('Este e-mail já está em uso.', 'danger')
        return redirect(url_for('conta_editar_get'))

    user.Nome = nome
    user.Email = email
    db.session.commit()

    session['name'] = nome
    session['user'] = email

    flash('Dados atualizados com sucesso.', 'success')
    return redirect(url_for('conta_editar_get'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("🚀 Servidor REvest iniciando...")
    print("🌐 Acesse: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)

# --- Security session config (added) ---
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'change_this_to_a_strong_secret'),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,    # True em produção (HTTPS)
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600
)

@app.after_request
def add_security_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

from flask import session, redirect, url_for, request
try:
    from flask_login import logout_user
except Exception:
    logout_user = None

@app.route('/safe-logout', methods=['POST'])
def safe_logout():
    try:
        if logout_user:
            logout_user()
    except Exception:
        pass
    session.clear()
    try:
        return redirect(url_for('login'))
    except Exception:
        return redirect('/')