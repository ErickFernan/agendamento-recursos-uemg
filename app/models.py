from app import db
from sqlalchemy import UniqueConstraint
from datetime import datetime, timezone

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

    # Campos de Auditoria (Timestamps)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamentos 1:N
    recursos = db.relationship('Recurso', backref='unidade', lazy=True)
    usuarios = db.relationship('Usuario', backref='unidade', lazy=True)

    __table_args__ = (
        UniqueConstraint('nome', 'cidade', name='uq_unidade_nome_cidade'),
    )

class CategoriaRecurso(db.Model):
    __tablename__ = 'categoria_recurso'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True) # Ex: Quadra, Laboratório, Auditório
    descricao = db.Column(db.String(255), nullable=True)

    # Campos de Auditoria
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamentos 1:N
    recursos = db.relationship('Recurso', backref='categoria', lazy=True)

class StatusAgendamento(db.Model):
    __tablename__ = 'status_agendamento'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True) # Ex: Pendente, Confirmado, Cancelado

    # Campos de Auditoria
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamentos 1:N
    agendamentos = db.relationship('Agendamento', backref='status', lazy=True)

class Perfil(db.Model):
    __tablename__ = 'perfil'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True) # Ex: Aluno, Admin, Comunidade

    # Campos de Auditoria
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# ==========================================
# ENTIDADES DE NEGÓCIO PRINCIPAIS
# ==========================================

class Usuario(db.Model):
    __tablename__ = 'usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    
    # Campos de Auditoria
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Chaves Estrangeiras
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidade.id'), nullable=False)

    # Relacionamentos (N:N com Perfil)
    perfis = db.relationship('Perfil', secondary=usuario_perfil, backref=db.backref('usuarios', lazy=True))
    agendamentos_solicitados = db.relationship('Agendamento', backref='solicitante', lazy=True)

class Recurso(db.Model):
    __tablename__ = 'recurso'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    capacidade = db.Column(db.Integer, nullable=False, default=0)
    
    # Campos de Auditoria
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Chaves Estrangeiras
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidade.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria_recurso.id'), nullable=False)

    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='recurso', lazy=True)

    __table_args__ = (
        UniqueConstraint('nome', 'unidade_id', name='uq_recurso_nome_unidade'),
    )

class Agendamento(db.Model):
    __tablename__ = 'agendamento'
    
    id = db.Column(db.Integer, primary_key=True)
    data_hora_inicio = db.Column(db.DateTime, nullable=False)
    data_hora_fim = db.Column(db.DateTime, nullable=False)
    finalidade = db.Column(db.String(255), nullable=False)
    
    # Campos de Auditoria
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Chaves Estrangeiras
    recurso_id = db.Column(db.Integer, db.ForeignKey('recurso.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False) # Quem solicitou
    status_id = db.Column(db.Integer, db.ForeignKey('status_agendamento.id'), nullable=False)

    # Relacionamentos M:N (Outras pessoas convidadas para o agendamento)
    participantes = db.relationship('Usuario', secondary=participante_agendamento, backref=db.backref('agendamentos_participados', lazy=True))

    """
    IMPORTANTE:
        Se você colocar apenas um UniqueConstraint nos campos (recurso_id, data_hora_inicio), você impede que duas pessoas agendem exatamente às 14:00. 
        Mas não impede que o Usuário A agende das 14:00 às 16:00, e o Usuário B agende das 15:00 às 17:00 (gerando sobreposição).

        Como resolver?
        No PostgreSQL, existe uma trava avançada chamada EXCLUDE constraint (que impede sobreposição de intervalos de tempo). Porém, implementar isso 
        no SQLAlchemy via Alembic é bem complexo.

        A recomendação para agora: Não coloque restrição de horário diretamente no modelo de banco de dados do agendamento. 
        Deixe para tratar isso na Regra de Negócio (no seu arquivo de rotas). Antes de dar o db.session.add(novo_agendamento), você fará uma 
        query verificando se já existe algum agendamento para aquele recurso_id cujos horários se cruzem com o horário solicitado.
    """