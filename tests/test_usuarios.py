import pytest
from app.models import Usuario, Unidade
from app import db
from werkzeug.security import generate_password_hash

def test_criar_usuario_sucesso(client, admin_token_headers, db_session):
    unidade = Unidade(nome="Unidade Teste Usuario", sigla="UTU", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    payload = {
        "nome": "Novo Usuario",
        "email": "novo.usuario@uemg.br",
        "senha": "password123",
        "unidade_id": unidade.id
    }
    response = client.post("/api/usuarios", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 201
    assert data["mensagem"] == "Usuário criado com sucesso!"
    assert data["usuario"]["nome"] == "Novo Usuario"
    assert data["usuario"]["email"] == "novo.usuario@uemg.br"
    assert "senha" not in data["usuario"]
    assert "senha_hash" not in data["usuario"]

def test_criar_usuario_email_duplicado(client, admin_token_headers, db_session):
    unidade = Unidade(nome="Unidade Teste Duplicado", sigla="UTD", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    usuario = Usuario(
        nome="Usuario Existente",
        email="duplicado@uemg.br",
        senha_hash=generate_password_hash("123456"),
        unidade_id=unidade.id
    )
    db_session.add(usuario)
    db_session.commit()

    payload = {
        "nome": "Outro Usuario",
        "email": "duplicado@uemg.br",
        "senha": "password123",
        "unidade_id": unidade.id
    }
    response = client.post("/api/usuarios", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 409
    assert data["erro"] == "Este e-mail já está em uso por outro usuário."

def test_criar_usuario_payload_invalido(client, admin_token_headers, db_session):
    unidade = Unidade(nome="Unidade Teste Invalido", sigla="UTI", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    payload = {
        "nome": "Usuario Invalido",
        "email": "emailinvalido",
        "senha": "123",
        "unidade_id": unidade.id
    }
    response = client.post("/api/usuarios", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 400
    assert data["erro"] == "Dados inválidos"
    assert "email" in data["detalhes"]
    assert "senha" in data["detalhes"]

def test_criar_usuario_unidade_inexistente(client, admin_token_headers):
    payload = {
        "nome": "Usuario Sem Unidade",
        "email": "semunidade@uemg.br",
        "senha": "password123",
        "unidade_id": 9999
    }
    response = client.post("/api/usuarios", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 404
    assert data["erro"] == "A unidade informada não existe."

def test_criar_usuario_sem_token(client):
    payload = {
        "nome": "Usuario Sem Token",
        "email": "semtoken@uemg.br",
        "senha": "password123",
        "unidade_id": 1
    }
    response = client.post("/api/usuarios", json=payload)
    assert response.status_code == 401

def test_criar_usuario_sem_permissao(client, user_token_headers, db_session):
    unidade = Unidade(nome="Unidade Teste Permissao", sigla="UTP", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    payload = {
        "nome": "Usuario Nao Admin",
        "email": "naoadmin@uemg.br",
        "senha": "password123",
        "unidade_id": unidade.id
    }
    response = client.post("/api/usuarios", json=payload, headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 403
    assert data["erro"] == "Acesso negado. Requer privilégios de administrador."

def test_listar_usuarios_sucesso(client, admin_token_headers, db_session):
    response = client.get("/api/usuarios", headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)

def test_listar_usuarios_sem_permissao(client, user_token_headers):
    response = client.get("/api/usuarios", headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 403
    assert data["erro"] == "Acesso negado. Requer privilégios de administrador."

def test_atualizar_usuario_put_sucesso(client, admin_token_headers, db_session):
    unidade = Unidade(nome="Unidade Put", sigla="UPUT", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    usuario = Usuario(
        nome="Nome Antigo",
        email="antigo@uemg.br",
        senha_hash=generate_password_hash("123456"),
        unidade_id=unidade.id
    )
    db_session.add(usuario)
    db_session.commit()

    payload = {
        "nome": "Nome Novo",
        "email": "novo@uemg.br",
        "unidade_id": unidade.id
    }
    response = client.put(f"/api/usuarios/{usuario.id}", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert data["mensagem"] == "Usuário atualizado com sucesso!"
    assert data["usuario"]["nome"] == "Nome Novo"
    assert data["usuario"]["email"] == "novo@uemg.br"
    assert "senha" not in data["usuario"]
    assert "senha_hash" not in data["usuario"]

def test_atualizar_usuario_patch_sucesso(client, admin_token_headers, db_session):
    unidade = Unidade(nome="Unidade Patch", sigla="UPAT", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    usuario = Usuario(
        nome="Nome Parcial",
        email="parcial@uemg.br",
        senha_hash=generate_password_hash("123456"),
        unidade_id=unidade.id
    )
    db_session.add(usuario)
    db_session.commit()

    payload = {
        "nome": "Nome Parcial Atualizado"
    }
    response = client.patch(f"/api/usuarios/{usuario.id}", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert data["mensagem"] == "Usuário atualizado com sucesso!"
    assert data["usuario"]["nome"] == "Nome Parcial Atualizado"

def test_atualizar_usuario_inexistente_404(client, admin_token_headers, db_session):
    unidade = Unidade(nome="Unidade 404", sigla="U404", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    payload = {
        "nome": "Qualquer",
        "email": "qualquer@uemg.br",
        "unidade_id": unidade.id
    }
    response = client.put("/api/usuarios/9999", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 404
    assert data["erro"] == "Usuário não encontrado."

def test_deletar_usuario_sucesso(client, admin_token_headers, db_session):
    unidade = Unidade(nome="Unidade Delete", sigla="UDEL", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    usuario = Usuario(
        nome="Para Deletar",
        email="deletar@uemg.br",
        senha_hash=generate_password_hash("123456"),
        unidade_id=unidade.id
    )
    db_session.add(usuario)
    db_session.commit()

    response = client.delete(f"/api/usuarios/{usuario.id}", headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert data["mensagem"] == "Usuário deletado com sucesso!"

def test_deletar_usuario_inexistente_404(client, admin_token_headers):
    response = client.delete("/api/usuarios/9999", headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 404
    assert data["erro"] == "Usuário não encontrado."

def test_resetar_senha_sucesso(client, admin_token_headers, db_session):
    unidade = Unidade(nome="Unidade Reset", sigla="URES", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    usuario = Usuario(
        nome="Reset Senha",
        email="reset@uemg.br",
        senha_hash=generate_password_hash("123456"),
        unidade_id=unidade.id
    )
    db_session.add(usuario)
    db_session.commit()

    payload = {
        "nova_senha": "newpassword123"
    }
    response = client.patch(f"/api/usuarios/{usuario.id}/resetar-senha", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert data["mensagem"] == "Senha atualizada com sucesso!"

