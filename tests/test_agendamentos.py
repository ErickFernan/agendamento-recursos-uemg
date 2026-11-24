from datetime import datetime
import pytest
from werkzeug.security import generate_password_hash
from app.models import (
    Unidade,
    CategoriaRecurso,
    Recurso,
    Perfil,
    Usuario,
    StatusAgendamento,
    Agendamento,
)


def _get_or_create_perfil(db_session, nome):
    perfil = db_session.scalar(db_session.query(Perfil).filter_by(nome=nome).statement)
    if not perfil:
        perfil = Perfil(nome=nome)
        db_session.add(perfil)
        db_session.flush()
    return perfil


def _get_or_create_status(db_session, nome):
    status = db_session.scalar(db_session.query(StatusAgendamento).filter_by(nome=nome).statement)
    if not status:
        status = StatusAgendamento(nome=nome)
        db_session.add(status)
        db_session.flush()
    return status


def _criar_usuario_e_headers(client, db_session, unidade_id, nome, email, nome_perfil):
    perfil = _get_or_create_perfil(db_session, nome_perfil)
    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=generate_password_hash("Senha123"),
        unidade_id=unidade_id,
    )
    usuario.perfis.append(perfil)
    db_session.add(usuario)
    db_session.commit()

    resp = client.post("/api/login", json={"email": email, "senha": "Senha123"})
    token = resp.get_json()["access_token"]
    return usuario, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def cenario_agendamento(client, db_session):
    """Cria a estrutura base (Unidade, Categoria, Recurso, Status e Usuários) para os testes."""
    for nome_status in ["Pendente", "Confirmado", "Cancelado", "Rejeitado", "Concluído"]:
        _get_or_create_status(db_session, nome_status)

    unidade = Unidade(
        nome="UEMG Teste Agendamento",
        sigla="UEMG-AG",
        cidade="Carangola",
        estado="MG",
    )
    categoria = CategoriaRecurso(nome="Laboratório Teste", descricao="Lab para testes")
    db_session.add_all([unidade, categoria])
    db_session.flush()

    recurso = Recurso(
        nome="Lab 01",
        capacidade=30,
        unidade_id=unidade.id,
        categoria_id=categoria.id,
    )
    db_session.add(recurso)
    db_session.commit()

    aluno1, aluno1_headers = _criar_usuario_e_headers(
        client, db_session, unidade.id, "Aluno Um", "aluno1.ag@uemg.br", "aluno"
    )
    aluno2, aluno2_headers = _criar_usuario_e_headers(
        client, db_session, unidade.id, "Aluno Dois", "aluno2.ag@uemg.br", "aluno"
    )
    prof1, prof1_headers = _criar_usuario_e_headers(
        client, db_session, unidade.id, "Professor Um", "prof1.ag@uemg.br", "professor"
    )
    prof2, prof2_headers = _criar_usuario_e_headers(
        client, db_session, unidade.id, "Professor Dois", "prof2.ag@uemg.br", "professor"
    )

    status_map = {
        s.nome: s
        for s in db_session.query(StatusAgendamento).all()
    }

    return {
        "unidade": unidade,
        "recurso": recurso,
        "aluno1": aluno1,
        "aluno1_headers": aluno1_headers,
        "aluno2": aluno2,
        "aluno2_headers": aluno2_headers,
        "prof1": prof1,
        "prof1_headers": prof1_headers,
        "prof2": prof2,
        "prof2_headers": prof2_headers,
        "status": status_map,
    }


# ==========================================
# AUTENTICAÇÃO (401)
# ==========================================

def test_listar_agendamentos_sem_token_401(client):
    response = client.get("/api/agendamentos")
    assert response.status_code == 401


def test_criar_agendamento_sem_token_401(client):
    response = client.post("/api/agendamentos", json={})
    assert response.status_code == 401


# ==========================================
# CRIAÇÃO E REGRAS DE NEGÓCIO (POST)
# ==========================================

def test_aluno_cria_agendamento_sucesso_nasce_pendente(client, cenario_agendamento):
    payload = {
        "data_hora_inicio": "2026-12-01T14:00:00",
        "data_hora_fim": "2026-12-01T16:00:00",
        "finalidade": "Estudo em grupo",
        "recurso_id": cenario_agendamento["recurso"].id,
        "participantes_ids": [cenario_agendamento["aluno2"].id],
    }

    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["aluno1_headers"],
    )
    data = response.get_json()

    assert response.status_code == 201
    assert data["agendamento"]["usuario_id"] == cenario_agendamento["aluno1"].id
    assert data["agendamento"]["status_id"] == cenario_agendamento["status"]["Pendente"].id
    assert len(data["agendamento"]["participantes"]) == 1
    assert data["agendamento"]["participantes"][0]["id"] == cenario_agendamento["aluno2"].id


