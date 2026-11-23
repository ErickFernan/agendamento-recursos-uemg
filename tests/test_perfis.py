from app.models import Perfil


def test_listar_perfis_sem_token_retorna_401(client):
    response = client.get("/api/perfis")
    assert response.status_code == 401


def test_buscar_perfil_por_id_sem_token_retorna_401(client):
    response = client.get("/api/perfis/1")
    assert response.status_code == 401


def test_listar_perfis_sucesso(client, user_token_headers, db_session):
    perfil = Perfil(nome="professor")
    db_session.add(perfil)
    db_session.commit()

    response = client.get("/api/perfis", headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    nomes = [p["nome"] for p in data]
    assert "professor" in nomes


def test_buscar_perfil_por_id_sucesso(client, user_token_headers, db_session):
    perfil = Perfil(nome="comunidade")
    db_session.add(perfil)
    db_session.commit()

    response = client.get(f"/api/perfis/{perfil.id}", headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert data["id"] == perfil.id
    assert data["nome"] == "comunidade"


def test_buscar_perfil_por_id_inexistente_404(client, user_token_headers):
    response = client.get("/api/perfis/9999", headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 404
    assert data["erro"] == "Perfil não encontrado."
    