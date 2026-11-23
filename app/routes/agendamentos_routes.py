import os
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from loguru import logger
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt
from app.models import db, Agendamento, Recurso, Usuario, StatusAgendamento
from app.schemas.agendamento_schema import AgendamentoSchema

agendamentos_bp = Blueprint('agendamentos', __name__)

agendamento_schema = AgendamentoSchema()
agendamentos_schema = AgendamentoSchema(many=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HORA_ABERTURA = 7
HORA_FECHAMENTO = 22
STATUS_ATIVOS = ('Pendente', 'Confirmado')


def _normalizar_naive(dt):
    """Remove tzinfo para compatibilidade com colunas TIMESTAMP WITHOUT TIME ZONE."""
    return dt.replace(tzinfo=None) if dt and dt.tzinfo is not None else dt


def _validar_horario_funcionamento(inicio, fim, is_admin):
    """Usuários comuns só podem reservar no mesmo dia, entre 07:00 e 22:00."""
    if is_admin:
        return None
    if inicio.date() != fim.date() or inicio.hour < HORA_ABERTURA or fim.hour > HORA_FECHAMENTO:
        return (
            f"Usuários comuns só podem agendar no mesmo dia, entre "
            f"{HORA_ABERTURA:02d}:00 e {HORA_FECHAMENTO:02d}:00. "
            f"Para horários especiais, solicite a um administrador."
        )
    return None


def _buscar_conflitos(recurso_id, inicio, fim, ignorar_id=None):
    """Busca agendamentos ativos (Pendente ou Confirmado) que se sobrepõem ao intervalo."""
    query = (
        db.select(Agendamento)
        .join(StatusAgendamento, Agendamento.status_id == StatusAgendamento.id)
        .where(
            Agendamento.recurso_id == recurso_id,
            StatusAgendamento.nome.in_(STATUS_ATIVOS),
            Agendamento.data_hora_inicio < fim,
            Agendamento.data_hora_fim > inicio,
        )
    )
    if ignorar_id is not None:
        query = query.where(Agendamento.id != ignorar_id)

    return db.session.scalars(query).all()


def _resolver_conflitos(conflitos, perfis_solicitante):
    """
    Aplica a regra de conflito e prioridade docente:
    - Conflito com 'Confirmado': bloqueia sempre (409).
    - Conflito com 'Pendente' de aluno/comunidade: professor ou admin tem prioridade
      e a reserva pendente é automaticamente movida para 'Rejeitado'.
    - Demais casos: bloqueia (409).
    """
    if not conflitos:
        return True, [], None

    if any(ag.status.nome == 'Confirmado' for ag in conflitos):
        return False, [], "Já existe um agendamento confirmado para este recurso no horário solicitado."

    tem_prioridade = 'professor' in perfis_solicitante or 'admin' in perfis_solicitante
    if not tem_prioridade:
        return False, [], "Já existe um agendamento pendente para este recurso no horário solicitado."

    for ag in conflitos:
        perfis_dono = [p.nome for p in ag.solicitante.perfis]
        if 'admin' in perfis_dono or 'professor' in perfis_dono:
            return False, [], "Já existe um agendamento pendente de um professor ou administrador neste horário."

    status_rejeitado = db.session.scalar(
        db.select(StatusAgendamento).filter_by(nome='Rejeitado')
    )
    if not status_rejeitado:
        return False, [], "Conflito detectado e status 'Rejeitado' não encontrado para aplicar prioridade."

    for ag in conflitos:
        ag.status_id = status_rejeitado.id

    return True, conflitos, None


def _logar_sobrescritas(substituidos, usuario_logado_id):
    """Registra em log de auditoria cada agendamento pendente substituído por prioridade."""
    for ag in substituidos:
        logger.warning(
            f"[AUDITORIA] Prioridade aplicada pelo usuário ID {usuario_logado_id}: "
            f"Agendamento ID {ag.id} (Solicitante ID {ag.usuario_id}, Recurso ID {ag.recurso_id}) "
            f"alterado de 'Pendente' para 'Rejeitado'."
        )


def _buscar_participantes(participantes_ids):
    """Valida e retorna a lista de objetos Usuario para os IDs informados."""
    if not participantes_ids:
        return [], None
    ids_unicos = list(set(participantes_ids))
    usuarios = db.session.scalars(
        db.select(Usuario).where(Usuario.id.in_(ids_unicos))
    ).all()
    if len(usuarios) != len(ids_unicos):
        return None, "Um ou mais participantes informados não foram encontrados."
    return usuarios, None


@agendamentos_bp.route('/agendamentos', methods=['POST'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'agendamentos', 'post_agendamento.yml'))
@jwt_required()
def criar_agendamento():
    """
    Cria um novo agendamento de recurso.
    Autorização: Qualquer usuário autenticado.
    """
    claims = get_jwt()
    perfis = claims.get('perfis', [])
    is_admin = 'admin' in perfis
    usuario_logado_id = int(claims.get('sub'))

    json_data = request.get_json()
    if not json_data:
        return jsonify({"erro": "Corpo da requisição JSON é obrigatório."}), 400

    try:
        dados = agendamento_schema.load(json_data)
    except ValidationError as err:
        logger.warning(f"Dados inválidos ao criar agendamento: {err.messages}")
        return jsonify({"erro": "Dados inválidos", "detalhes": err.messages}), 400

    inicio = _normalizar_naive(dados['data_hora_inicio'])
    fim = _normalizar_naive(dados['data_hora_fim'])

    # Regra 1: Horário de funcionamento (07h-22h para comuns; livre para admin)
    erro_horario = _validar_horario_funcionamento(inicio, fim, is_admin)
    if erro_horario:
        return jsonify({"erro": erro_horario}), 400

    # Regra 2: Quem é o solicitante da reserva
    usuario_id_alvo = dados.get('usuario_id')
    if usuario_id_alvo is not None and usuario_id_alvo != usuario_logado_id:
        if not is_admin:
            logger.warning(f"Usuário {usuario_logado_id} tentou agendar em nome do usuário {usuario_id_alvo}.")
            return jsonify({"erro": "Acesso negado. Apenas administradores podem agendar em nome de outro usuário."}), 403
        if not db.session.get(Usuario, usuario_id_alvo):
            return jsonify({"erro": "Usuário solicitante não encontrado."}), 404
    else:
        usuario_id_alvo = usuario_logado_id

    # Regra 3: Verificar se o recurso existe
    recurso = db.session.get(Recurso, dados['recurso_id'])
    if not recurso:
        return jsonify({"erro": "Recurso não encontrado."}), 404

    # Regra 4: Definição do status inicial
    status_id_informado = dados.get('status_id')
    if status_id_informado is not None:
        if not is_admin:
            return jsonify({"erro": "Acesso negado. Apenas administradores podem definir o status manualmente."}), 403
        status_alvo = db.session.get(StatusAgendamento, status_id_informado)
        if not status_alvo:
            return jsonify({"erro": "Status de agendamento não encontrado."}), 404
    else:
        nome_status_padrao = 'Confirmado' if is_admin else 'Pendente'
        status_alvo = db.session.scalar(
            db.select(StatusAgendamento).filter_by(nome=nome_status_padrao)
        )
        if not status_alvo:
            return jsonify({"erro": f"Status padrão '{nome_status_padrao}' não cadastrado no sistema."}), 500

    # Regra 5: Participantes (N:N)
    participantes, erro_part = _buscar_participantes(dados.get('participantes_ids', []))
    if erro_part:
        return jsonify({"erro": erro_part}), 404

    try:
        # Regra 6: Conflito de horários e prioridade docente
        substituidos = []
        if status_alvo.nome in STATUS_ATIVOS:
            conflitos = _buscar_conflitos(recurso.id, inicio, fim)
            ok, substituidos, erro_conflito = _resolver_conflitos(conflitos, perfis)
            if not ok:
                logger.warning(f"Conflito de horário no recurso {recurso.id}: {erro_conflito}")
                return jsonify({"erro": erro_conflito}), 409

        novo_agendamento = Agendamento(
            data_hora_inicio=inicio,
            data_hora_fim=fim,
            finalidade=dados['finalidade'],
            recurso_id=recurso.id,
            usuario_id=usuario_id_alvo,
            status_id=status_alvo.id,
        )
        if participantes:
            novo_agendamento.participantes.extend(participantes)

        db.session.add(novo_agendamento)
        db.session.commit()

        logger.info(
            f"Agendamento ID {novo_agendamento.id} criado para recurso {recurso.id} "
            f"(Solicitante: {usuario_id_alvo} | Criado por: {usuario_logado_id})."
        )

        resposta = {
            "mensagem": "Agendamento criado com sucesso!",
            "agendamento": agendamento_schema.dump(novo_agendamento)
        }
        if substituidos:
            ids_sub = [ag.id for ag in substituidos]
            _logar_sobrescritas(substituidos, usuario_logado_id)
            resposta["aviso"] = "Solicitações pendentes de alunos neste horário foram substituídas por prioridade."
            resposta["agendamentos_substituidos_ids"] = ids_sub

        return jsonify(resposta), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico ao criar agendamento: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@agendamentos_bp.route('/agendamentos', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'agendamentos', 'get_agendamentos.yml'))
