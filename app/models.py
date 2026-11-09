from app import db

# ==========================================
# TABELAS ASSOCIATIVAS (Relações Muitos-para-Muitos)
# ==========================================

usuario_perfil = db.Table('usuario_perfil',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('perfil_id', db.Integer, db.ForeignKey('perfil.id'), primary_key=True)
)

participante_agendamento = db.Table('participante_agendamento',
    db.Column('agendamento_id', db.Integer, db.ForeignKey('agendamento.id'), primary_key=True),
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
)

# ==========================================
# TABELAS DIMENSIONAIS / ENTIDADES BASE
# ==========================================

class Unidade(db.Model):
    __tablename__ = 'unidade'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    sigla = db.Column(db.String(20), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)

    # Relacionamentos 1:N
    recursos = db.relationship('Recurso', backref='unidade', lazy=True)
    usuarios = db.relationship('Usuario', backref='unidade', lazy=True)

class CategoriaRecurso(db.Model):
    __tablename__ = 'categoria_recurso'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True) # Ex: Quadra, Laboratório, Auditório
    descricao = db.Column(db.String(255), nullable=True)

    # Relacionamentos 1:N
    recursos = db.relationship('Recurso', backref='categoria', lazy=True)

class StatusAgendamento(db.Model):
    __tablename__ = 'status_agendamento'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True) # Ex: Pendente, Confirmado, Cancelado

    # Relacionamentos 1:N
    agendamentos = db.relationship('Agendamento', backref='status', lazy=True)

class Perfil(db.Model):
    __tablename__ = 'perfil'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True) # Ex: Aluno, Admin, Comunidade

# ==========================================
# ENTIDADES DE NEGÓCIO PRINCIPAIS
# ==========================================

class Usuario(db.Model):
    __tablename__ = 'usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    
    # Chaves Estrangeiras
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidade.id'), nullable=False)

    # Relacionamentos
    perfis = db.relationship('Perfil', secondary=usuario_perfil, backref=db.backref('usuarios', lazy=True))
    agendamentos_solicitados = db.relationship('Agendamento', backref='solicitante', lazy=True)

class Recurso(db.Model):
    __tablename__ = 'recurso'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    capacidade = db.Column(db.Integer, nullable=False, default=0)
    
    # Chaves Estrangeiras
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidade.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria_recurso.id'), nullable=False)

    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='recurso', lazy=True)

class Agendamento(db.Model):
    __tablename__ = 'agendamento'
    
    id = db.Column(db.Integer, primary_key=True)
    data_hora_inicio = db.Column(db.DateTime, nullable=False)
    data_hora_fim = db.Column(db.DateTime, nullable=False)
    finalidade = db.Column(db.String(255), nullable=False)
    
    # Chaves Estrangeiras
    recurso_id = db.Column(db.Integer, db.ForeignKey('recurso.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False) # Quem solicitou
    status_id = db.Column(db.Integer, db.ForeignKey('status_agendamento.id'), nullable=False)

    # Relacionamentos M:N (Outras pessoas convidadas para o agendamento)
    participantes = db.relationship('Usuario', secondary=participante_agendamento, backref=db.backref('agendamentos_participados', lazy=True))
    