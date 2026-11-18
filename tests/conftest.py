import os
os.environ["TESTING"] = "True"

import pytest
from app import create_app, db
from app.models import Usuario, Unidade, Perfil
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope='function')
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False}
        },
        "JWT_SECRET_KEY": "2912caec3e5d084b955dab8de18b9207f80130a7ef5c07ed6630546bc5761600",
        "WTF_CSRF_ENABLED": False
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    return db.session


@pytest.fixture(scope='function')
def unidade_padrao(app):
    with app.app_context():
        unidade = Unidade(
            nome="Unidade Teste",
            sigla="UT",
            cidade="Belo Horizonte",
            estado="MG"
        )
        db.session.add(unidade)
        db.session.commit()
        return unidade.id


@pytest.fixture(scope='function')
def admin_token_headers(app, unidade_padrao):
    with app.app_context():
        perfil_admin = Perfil(nome="admin")
        db.session.add(perfil_admin)
        db.session.commit()

        usuario_admin = Usuario(
            nome="Admin Teste",
            email="admin@uemg.br",
            senha_hash=generate_password_hash("123456"),
            unidade_id=unidade_padrao
        )
        usuario_admin.perfis.append(perfil_admin)
        db.session.add(usuario_admin)
        db.session.commit()

        token = create_access_token(
            identity=str(usuario_admin.id),
            additional_claims={
                "perfis": ["admin"],
                "nome": usuario_admin.nome
            }
        )
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope='function')
def user_token_headers(app, unidade_padrao):
    with app.app_context():
        perfil_aluno = Perfil(nome="aluno")
        db.session.add(perfil_aluno)
        db.session.commit()

        usuario_comum = Usuario(
            nome="Usuario Comum",
            email="comum@uemg.br",
            senha_hash=generate_password_hash("123456"),
            unidade_id=unidade_padrao
        )
        usuario_comum.perfis.append(perfil_aluno)
        db.session.add(usuario_comum)
        db.session.commit()

        token = create_access_token(
            identity=str(usuario_comum.id),
            additional_claims={
                "perfis": ["aluno"],
                "nome": usuario_comum.nome
            }
        )
        return {"Authorization": f"Bearer {token}"}