@jwt_required()
def listar_agendamentos():
    """
    Lista agendamentos com filtros opcionais por recurso_id, usuario_id e status_id.
    Autorização: Qualquer usuário autenticado.
    """
    try:
        query = db.select(Agendamento)

        recurso_id = request.args.get('recurso_id', type=int)
        usuario_id = request.args.get('usuario_id', type=int)
        status_id = request.args.get('status_id', type=int)

        if recurso_id is not None:
            query = query.where(Agendamento.recurso_id == recurso_id)
        if usuario_id is not None:
            query = query.where(Agendamento.usuario_id == usuario_id)
        if status_id is not None:
            query = query.where(Agendamento.status_id == status_id)

        agendamentos = db.session.scalars(query).all()
        logger.info(f"Listagem de agendamentos solicitada. Total retornado: {len(agendamentos)}")
        return jsonify(agendamentos_schema.dump(agendamentos)), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao listar agendamentos: {str(e)}")
        return jsonify({"erro": "Erro ao buscar agendamentos.", "detalhes": str(e)}), 500


@agendamentos_bp.route('/agendamentos/<int:id>', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'agendamentos', 'get_agendamento_by_id.yml'))
@jwt_required()
def buscar_agendamento_por_id(id):
    """
    Busca um agendamento específico pelo ID.
    Autorização: Qualquer usuário autenticado.
    """
    try:
        agendamento = db.session.get(Agendamento, id)
        if not agendamento:
            logger.warning(f"Busca por agendamento inexistente. ID: {id}")
            return jsonify({"erro": "Agendamento não encontrado."}), 404

        return jsonify(agendamento_schema.dump(agendamento)), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao buscar agendamento ID {id}: {str(e)}")
        return jsonify({"erro": "Erro ao buscar agendamento.", "detalhes": str(e)}), 500