def test_admin_cria_agendamento_fora_do_horario_para_aluno_sucesso(
    client, admin_token_headers, cenario_agendamento
):
    payload = {
        "data_hora_inicio": "2026-12-01T23:00:00",
        "data_hora_fim": "2026-12-02T01:00:00",
        "finalidade": "Evento noturno especial",
        "recurso_id": cenario_agendamento["recurso"].id,
        "usuario_id": cenario_agendamento["aluno1"].id,
    }

    response = client.post("/api/agendamentos", json=payload, headers=admin_token_headers)
    data = response.get_json()

    assert response.status_code == 201
    assert data["agendamento"]["usuario_id"] == cenario_agendamento["aluno1"].id
    assert data["agendamento"]["status_id"] == cenario_agendamento["status"]["Confirmado"].id


def test_aluno_fora_do_horario_funcionamento_retorna_400(client, cenario_agendamento):
    payload = {
        "data_hora_inicio": "2026-12-01T21:00:00",
        "data_hora_fim": "2026-12-01T23:00:00",
        "finalidade": "Reunião tarde",
        "recurso_id": cenario_agendamento["recurso"].id,
    }

    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["aluno1_headers"],
    )
    assert response.status_code == 400


def test_aluno_nao_pode_agendar_em_fim_de_semana_400(client, cenario_agendamento):
    # 2026-12-05 é sábado
    payload = {
        "data_hora_inicio": "2026-12-05T10:00:00",
        "data_hora_fim": "2026-12-05T12:00:00",
        "finalidade": "Estudo no sábado",
        "recurso_id": cenario_agendamento["recurso"].id,
    }

    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["aluno1_headers"],
    )
    data = response.get_json()

    assert response.status_code == 400
    assert "sábados ou domingos" in data["erro"]


def test_aluno_nao_pode_agendar_em_feriado_400(client, cenario_agendamento):
    # 2026-12-25 é sexta-feira (Natal - feriado nacional)
    payload = {
        "data_hora_inicio": "2026-12-25T10:00:00",
        "data_hora_fim": "2026-12-25T12:00:00",
        "finalidade": "Reunião no Natal",
        "recurso_id": cenario_agendamento["recurso"].id,
    }

    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["aluno1_headers"],
    )
    data = response.get_json()

    assert response.status_code == 400
    assert "feriados" in data["erro"]


def test_admin_pode_agendar_em_fim_de_semana_e_feriado_201(
    client, admin_token_headers, cenario_agendamento
):
    payload_sabado = {
        "data_hora_inicio": "2026-12-05T10:00:00",
        "data_hora_fim": "2026-12-05T12:00:00",
        "finalidade": "Evento institucional no sábado",
        "recurso_id": cenario_agendamento["recurso"].id,
    }
    resp_sabado = client.post(
        "/api/agendamentos", json=payload_sabado, headers=admin_token_headers
    )
    assert resp_sabado.status_code == 201

    payload_feriado = {
        "data_hora_inicio": "2026-12-25T14:00:00",
        "data_hora_fim": "2026-12-25T16:00:00",
        "finalidade": "Manutenção programada no feriado",
        "recurso_id": cenario_agendamento["recurso"].id,
    }
    resp_feriado = client.post(
        "/api/agendamentos", json=payload_feriado, headers=admin_token_headers
    )
    assert resp_feriado.status_code == 201


def test_horario_quebrado_nao_inteiro_retorna_400(client, cenario_agendamento):
    payload = {
        "data_hora_inicio": "2026-12-01T14:30:00",
        "data_hora_fim": "2026-12-01T16:00:00",
        "finalidade": "Horário inválido",
        "recurso_id": cenario_agendamento["recurso"].id,
    }

    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["aluno1_headers"],
    )
    assert response.status_code == 400


def test_data_fim_anterior_ao_inicio_retorna_400(client, cenario_agendamento):
    payload = {
        "data_hora_inicio": "2026-12-01T16:00:00",
        "data_hora_fim": "2026-12-01T14:00:00",
        "finalidade": "Intervalo invertido",
        "recurso_id": cenario_agendamento["recurso"].id,
    }

    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["aluno1_headers"],
    )
    assert response.status_code == 400


def test_aluno_nao_pode_reservar_para_terceiro_403(client, cenario_agendamento):
    payload = {
        "data_hora_inicio": "2026-12-01T10:00:00",
        "data_hora_fim": "2026-12-01T12:00:00",
        "finalidade": "Tentativa em nome de outro",
        "recurso_id": cenario_agendamento["recurso"].id,
        "usuario_id": cenario_agendamento["aluno2"].id,
    }

    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["aluno1_headers"],
    )
    assert response.status_code == 403


