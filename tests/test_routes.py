import pytest


def test_rota_inexistente_404(client):
    response = client.get("/api/v1/rota-que-nao-existe")
    assert response.status_code == 404


def test_metodo_nao_permitido_405(client):
    response = client.get("/api/login")
    assert response.status_code == 405


def test_health_check_200(client):
    response = client.get("/health")
    assert response.status_code == 200