@agendamentos_bp.route('/agendamentos/<int:id>', methods=['PUT'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'agendamentos', 'put_agendamento.yml'))
@jwt_required()
def atualizar_agendamento_total(id):
    """
    Atualiza todos os campos de um agendamento existente.
    Autorização: Administrador ou próprio solicitante.
    """
    claims = get_jwt()
    perfis = claims.get('perfis', [])
    is_admin = 'admin' in perfis
    usuario_logado_id = int(claims.get('sub'))

    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({"erro": "Agendamento não encontrado."}), 404

    if not is_admin and agendamento.usuario_id != usuario_logado_id:
        logger.warning(f"Tentativa negada de PUT no agendamento {id} pelo usuário {usuario_logado_id}.")
        return jsonify({"erro": "Acesso negado. Apenas o solicitante ou um administrador pode editar este agendamento."}), 403

    json_data = request.get_json()
    if not json_data:
        return jsonify({"erro": "Corpo da requisição JSON é obrigatório."}), 400

    try:
        dados = agendamento_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"erro": "Dados inválidos", "detalhes": err.messages}), 400

    inicio = _normalizar_naive(dados['data_hora_inicio'])
    fim = _normalizar_naive(dados['data_hora_fim'])

    erro_horario = _validar_horario_funcionamento(inicio, fim, is_admin)
    if erro_horario:
        return jsonify({"erro": erro_horario}), 400

    recurso = db.session.get(Recurso, dados['recurso_id'])
    if not recurso:
        return jsonify({"erro": "Recurso não encontrado."}), 404

    # Validação de troca de status
    status_alvo = agendamento.status
    if dados.get('status_id') is not None and dados['status_id'] != agendamento.status_id:
        status_alvo = db.session.get(StatusAgendamento, dados['status_id'])
        if not status_alvo:
            return jsonify({"erro": "Status de agendamento não encontrado."}), 404
        if not is_admin and status_alvo.nome != 'Cancelado':
            return jsonify({"erro": "Acesso negado. Usuários comuns só podem alterar o status para 'Cancelado'."}), 403

    # Validação de troca de solicitante
    novo_usuario_id = agendamento.usuario_id
    if dados.get('usuario_id') is not None and dados['usuario_id'] != agendamento.usuario_id:
        if not is_admin:
            return jsonify({"erro": "Acesso negado. Apenas administradores podem alterar o solicitante."}), 403
        if not db.session.get(Usuario, dados['usuario_id']):
            return jsonify({"erro": "Usuário solicitante não encontrado."}), 404
        novo_usuario_id = dados['usuario_id']

    participantes, erro_part = _buscar_participantes(dados.get('participantes_ids', []))
    if erro_part:
        return jsonify({"erro": erro_part}), 404

    try:
        substituidos = []
        if status_alvo.nome in STATUS_ATIVOS:
            conflitos = _buscar_conflitos(recurso.id, inicio, fim, ignorar_id=agendamento.id)
            ok, substituidos, erro_conflito = _resolver_conflitos(conflitos, perfis)
            if not ok:
                return jsonify({"erro": erro_conflito}), 409

        agendamento.data_hora_inicio = inicio
        agendamento.data_hora_fim = fim
        agendamento.finalidade = dados['finalidade']
        agendamento.recurso_id = recurso.id
        agendamento.usuario_id = novo_usuario_id
        agendamento.status_id = status_alvo.id
        agendamento.participantes = participantes

        db.session.commit()

        logger.info(f"[AUDITORIA] Agendamento ID {id} atualizado via PUT pelo usuário ID {usuario_logado_id}.")
        if substituidos:
            _logar_sobrescritas(substituidos, usuario_logado_id)

        return jsonify({
            "mensagem": "Agendamento atualizado com sucesso!",
            "agendamento": agendamento_schema.dump(agendamento)
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico no PUT do agendamento {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@agendamentos_bp.route('/agendamentos/<int:id>', methods=['PATCH'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'agendamentos', 'patch_agendamento.yml'))
@jwt_required()
def atualizar_agendamento_parcial(id):
    """
    Atualiza parcialmente um agendamento (ideal para aprovar, rejeitar ou cancelar).
    Autorização: Administrador ou próprio solicitante.
    """
    claims = get_jwt()
    perfis = claims.get('perfis', [])
    is_admin = 'admin' in perfis
    usuario_logado_id = int(claims.get('sub'))

    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({"erro": "Agendamento não encontrado."}), 404

    if not is_admin and agendamento.usuario_id != usuario_logado_id:
        logger.warning(f"Tentativa negada de PATCH no agendamento {id} pelo usuário {usuario_logado_id}.")
        return jsonify({"erro": "Acesso negado. Apenas o solicitante ou um administrador pode editar este agendamento."}), 403

    json_data = request.get_json()
    if not json_data:
        return jsonify({"erro": "Corpo da requisição JSON é obrigatório."}), 400

    try:
        dados = agendamento_schema.load(json_data, partial=True)
    except ValidationError as err:
        return jsonify({"erro": "Dados inválidos", "detalhes": err.messages}), 400

    novo_inicio = _normalizar_naive(dados.get('data_hora_inicio', agendamento.data_hora_inicio))
    novo_fim = _normalizar_naive(dados.get('data_hora_fim', agendamento.data_hora_fim))

    if novo_fim <= novo_inicio:
        return jsonify({
            "erro": "Dados inválidos",
            "detalhes": {"data_hora_fim": ["A data/hora de término deve ser posterior à data/hora de início."]}
        }), 400

    if 'data_hora_inicio' in dados or 'data_hora_fim' in dados:
        erro_horario = _validar_horario_funcionamento(novo_inicio, novo_fim, is_admin)
        if erro_horario:
            return jsonify({"erro": erro_horario}), 400

    novo_recurso_id = agendamento.recurso_id
    if 'recurso_id' in dados:
        if not db.session.get(Recurso, dados['recurso_id']):
            return jsonify({"erro": "Recurso não encontrado."}), 404
        novo_recurso_id = dados['recurso_id']

    status_alvo = agendamento.status
    if 'status_id' in dados and dados['status_id'] is not None:
        status_alvo = db.session.get(StatusAgendamento, dados['status_id'])
        if not status_alvo:
            return jsonify({"erro": "Status de agendamento não encontrado."}), 404
        if not is_admin and status_alvo.nome != 'Cancelado':
            return jsonify({"erro": "Acesso negado. Usuários comuns só podem alterar o status para 'Cancelado'."}), 403

    if 'usuario_id' in dados and dados['usuario_id'] is not None and dados['usuario_id'] != agendamento.usuario_id:
        if not is_admin:
            return jsonify({"erro": "Acesso negado. Apenas administradores podem alterar o solicitante."}), 403
        if not db.session.get(Usuario, dados['usuario_id']):
            return jsonify({"erro": "Usuário solicitante não encontrado."}), 404
        agendamento.usuario_id = dados['usuario_id']

    if 'participantes_ids' in json_data:
        participantes, erro_part = _buscar_participantes(dados.get('participantes_ids', []))
        if erro_part:
            return jsonify({"erro": erro_part}), 404
        agendamento.participantes = participantes

    try:
        substituidos = []
        if status_alvo.nome in STATUS_ATIVOS:
            conflitos = _buscar_conflitos(novo_recurso_id, novo_inicio, novo_fim, ignorar_id=agendamento.id)
            ok, substituidos, erro_conflito = _resolver_conflitos(conflitos, perfis)
            if not ok:
                return jsonify({"erro": erro_conflito}), 409

        agendamento.data_hora_inicio = novo_inicio
        agendamento.data_hora_fim = novo_fim
        agendamento.recurso_id = novo_recurso_id
        agendamento.status_id = status_alvo.id
        if 'finalidade' in dados:
            agendamento.finalidade = dados['finalidade']

        db.session.commit()

        logger.info(f"[AUDITORIA] Agendamento ID {id} atualizado via PATCH pelo usuário ID {usuario_logado_id}.")
        if substituidos:
            _logar_sobrescritas(substituidos, usuario_logado_id)

        return jsonify({
            "mensagem": "Agendamento atualizado parcialmente com sucesso!",
            "agendamento": agendamento_schema.dump(agendamento)
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico no PATCH do agendamento {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@agendamentos_bp.route('/agendamentos/<int:id>', methods=['DELETE'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'agendamentos', 'delete_agendamento.yml'))
@jwt_required()
def deletar_agendamento(id):
    """
    Remove um agendamento do sistema.
    Autorização: Administrador ou próprio solicitante.
    """
    claims = get_jwt()
    is_admin = 'admin' in claims.get('perfis', [])
    usuario_logado_id = int(claims.get('sub'))

    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({"erro": "Agendamento não encontrado."}), 404

    if not is_admin and agendamento.usuario_id != usuario_logado_id:
        logger.warning(f"Tentativa negada de DELETE no agendamento {id} pelo usuário {usuario_logado_id}.")
        return jsonify({"erro": "Acesso negado. Apenas o solicitante ou um administrador pode deletar este agendamento."}), 403

    try:
        db.session.delete(agendamento)
        db.session.commit()
        logger.info(f"[AUDITORIA] Agendamento ID {id} deletado pelo usuário ID {usuario_logado_id}.")
        return jsonify({"mensagem": "Agendamento deletado com sucesso!"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico ao deletar agendamento {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500
    