def test_aluno_nao_pode_definir_status_manual_403(client, cenario_agendamento):
    payload = {
        "data_hora_inicio": "2026-12-01T10:00:00",
        "data_hora_fim": "2026-12-01T12:00:00",
        "finalidade": "Tentativa de autoaprovação",
        "recurso_id": cenario_agendamento["recurso"].id,
        "status_id": cenario_agendamento["status"]["Confirmado"].id,
    }

    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["aluno1_headers"],
    )
    assert response.status_code == 403


# ==========================================
# CONFLITOS E PRIORIDADE DOCENTE
# ==========================================

def test_conflito_com_agendamento_confirmado_bloqueia_professor_409(
    client, db_session, cenario_agendamento
):
    ag_confirmado = Agendamento(
        data_hora_inicio=datetime(2026, 12, 2, 14, 0, 0),
        data_hora_fim=datetime(2026, 12, 2, 16, 0, 0),
        finalidade="Reserva já aprovada",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["aluno1"].id,
        status_id=cenario_agendamento["status"]["Confirmado"].id,
    )
    db_session.add(ag_confirmado)
    db_session.commit()

    payload = {
        "data_hora_inicio": "2026-12-02T15:00:00",
        "data_hora_fim": "2026-12-02T17:00:00",
        "finalidade": "Tentativa de sobreposição",
        "recurso_id": cenario_agendamento["recurso"].id,
    }

    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["prof1_headers"],
    )
    assert response.status_code == 409


def test_aluno_conflitando_com_pendente_de_outro_aluno_409(
    client, db_session, cenario_agendamento
):
    ag_pendente = Agendamento(
        data_hora_inicio=datetime(2026, 12, 3, 10, 0, 0),
        data_hora_fim=datetime(2026, 12, 3, 12, 0, 0),
        finalidade="Reserva pendente aluno 1",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["aluno1"].id,
        status_id=cenario_agendamento["status"]["Pendente"].id,
    )
    db_session.add(ag_pendente)
    db_session.commit()

    payload = {
        "data_hora_inicio": "2026-12-03T11:00:00",
        "data_hora_fim": "2026-12-03T13:00:00",
        "finalidade": "Aluno 2 tentando mesmo horário",
        "recurso_id": cenario_agendamento["recurso"].id,
    }

    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["aluno2_headers"],
    )
    assert response.status_code == 409


def test_professor_tem_prioridade_sobre_pendente_de_aluno(
    client, db_session, cenario_agendamento
):
    ag_aluno = Agendamento(
        data_hora_inicio=datetime(2026, 12, 4, 19, 0, 0),
        data_hora_fim=datetime(2026, 12, 4, 21, 0, 0),
        finalidade="Estudo aluno",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["aluno1"].id,
        status_id=cenario_agendamento["status"]["Pendente"].id,
    )
    db_session.add(ag_aluno)
    db_session.commit()

    payload = {
        "data_hora_inicio": "2026-12-04T19:00:00",
        "data_hora_fim": "2026-12-04T21:00:00",
        "finalidade": "Aula prática de Sistemas",
        "recurso_id": cenario_agendamento["recurso"].id,
    }

    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["prof1_headers"],
    )
    data = response.get_json()

    assert response.status_code == 201
    assert "aviso" in data
    assert ag_aluno.id in data["agendamentos_substituidos_ids"]

    db_session.refresh(ag_aluno)
    assert ag_aluno.status_id == cenario_agendamento["status"]["Rejeitado"].id


def test_professor_nao_sobrescreve_pendente_de_outro_professor_409(
    client, db_session, cenario_agendamento
):
    ag_prof1 = Agendamento(
        data_hora_inicio=datetime(2026, 12, 14, 19, 0, 0),
        data_hora_fim=datetime(2026, 12, 14, 21, 0, 0),
        finalidade="Aula prof 1",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["prof1"].id,
        status_id=cenario_agendamento["status"]["Pendente"].id,
    )
    db_session.add(ag_prof1)
    db_session.commit()

    payload = {
        "data_hora_inicio": "2026-12-14T19:00:00",
        "data_hora_fim": "2026-12-14T21:00:00",
        "finalidade": "Aula prof 2",
        "recurso_id": cenario_agendamento["recurso"].id,
    }

    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["prof2_headers"],
    )
    assert response.status_code == 409


