import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.models import (
    Unidade,
    CategoriaRecurso,
    StatusAgendamento,
    Perfil,
    Usuario,
    Recurso,
    Agendamento,
)
from werkzeug.security import generate_password_hash


def test_criar_unidade_model(app, db_session):
    unidade = Unidade(
        nome="Unidade Central", sigla="UC", cidade="Belo Horizonte", estado="MG"
    )
    db_session.add(unidade)
    db_session.commit()

    assert unidade.id is not None
    assert unidade.nome == "Unidade Central"
    assert unidade.sigla == "UC"
    assert unidade.cidade == "Belo Horizonte"
    assert unidade.estado == "MG"
    assert unidade.created_at is not None
    assert unidade.updated_at is not None


def test_unidade_unique_constraint(app, db_session):
    u1 = Unidade(nome="Campus I", sigla="C1", cidade="Uberaba", estado="MG")
    db_session.add(u1)
    db_session.commit()

    u2 = Unidade(nome="Campus I", sigla="C2", cidade="Uberaba", estado="MG")
    db_session.add(u2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_criar_categoria_recurso_model(app, db_session):
    cat = CategoriaRecurso(nome="Laboratório", descricao="Labs de Informática")
    db_session.add(cat)
    db_session.commit()

    assert cat.id is not None
    assert cat.nome == "Laboratório"


def test_criar_status_agendamento_model(app, db_session):
    status = StatusAgendamento(nome="Pendente")
    db_session.add(status)
    db_session.commit()

    assert status.id is not None
    assert status.nome == "Pendente"


def test_criar_perfil_model(app, db_session):
    perfil = Perfil(nome="professor")
    db_session.add(perfil)
    db_session.commit()

    assert perfil.id is not None
    assert perfil.nome == "professor"


def test_criar_usuario_com_perfil_model(app, db_session):
    unidade = Unidade(nome="Unidade Sul", sigla="US", cidade="Passos", estado="MG")
    perfil = Perfil(nome="professor")
    db_session.add_all([unidade, perfil])
    db_session.commit()

    usuario = Usuario(
        nome="Professor Teste",
        email="prof@uemg.br",
        senha_hash=generate_password_hash("123456"),
        unidade_id=unidade.id,
    )
    usuario.perfis.append(perfil)
    db_session.add(usuario)
    db_session.commit()

    assert usuario.id is not None
    assert usuario.unidade.nome == "Unidade Sul"
    assert len(usuario.perfis) == 1
    assert usuario.perfis[0].nome == "professor"
    assert perfil.usuarios[0].nome == "Professor Teste"


def test_recurso_model(app, db_session):
    unidade = Unidade(nome="Unidade Leste", sigla="UL", cidade="Divinópolis", estado="MG")
    cat = CategoriaRecurso(nome="Auditório", descricao="Auditório principal")
    db_session.add_all([unidade, cat])
    db_session.commit()

    recurso = Recurso(
        nome="Auditório A", capacidade=100, unidade_id=unidade.id, categoria_id=cat.id
    )
    db_session.add(recurso)
    db_session.commit()

    assert recurso.id is not None
    assert recurso.unidade.nome == "Unidade Leste"
    assert recurso.categoria.nome == "Auditório"


def test_agendamento_model(app, db_session):
    unidade = Unidade(nome="Unidade Norte", sigla="UN", cidade="Muzambinho", estado="MG")
    cat = CategoriaRecurso(nome="Quadra", descricao="Quadra poliesportiva")
    status = StatusAgendamento(nome="Confirmado")
    db_session.add_all([unidade, cat, status])
    db_session.commit()

    usuario = Usuario(
        nome="Aluno Teste",
        email="aluno@uemg.br",
        senha_hash=generate_password_hash("123456"),
        unidade_id=unidade.id,
    )
    recurso = Recurso(
        nome="Quadra Coberta", capacidade=50, unidade_id=unidade.id, categoria_id=cat.id
    )
    db_session.add_all([usuario, recurso])
    db_session.commit()

    agendamento = Agendamento(
        data_hora_inicio=datetime(2026, 11, 20, 10, 0, 0),
        data_hora_fim=datetime(2026, 11, 20, 12, 0, 0),
        finalidade="Aula prática",
        recurso_id=recurso.id,
        usuario_id=usuario.id,
        status_id=status.id,
    )
    agendamento.participantes.append(usuario)
    db_session.add(agendamento)
    db_session.commit()

    assert agendamento.id is not None
    assert agendamento.solicitante.nome == "Aluno Teste"
    assert agendamento.recurso.nome == "Quadra Coberta"
    assert agendamento.status.nome == "Confirmado"
    assert len(agendamento.participantes) == 1