import os
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Inicializa o banco de dados
db = SQLAlchemy()

# ======================================================
# MODELOS DO BANCO DE DADOS
# ======================================================

class Doador(db.Model):
    """Modelo para Doadores"""
    __tablename__ = 'doador'
    
    ID_Doador = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nome = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    # CPF may be optional for some registration flows; make it nullable to avoid DB errors
    # Tornar nullable=True para evitar erros em dados de migração/seed que não incluam CPF
    CPF = db.Column(db.String(14), unique=True, nullable=True)
    CEP = db.Column(db.String(10), nullable=True)
    Numero = db.Column(db.String(10), nullable=False)
    Senha = db.Column(db.String(255), nullable=False)
    Data_Criacao = db.Column(db.DateTime, default=datetime.utcnow)
    is_banned = db.Column(db.Boolean, default=False)
    is_muted = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.String(255), nullable=True)
    banned_at = db.Column(db.DateTime, nullable=True)
    banned_by = db.Column(db.Integer, nullable=True)
    role = db.Column(db.String(20), default='user')  # user, admin, coletor
    
    # Relacionamentos
    doacoes = db.relationship('Doacao', backref='doador', lazy=True)
    tickets = db.relationship('Ticket', backref='doador', lazy=True)

    # Aliases para compatibilidade com templates antigos
    @property
    def id(self):
        return self.ID_Doador

    @property
    def name(self):
        return self.Nome

    @property
    def email(self):
        return self.Email

    @property
    def created_at(self):
        return self.Data_Criacao


class Endereco(db.Model):
    """Modelo para Endereços"""
    __tablename__ = 'endereco'
    
    ID_Endereco = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Doador = db.Column(db.Integer, db.ForeignKey('doador.ID_Doador'), nullable=False)
    Tipo = db.Column(db.String(50), nullable=False)  # Residencial, Comercial, etc
    Rua = db.Column(db.String(150), nullable=False)
    Numero = db.Column(db.String(10), nullable=False)
    CEP = db.Column(db.String(10), nullable=False)
    Bairro = db.Column(db.String(100), nullable=False)
    Cidade = db.Column(db.String(100), nullable=False)
    Estado = db.Column(db.String(2), nullable=False)
    Complemento = db.Column(db.String(255), nullable=True)
    is_default = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    doador = db.relationship('Doador', backref='enderecos')
    doacoes = db.relationship('Doacao', backref='endereco', lazy=True)

    # Aliases para templates
    @property
    def id(self):
        return self.ID_Endereco

    @property
    def type(self):
        return self.Tipo

    @property
    def street(self):
        return self.Rua

    @property
    def number(self):
        return self.Numero

    @property
    def cep(self):
        return self.CEP

    @property
    def neighborhood(self):
        return self.Bairro

    @property
    def city(self):
        return self.Cidade

    @property
    def state(self):
        return self.Estado

    @property
    def complement(self):
        return self.Complemento


class Roupa(db.Model):
    """Modelo para Tipos de Roupas"""
    __tablename__ = 'roupa'
    
    ID_Roupa = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nome = db.Column(db.String(100), unique=True, nullable=False)
    Descricao = db.Column(db.Text, nullable=True)


class Instituicao(db.Model):
    """Modelo para Instituições Beneficiárias"""
    __tablename__ = 'instituicao'
    
    ID_Instituicao = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nome = db.Column(db.String(150), nullable=False)
    CNPJ = db.Column(db.String(18), unique=True, nullable=False)
    Email = db.Column(db.String(100), nullable=False)
    Telefone = db.Column(db.String(20), nullable=True)
    Endereco = db.Column(db.Text, nullable=False)
    Data_Criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    beneficiarios = db.relationship('Beneficiario', backref='instituicao', lazy=True)
    recebimentos = db.relationship('Recebe', backref='instituicao', lazy=True)


class Administrador(db.Model):
    """Modelo para Administradores"""
    __tablename__ = 'administrador'
    
    ID_Admin = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nome = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Senha = db.Column(db.String(255), nullable=False)
    Permissoes = db.Column(db.String(255), nullable=True)
    Data_Criacao = db.Column(db.DateTime, default=datetime.utcnow)


class Beneficiario(db.Model):
    """Modelo para Beneficiários"""
    __tablename__ = 'beneficiario'
    
    ID_Beneficiario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Instituicao = db.Column(db.Integer, db.ForeignKey('instituicao.ID_Instituicao'), nullable=False)
    Nome = db.Column(db.String(100), nullable=False)
    CPF = db.Column(db.String(14), unique=True, nullable=True)
    Data_Nascimento = db.Column(db.Date, nullable=True)
    Data_Criacao = db.Column(db.DateTime, default=datetime.utcnow)