def test_agendamentos_colados_nao_geram_conflito_201(client, db_session, cenario_agendamento):
    ag_anterior = Agendamento(
        data_hora_inicio=datetime(2026, 12, 15, 14, 0, 0),
        data_hora_fim=datetime(2026, 12, 15, 16, 0, 0),
        finalidade="Aula anterior",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["prof1"].id,
        status_id=cenario_agendamento["status"]["Confirmado"].id,
    )
    db_session.add(ag_anterior)
    db_session.commit()

    payload = {
        "data_hora_inicio": "2026-12-15T16:00:00",
        "data_hora_fim": "2026-12-15T18:00:00",
        "finalidade": "Aula imediatamente seguinte",
        "recurso_id": cenario_agendamento["recurso"].id,
    }
    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["aluno1_headers"],
    )
    assert response.status_code == 201


def test_horario_com_reserva_cancelada_fica_livre_201(client, db_session, cenario_agendamento):
    ag_cancelado = Agendamento(
        data_hora_inicio=datetime(2026, 12, 16, 10, 0, 0),
        data_hora_fim=datetime(2026, 12, 16, 12, 0, 0),
        finalidade="Reserva cancelada",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["aluno1"].id,
        status_id=cenario_agendamento["status"]["Cancelado"].id,
    )
    db_session.add(ag_cancelado)
    db_session.commit()

    payload = {
        "data_hora_inicio": "2026-12-16T10:00:00",
        "data_hora_fim": "2026-12-16T12:00:00",
        "finalidade": "Nova reserva no horário livre",
        "recurso_id": cenario_agendamento["recurso"].id,
    }
    response = client.post(
        "/api/agendamentos",
        json=payload,
        headers=cenario_agendamento["aluno2_headers"],
    )
    assert response.status_code == 201
    

# ==========================================
# LEITURA E FILTROS (GET)
# ==========================================

def test_listar_agendamentos_com_filtros_200(client, db_session, cenario_agendamento):
    ag1 = Agendamento(
        data_hora_inicio=datetime(2026, 12, 6, 8, 0, 0),
        data_hora_fim=datetime(2026, 12, 6, 10, 0, 0),
        finalidade="Reserva A",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["aluno1"].id,
        status_id=cenario_agendamento["status"]["Pendente"].id,
    )
    ag2 = Agendamento(
        data_hora_inicio=datetime(2026, 12, 6, 14, 0, 0),
        data_hora_fim=datetime(2026, 12, 6, 16, 0, 0),
        finalidade="Reserva B",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["prof1"].id,
        status_id=cenario_agendamento["status"]["Confirmado"].id,
    )
    db_session.add_all([ag1, ag2])
    db_session.commit()

    response = client.get(
        f"/api/agendamentos?usuario_id={cenario_agendamento['prof1'].id}",
        headers=cenario_agendamento["aluno1_headers"],
    )
    data = response.get_json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["finalidade"] == "Reserva B"


def test_buscar_agendamento_por_id_sucesso_e_404(client, db_session, cenario_agendamento):
    ag = Agendamento(
        data_hora_inicio=datetime(2026, 12, 7, 9, 0, 0),
        data_hora_fim=datetime(2026, 12, 7, 11, 0, 0),
        finalidade="Monitoria",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["aluno1"].id,
        status_id=cenario_agendamento["status"]["Pendente"].id,
    )
    db_session.add(ag)
    db_session.commit()

    resp_ok = client.get(
        f"/api/agendamentos/{ag.id}",
        headers=cenario_agendamento["aluno1_headers"],
    )
    assert resp_ok.status_code == 200
    assert resp_ok.get_json()["id"] == ag.id

    resp_404 = client.get(
        "/api/agendamentos/99999",
        headers=cenario_agendamento["aluno1_headers"],
    )
    assert resp_404.status_code == 404


# ==========================================
# ATUALIZAÇÃO (PUT / PATCH) E PERMISSÕES
# ==========================================

