import pytest
from app.models import Unidade, Usuario
from werkzeug.security import generate_password_hash


def test_criar_unidade_sucesso(client, admin_token_headers):
    payload = {
        "nome": "Faculdade de Engenharia",
        "sigla": "FE",
        "cidade": "Belo Horizonte",
        "estado": "MG"
    }
    response = client.post("/api/unidades", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 201
    assert data["mensagem"] == "Unidade criada com sucesso!"
    assert data["unidade"]["nome"] == "Faculdade de Engenharia"
    assert data["unidade"]["sigla"] == "FE"


def test_criar_unidade_payload_invalido(client, admin_token_headers):
    payload = {
        "nome": "Faculdade",
        "sigla": "",
        "cidade": "BH",
        "estado": "MINAS"
    }
    response = client.post("/api/unidades", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 400
    assert data["erro"] == "Dados inválidos"
    assert "detalhes" in data


def test_criar_unidade_sem_token(client):
    payload = {
        "nome": "Faculdade de Engenharia",
        "sigla": "FE",
        "cidade": "Belo Horizonte",
        "estado": "MG"
    }
    response = client.post("/api/unidades", json=payload)
    assert response.status_code == 401


def test_criar_unidade_sem_permissao(client, user_token_headers):
    payload = {
        "nome": "Faculdade de Engenharia",
        "sigla": "FE",
        "cidade": "Belo Horizonte",
        "estado": "MG"
    }
    response = client.post("/api/unidades", json=payload, headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 403
    assert data["erro"] == "Acesso negado. Requer privilégios de administrador."


def test_listar_unidades_sucesso(client, user_token_headers, db_session):
    unidade = Unidade(nome="Unidade Central", sigla="UC", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    response = client.get("/api/unidades", headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) >= 1


def test_atualizar_unidade_put_sucesso(client, admin_token_headers, db_session):
    unidade = Unidade(nome="Unidade Antiga", sigla="UA", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    payload = {
        "nome": "Unidade Nova",
        "sigla": "UN",
        "cidade": "Contagem",
        "estado": "MG"
    }
    response = client.put(f"/api/unidades/{unidade.id}", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert data["mensagem"] == "Unidade atualizada com sucesso!"
    assert data["unidade"]["nome"] == "Unidade Nova"
    assert data["unidade"]["cidade"] == "Contagem"


def test_atualizar_unidade_patch_sucesso(client, admin_token_headers, db_session):
    unidade = Unidade(nome="Unidade Parcial", sigla="UP", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    payload = {
        "nome": "Unidade Parcial Alterada"
    }
    response = client.patch(f"/api/unidades/{unidade.id}", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert data["mensagem"] == "Unidade atualizada parcialmente com sucesso!"
    assert data["unidade"]["nome"] == "Unidade Parcial Alterada"
    assert data["unidade"]["sigla"] == "UP"


def test_deletar_unidade_sucesso(client, admin_token_headers, db_session):
    unidade = Unidade(nome="Unidade Deletar", sigla="UD", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    response = client.delete(f"/api/unidades/{unidade.id}", headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert data["mensagem"] == "Unidade deletada com sucesso!"


def test_atualizar_unidade_inexistente_404(client, admin_token_headers):
    payload = {
        "nome": "Qualquer",
        "sigla": "QQ",
        "cidade": "BH",
        "estado": "MG"
    }
    response = client.put("/api/unidades/9999", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 404
    assert data["erro"] == "Unidade não encontrada."


def test_deletar_unidade_inexistente_404(client, admin_token_headers):
    response = client.delete("/api/unidades/9999", headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 404
    assert data["erro"] == "Unidade não encontrada."


def test_deletar_unidade_com_vinculo_409(client, admin_token_headers, db_session):
    unidade = Unidade(nome="Unidade Vinculada", sigla="UV", cidade="Belo Horizonte", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    usuario = Usuario(
        nome="Usuario Vinculo",
        email="vinculo@uemg.br",
        senha_hash=generate_password_hash("123456"),
        unidade_id=unidade.id
    )
    db_session.add(usuario)
    db_session.commit()

    response = client.delete(f"/api/unidades/{unidade.id}", headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 409
    assert "Não é possível deletar" in data["erro"]


def test_buscar_unidade_por_id_sucesso(client, user_token_headers, db_session):
    unidade = Unidade(nome="Unidade Busca", sigla="UB", cidade="Carangola", estado="MG")
    db_session.add(unidade)
    db_session.commit()

    response = client.get(f"/api/unidades/{unidade.id}", headers=user_token_headers)

    assert response.status_code == 200
    assert response.get_json()["nome"] == "Unidade Busca"


def test_buscar_unidade_por_id_inexistente_404(client, user_token_headers):
    response = client.get("/api/unidades/9999", headers=user_token_headers)
    assert response.status_code == 404