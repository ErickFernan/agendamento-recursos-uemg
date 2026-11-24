from app.models import StatusAgendamento


def test_listar_status_agendamento_sem_token_retorna_401(client):
    response = client.get("/api/status-agendamento")
    assert response.status_code == 401


def test_buscar_status_agendamento_por_id_sem_token_retorna_401(client):
    response = client.get("/api/status-agendamento/1")
    assert response.status_code == 401


def test_listar_status_agendamento_sucesso(client, user_token_headers, db_session):
    status = StatusAgendamento(nome="Pendente")
    db_session.add(status)
    db_session.commit()

    response = client.get("/api/status-agendamento", headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["nome"] == "Pendente"


def test_buscar_status_agendamento_por_id_sucesso(client, user_token_headers, db_session):
    status = StatusAgendamento(nome="Confirmado")
    db_session.add(status)
    db_session.commit()

    response = client.get(f"/api/status-agendamento/{status.id}", headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert data["id"] == status.id
    assert data["nome"] == "Confirmado"


def test_buscar_status_agendamento_por_id_inexistente_404(client, user_token_headers):
    response = client.get("/api/status-agendamento/9999", headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 400
    assert data["erro"] == "Status de agendamento não encontrado."