def test_admin_aprova_agendamento_via_patch(
    client, admin_token_headers, db_session, cenario_agendamento
):
    ag = Agendamento(
        data_hora_inicio=datetime(2026, 12, 8, 14, 0, 0),
        data_hora_fim=datetime(2026, 12, 8, 16, 0, 0),
        finalidade="Aguardando aprovação",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["aluno1"].id,
        status_id=cenario_agendamento["status"]["Pendente"].id,
    )
    db_session.add(ag)
    db_session.commit()

    response = client.patch(
        f"/api/agendamentos/{ag.id}",
        json={"status_id": cenario_agendamento["status"]["Confirmado"].id},
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    assert response.get_json()["agendamento"]["status_id"] == cenario_agendamento["status"]["Confirmado"].id


def test_aluno_pode_cancelar_proprio_agendamento_mas_nao_aprovar(
    client, db_session, cenario_agendamento
):
    ag = Agendamento(
        data_hora_inicio=datetime(2026, 12, 9, 14, 0, 0),
        data_hora_fim=datetime(2026, 12, 9, 16, 0, 0),
        finalidade="Reserva do aluno",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["aluno1"].id,
        status_id=cenario_agendamento["status"]["Pendente"].id,
    )
    db_session.add(ag)
    db_session.commit()

    # Tentar aprovar -> 403
    resp_aprovar = client.patch(
        f"/api/agendamentos/{ag.id}",
        json={"status_id": cenario_agendamento["status"]["Confirmado"].id},
        headers=cenario_agendamento["aluno1_headers"],
    )
    assert resp_aprovar.status_code == 403

    # Cancelar -> 200
    resp_cancelar = client.patch(
        f"/api/agendamentos/{ag.id}",
        json={"status_id": cenario_agendamento["status"]["Cancelado"].id},
        headers=cenario_agendamento["aluno1_headers"],
    )
    assert resp_cancelar.status_code == 200
    assert resp_cancelar.get_json()["agendamento"]["status_id"] == cenario_agendamento["status"]["Cancelado"].id


def test_outro_usuario_nao_pode_editar_agendamento_403(
    client, db_session, cenario_agendamento
):
    ag = Agendamento(
        data_hora_inicio=datetime(2026, 12, 10, 14, 0, 0),
        data_hora_fim=datetime(2026, 12, 10, 16, 0, 0),
        finalidade="Reserva aluno 1",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["aluno1"].id,
        status_id=cenario_agendamento["status"]["Pendente"].id,
    )
    db_session.add(ag)
    db_session.commit()

    response = client.patch(
        f"/api/agendamentos/{ag.id}",
        json={"finalidade": "Invasão"},
        headers=cenario_agendamento["aluno2_headers"],
    )
    assert response.status_code == 403


def test_put_agendamento_pelo_solicitante_sucesso(client, db_session, cenario_agendamento):
    ag = Agendamento(
        data_hora_inicio=datetime(2026, 12, 11, 14, 0, 0),
        data_hora_fim=datetime(2026, 12, 11, 16, 0, 0),
        finalidade="Original",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["aluno1"].id,
        status_id=cenario_agendamento["status"]["Pendente"].id,
    )
    db_session.add(ag)
    db_session.commit()

    payload = {
        "data_hora_inicio": "2026-12-11T15:00:00",
        "data_hora_fim": "2026-12-11T17:00:00",
        "finalidade": "Remarcada via PUT",
        "recurso_id": cenario_agendamento["recurso"].id,
    }
    response = client.put(
        f"/api/agendamentos/{ag.id}",
        json=payload,
        headers=cenario_agendamento["aluno1_headers"],
    )
    assert response.status_code == 200
    assert response.get_json()["agendamento"]["finalidade"] == "Remarcada via PUT"


# ==========================================
# EXCLUSÃO (DELETE)
# ==========================================

def test_outro_usuario_nao_pode_deletar_agendamento_403(
    client, db_session, cenario_agendamento
):
    ag = Agendamento(
        data_hora_inicio=datetime(2026, 12, 12, 10, 0, 0),
        data_hora_fim=datetime(2026, 12, 12, 12, 0, 0),
        finalidade="Reserva protegida",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["aluno1"].id,
        status_id=cenario_agendamento["status"]["Pendente"].id,
    )
    db_session.add(ag)
    db_session.commit()

    response = client.delete(
        f"/api/agendamentos/{ag.id}",
        headers=cenario_agendamento["aluno2_headers"],
    )
    assert response.status_code == 403


def test_solicitante_deleta_proprio_agendamento_200(client, db_session, cenario_agendamento):
    ag = Agendamento(
        data_hora_inicio=datetime(2026, 12, 13, 10, 0, 0),
        data_hora_fim=datetime(2026, 12, 13, 12, 0, 0),
        finalidade="Reserva para deletar",
        recurso_id=cenario_agendamento["recurso"].id,
        usuario_id=cenario_agendamento["aluno1"].id,
        status_id=cenario_agendamento["status"]["Pendente"].id,
    )
    db_session.add(ag)
    db_session.commit()

    response = client.delete(
        f"/api/agendamentos/{ag.id}",
        headers=cenario_agendamento["aluno1_headers"],
    )
    assert response.status_code == 200


def test_deletar_agendamento_inexistente_404(client, admin_token_headers):
    response = client.delete("/api/agendamentos/99999", headers=admin_token_headers)
    assert response.status_code == 404