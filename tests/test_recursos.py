from app.models import Unidade, CategoriaRecurso, Recurso


def _criar_dependencias(db_session):
    """Cria uma Unidade e uma CategoriaRecurso exclusivas para o teste."""
    unidade = Unidade(
        nome="Unidade Recursos Teste",
        sigla="URT",
        cidade="Carangola",
        estado="MG"
    )
    categoria = CategoriaRecurso(
        nome="Laboratório",
        descricao="Laboratórios de informática"
    )
    db_session.add_all([unidade, categoria])
    db_session.commit()
    return unidade, categoria


def test_listar_recursos_sem_token_retorna_401(client):
    response = client.get("/api/recursos")
    assert response.status_code == 401


def test_criar_recurso_sem_token_retorna_401(client):
    response = client.post("/api/recursos", json={})
    assert response.status_code == 401


def test_criar_recurso_como_aluno_retorna_403(client, user_token_headers, db_session):
    unidade, categoria = _criar_dependencias(db_session)

    payload = {
        "nome": "Lab Proibido",
        "capacidade": 25,
        "unidade_id": unidade.id,
        "categoria_id": categoria.id
    }
    response = client.post("/api/recursos", json=payload, headers=user_token_headers)

    assert response.status_code == 403
    assert response.get_json()["erro"] == "Acesso negado. Requer privilégios de administrador."


def test_criar_recurso_sucesso(client, admin_token_headers, db_session):
    unidade, categoria = _criar_dependencias(db_session)

    payload = {
        "nome": "Laboratório de Redes",
        "capacidade": 30,
        "unidade_id": unidade.id,
        "categoria_id": categoria.id
    }
    response = client.post("/api/recursos", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 201
    assert data["mensagem"] == "Recurso criado com sucesso!"
    assert data["recurso"]["nome"] == "Laboratório de Redes"


def test_criar_recurso_duplicado_retorna_409(client, admin_token_headers, db_session):
    unidade, categoria = _criar_dependencias(db_session)
    recurso_existente = Recurso(
        nome="Laboratório de Redes",
        capacidade=30,
        unidade_id=unidade.id,
        categoria_id=categoria.id
    )
    db_session.add(recurso_existente)
    db_session.commit()

    payload = {
        "nome": "Laboratório de Redes",
        "capacidade": 30,
        "unidade_id": unidade.id,
        "categoria_id": categoria.id
    }
    response = client.post("/api/recursos", json=payload, headers=admin_token_headers)

    assert response.status_code == 409


def test_listar_recursos_com_filtro_unidade(client, user_token_headers, db_session):
    unidade, categoria = _criar_dependencias(db_session)
    recurso = Recurso(
        nome="Auditório Principal",
        capacidade=100,
        unidade_id=unidade.id,
        categoria_id=categoria.id
    )
    db_session.add(recurso)
    db_session.commit()

    response = client.get(f"/api/recursos?unidade_id={unidade.id}", headers=user_token_headers)

    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_buscar_recurso_por_id_sucesso(client, user_token_headers, db_session):
    unidade, categoria = _criar_dependencias(db_session)
    recurso = Recurso(
        nome="Auditório Principal",
        capacidade=100,
        unidade_id=unidade.id,
        categoria_id=categoria.id
    )
    db_session.add(recurso)
    db_session.commit()

    response = client.get(f"/api/recursos/{recurso.id}", headers=user_token_headers)

    assert response.status_code == 200
    assert response.get_json()["nome"] == "Auditório Principal"


def test_buscar_recurso_por_id_inexistente_404(client, user_token_headers):
    response = client.get("/api/recursos/9999", headers=user_token_headers)
    assert response.status_code == 404


def test_atualizar_recurso_patch_sucesso(client, admin_token_headers, db_session):
    unidade, categoria = _criar_dependencias(db_session)
    recurso = Recurso(
        nome="Sala 101",
        capacidade=30,
        unidade_id=unidade.id,
        categoria_id=categoria.id
    )
    db_session.add(recurso)
    db_session.commit()

    response = client.patch(
        f"/api/recursos/{recurso.id}",
        json={"capacidade": 35},
        headers=admin_token_headers
    )

    assert response.status_code == 200
    assert response.get_json()["recurso"]["capacidade"] == 35


def test_atualizar_recurso_put_sucesso(client, admin_token_headers, db_session):
    unidade, categoria = _criar_dependencias(db_session)
    recurso = Recurso(
        nome="Sala 101",
        capacidade=30,
        unidade_id=unidade.id,
        categoria_id=categoria.id
    )
    db_session.add(recurso)
    db_session.commit()

    payload_put = {
        "nome": "Sala 101 Reformada",
        "capacidade": 40,
        "unidade_id": unidade.id,
        "categoria_id": categoria.id
    }
    response = client.put(
        f"/api/recursos/{recurso.id}",
        json=payload_put,
        headers=admin_token_headers
    )

    assert response.status_code == 200
    assert response.get_json()["recurso"]["nome"] == "Sala 101 Reformada"


def test_deletar_recurso_como_aluno_retorna_403(client, user_token_headers, db_session):
    unidade, categoria = _criar_dependencias(db_session)
    recurso = Recurso(
        nome="Quadra Coberta",
        capacidade=50,
        unidade_id=unidade.id,
        categoria_id=categoria.id
    )
    db_session.add(recurso)
    db_session.commit()

    response = client.delete(f"/api/recursos/{recurso.id}", headers=user_token_headers)
    assert response.status_code == 403


def test_deletar_recurso_como_admin_sucesso(client, admin_token_headers, db_session):
    unidade, categoria = _criar_dependencias(db_session)
    recurso = Recurso(
        nome="Sala Para Deletar",
        capacidade=20,
        unidade_id=unidade.id,
        categoria_id=categoria.id
    )
    db_session.add(recurso)
    db_session.commit()

    response = client.delete(f"/api/recursos/{recurso.id}", headers=admin_token_headers)

    assert response.status_code == 200
    assert response.get_json()["mensagem"] == "Recurso deletado com sucesso!"
    assert db_session.get(Recurso, recurso.id) is None