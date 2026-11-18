import pytest
from app.models import Usuario, Unidade
from app import db
from werkzeug.security import generate_password_hash

def test_login_sucesso(client, db_session):
    # Arrange
    unidade = Unidade(nome="Unidade Belo Horizonte", sigla="UBH", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    usuario = Usuario(
        nome="Teste Login",
        email="teste.login@uemg.br",
        senha_hash=generate_password_hash("123456"),
        unidade_id=unidade.id
    )
    db_session.add(usuario)
    db_session.commit()

    payload = {
        "email": "teste.login@uemg.br",
        "senha": "123456"
    }

    # Act
    response = client.post("/api/login", json=payload)
    data = response.get_json()

    # Assert
    assert response.status_code == 200
    assert data["mensagem"] == "Login realizado com sucesso!"
    assert "access_token" in data
    assert data["usuario"]["nome"] == "Teste Login"


def test_login_senha_incorreta(client, db_session):
    # Arrange
    unidade = Unidade(nome="Unidade Belo Horizonte", sigla="UBH", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    usuario = Usuario(
        nome="Teste Senha",
        email="teste.senha@uemg.br",
        senha_hash=generate_password_hash("123456"),
        unidade_id=unidade.id
    )
    db_session.add(usuario)
    db_session.commit()

    payload = {
        "email": "teste.senha@uemg.br",
        "senha": "senhaerrada"
    }

    # Act
    response = client.post("/api/login", json=payload)
    data = response.get_json()

    # Assert
    assert response.status_code == 401
    assert data["erro"] == "E-mail ou senha incorretos."


def test_login_usuario_inexistente(client):
    # Arrange
    payload = {
        "email": "naoexiste@uemg.br",
        "senha": "123456"
    }

    # Act
    response = client.post("/api/login", json=payload)
    data = response.get_json()

    # Assert
    assert response.status_code == 401
    assert data["erro"] == "E-mail ou senha incorretos."


def test_login_campos_ausentes(client):
    # Arrange - missing senha
    payload = {
        "email": "teste@uemg.br"
    }

    # Act
    response = client.post("/api/login", json=payload)
    data = response.get_json()

    # Assert
    assert response.status_code == 400
    assert data["erro"] == "Dados inválidos"
    assert "detalhes" in data


def test_login_email_invalido(client):
    # Arrange
    payload = {
        "email": "emailinvalido",
        "senha": "123456"
    }

    # Act
    response = client.post("/api/login", json=payload)
    data = response.get_json()

    # Assert
    assert response.status_code == 400
    assert data["erro"] == "Dados inválidos"
    assert "email" in data["detalhes"]


def test_login_senha_curta(client):
    # Arrange
    payload = {
        "email": "teste@uemg.br",
        "senha": "123"
    }

    # Act
    response = client.post("/api/login", json=payload)
    data = response.get_json()

    # Assert
    assert response.status_code == 400
    assert data["erro"] == "Dados inválidos"
    assert "senha" in data["detalhes"]
