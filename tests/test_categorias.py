from app.models import CategoriaRecurso, Recurso


def test_listar_categorias_sem_token_retorna_401(client):
    response = client.get("/api/categorias")
    assert response.status_code == 401


def test_criar_categoria_sem_token_retorna_401(client):
    response = client.post("/api/categorias", json={"nome": "Laboratório"})
    assert response.status_code == 401


def test_criar_categoria_sucesso(client, admin_token_headers):
    payload = {
        "nome": "Laboratório de Informática",
        "descricao": "Salas com computadores para aulas práticas"
    }
    response = client.post("/api/categorias", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 201
    assert data["mensagem"] == "Categoria criada com sucesso!"
    assert data["categoria"]["nome"] == "Laboratório de Informática"
    assert data["categoria"]["descricao"] == "Salas com computadores para aulas práticas"


def test_criar_categoria_como_aluno_retorna_403(client, user_token_headers):
    payload = {"nome": "Auditório"}
    response = client.post("/api/categorias", json=payload, headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 403
    assert data["erro"] == "Acesso negado. Requer privilégios de administrador."


def test_criar_categoria_payload_invalido_400(client, admin_token_headers):
    payload = {"nome": "A"}
    response = client.post("/api/categorias", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 400
    assert data["erro"] == "Dados inválidos"
    assert "nome" in data["detalhes"]


def test_criar_categoria_nome_duplicado_409(client, admin_token_headers, db_session):
    categoria = CategoriaRecurso(nome="Quadra", descricao="Quadra poliesportiva")
    db_session.add(categoria)
    db_session.commit()

    payload = {"nome": "Quadra", "descricao": "Outra descrição"}
    response = client.post("/api/categorias", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 409
    assert data["erro"] == "Já existe uma categoria com este nome."


def test_listar_categorias_sucesso(client, user_token_headers, db_session):
    categoria = CategoriaRecurso(nome="Sala de Aula", descricao="Salas convencionais")
    db_session.add(categoria)
    db_session.commit()

    response = client.get("/api/categorias", headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["nome"] == "Sala de Aula"


def test_buscar_categoria_por_id_sucesso(client, user_token_headers, db_session):
    categoria = CategoriaRecurso(nome="Auditório", descricao="Eventos e palestras")
    db_session.add(categoria)
    db_session.commit()

    response = client.get(f"/api/categorias/{categoria.id}", headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert data["nome"] == "Auditório"


def test_buscar_categoria_por_id_inexistente_404(client, user_token_headers):
    response = client.get("/api/categorias/9999", headers=user_token_headers)
    data = response.get_json()

    assert response.status_code == 404
    assert data["erro"] == "Categoria não encontrada."


def test_atualizar_categoria_put_sucesso(client, admin_token_headers, db_session):
    categoria = CategoriaRecurso(nome="Lab Antigo", descricao="Descrição antiga")
    db_session.add(categoria)
    db_session.commit()

    payload = {
        "nome": "Lab Novo",
        "descricao": "Descrição atualizada"
    }
    response = client.put(
        f"/api/categorias/{categoria.id}",
        json=payload,
        headers=admin_token_headers
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["mensagem"] == "Categoria atualizada com sucesso!"
    assert data["categoria"]["nome"] == "Lab Novo"
    assert data["categoria"]["descricao"] == "Descrição atualizada"


def test_atualizar_categoria_put_como_aluno_retorna_403(client, user_token_headers, db_session):
    categoria = CategoriaRecurso(nome="Lab Restrito", descricao="Apenas admin edita")
    db_session.add(categoria)
    db_session.commit()

    payload = {"nome": "Tentativa", "descricao": "Nova"}
    response = client.put(
        f"/api/categorias/{categoria.id}",
        json=payload,
        headers=user_token_headers
    )
    assert response.status_code == 403


def test_atualizar_categoria_put_inexistente_404(client, admin_token_headers):
    payload = {"nome": "Qualquer", "descricao": "Qualquer"}
    response = client.put("/api/categorias/9999", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 404
    assert data["erro"] == "Categoria não encontrada."


def test_atualizar_categoria_patch_sucesso(client, admin_token_headers, db_session):
    categoria = CategoriaRecurso(nome="Biblioteca", descricao="Descrição original")
    db_session.add(categoria)
    db_session.commit()

    payload = {"descricao": "Descrição parcialmente alterada"}
    response = client.patch(
        f"/api/categorias/{categoria.id}",
        json=payload,
        headers=admin_token_headers
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["mensagem"] == "Categoria atualizada parcialmente com sucesso!"
    assert data["categoria"]["nome"] == "Biblioteca"
    assert data["categoria"]["descricao"] == "Descrição parcialmente alterada"


def test_atualizar_categoria_patch_inexistente_404(client, admin_token_headers):
    payload = {"descricao": "Teste"}
    response = client.patch("/api/categorias/9999", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 404
    assert data["erro"] == "Categoria não encontrada."


def test_deletar_categoria_sucesso(client, admin_token_headers, db_session):
    categoria = CategoriaRecurso(nome="Categoria Deletar", descricao="Será removida")
    db_session.add(categoria)
    db_session.commit()

    response = client.delete(f"/api/categorias/{categoria.id}", headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert data["mensagem"] == "Categoria deletada com sucesso!"
    assert db_session.get(CategoriaRecurso, categoria.id) is None


def test_deletar_categoria_como_aluno_retorna_403(client, user_token_headers, db_session):
    categoria = CategoriaRecurso(nome="Categoria Protegida")
    db_session.add(categoria)
    db_session.commit()

    response = client.delete(f"/api/categorias/{categoria.id}", headers=user_token_headers)
    assert response.status_code == 403


def test_deletar_categoria_inexistente_404(client, admin_token_headers):
    response = client.delete("/api/categorias/9999", headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 404
    assert data["erro"] == "Categoria não encontrada."


def test_deletar_categoria_com_vinculo_409(client, admin_token_headers, db_session, unidade_padrao):
    categoria = CategoriaRecurso(nome="Categoria Vinculada")
    db_session.add(categoria)
    db_session.commit()

    recurso = Recurso(
        nome="Sala Vinculada",
        capacidade=30,
        unidade_id=unidade_padrao,
        categoria_id=categoria.id
    )
    db_session.add(recurso)
    db_session.commit()

    response = client.delete(f"/api/categorias/{categoria.id}", headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 409
    assert "Não é possível deletar" in data["erro"]
    