class Administra(db.Model):
    """Modelo de Relacionamento entre Admin e Instituição"""
    __tablename__ = 'administra'
    
    ID_Admin = db.Column(db.Integer, db.ForeignKey('administrador.ID_Admin'), primary_key=True)
    ID_Instituicao = db.Column(db.Integer, db.ForeignKey('instituicao.ID_Instituicao'), primary_key=True)
    Data_Associacao = db.Column(db.DateTime, default=datetime.utcnow)


class Doacao(db.Model):
    """Modelo para Doações"""
    __tablename__ = 'doacao'
    
    ID_Doacao = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Doador = db.Column(db.Integer, db.ForeignKey('doador.ID_Doador'), nullable=False)
    Endereco_Id = db.Column(db.Integer, db.ForeignKey('endereco.ID_Endereco'), nullable=True)
    Data_Coleta = db.Column(db.Date, nullable=False)
    Data_Criacao = db.Column(db.DateTime, default=datetime.utcnow)
    Status = db.Column(db.String(50), default='pendente')  # pendente, aprovada, coletada, cancelada
    Observacoes = db.Column(db.Text, nullable=True)
    
    # Relacionamentos
    itens = db.relationship('DoacaoItem', backref='doacao', lazy=True, cascade='all, delete-orphan')
    recebimentos = db.relationship('Recebe', backref='doacao', lazy=True)

    # Aliases compatíveis com código antigo/templates
    @property
    def id(self):
        return self.ID_Doacao

    @property
    def user_id(self):
        return self.ID_Doador

    @property
    def address_id(self):
        return self.Endereco_Id

    @property
    def data_coleta(self):
        return self.Data_Coleta

    @property
    def status(self):
        return self.Status


class DoacaoItem(db.Model):
    """Modelo para Itens de Doação"""
    __tablename__ = 'doacao_item'
    
    ID_Item = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Doacao = db.Column(db.Integer, db.ForeignKey('doacao.ID_Doacao'), nullable=False)
    Tipo = db.Column(db.String(100), nullable=False)  # roupas, calças, blusas, etc
    Tamanho = db.Column(db.String(20), nullable=True)  # P, M, G, GG, etc
    Categoria = db.Column(db.String(100), nullable=True)  # infantil, adulto, etc
    Descricao = db.Column(db.Text, nullable=True)
    Quantidade = db.Column(db.Integer, default=1)
    Data_Criacao = db.Column(db.DateTime, default=datetime.utcnow)


class Recebe(db.Model):
    """Modelo para Recebimento de Doações"""
    __tablename__ = 'recebe'
    
    ID_Recebimento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Instituicao = db.Column(db.Integer, db.ForeignKey('instituicao.ID_Instituicao'), nullable=False)
    ID_Doacao = db.Column(db.Integer, db.ForeignKey('doacao.ID_Doacao'), nullable=False)
    Data_Recebimento = db.Column(db.DateTime, default=datetime.utcnow)
    Observacoes = db.Column(db.Text, nullable=True)


class Ticket(db.Model):
    """Modelo para Tickets de Suporte"""
    __tablename__ = 'ticket'
    
    ID_Ticket = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Doador = db.Column(db.Integer, db.ForeignKey('doador.ID_Doador'), nullable=False)
    Assunto = db.Column(db.String(200), nullable=False)
    Mensagem = db.Column(db.Text, nullable=False)
    Status = db.Column(db.String(50), default='aberto')  # aberto, respondido, fechado
    # Usar horário local do servidor para exibição correta da hora
    Data_Criacao = db.Column(db.DateTime, default=datetime.now)
    Data_Atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class SolicitacaoExclusao(db.Model):
    """Modelo para Solicitações de Exclusão de Histórico"""
    __tablename__ = 'solicitacao_exclusao'
    
    ID_Solicitacao = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Doador = db.Column(db.Integer, db.ForeignKey('doador.ID_Doador'), nullable=False)
    Tipo = db.Column(db.String(50), nullable=False)  # 'doador' ou 'coletor' (ambos são Doador com roles diferentes)
    Status = db.Column(db.String(50), default='pendente')  # pendente, aprovada, rejeitada
    Motivo = db.Column(db.Text, nullable=True)  # Motivo da rejeição (se houver)
    Data_Solicitacao = db.Column(db.DateTime, default=datetime.utcnow)
    Data_Resposta = db.Column(db.DateTime, nullable=True)
    ID_Admin_Resposta = db.Column(db.Integer, nullable=True)  # Qual admin respondeu
    
    # Relacionamentos
    doador = db.relationship('Doador', backref='solicitacoes_exclusao')
