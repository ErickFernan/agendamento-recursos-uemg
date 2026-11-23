import os
from flask import Blueprint, jsonify
from flasgger import swag_from
from loguru import logger
from flask_jwt_extended import jwt_required
from app.models import db, StatusAgendamento
from app.schemas.status_agendamento_schema import StatusAgendamentoSchema

status_agendamento_bp = Blueprint('status_agendamento', __name__)

status_schema = StatusAgendamentoSchema()
statuses_schema = StatusAgendamentoSchema(many=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@status_agendamento_bp.route('/status-agendamento', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'status_agendamento', 'get_status_agendamento.yml'))
@jwt_required()
def listar_status_agendamento():
    """
    Lista todos os status de agendamento disponíveis.
    Autorização: Qualquer usuário autenticado.
    """
    try:
        status_list = db.session.scalars(db.select(StatusAgendamento)).all()
        resultado = statuses_schema.dump(status_list)
        logger.info(f"Listagem de status de agendamento solicitada. Total retornado: {len(status_list)}")
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao listar status de agendamento: {str(e)}")
        return jsonify({"erro": "Erro ao buscar status de agendamento.", "detalhes": str(e)}), 500


@status_agendamento_bp.route('/status-agendamento/<int:id>', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'status_agendamento', 'get_status_agendamento_by_id.yml'))
@jwt_required()
def buscar_status_agendamento_por_id(id):
    """
    Busca um status de agendamento específico pelo ID.
    Autorização: Qualquer usuário autenticado.
    """
    try:
        status = db.session.get(StatusAgendamento, id)
        if not status:
            logger.warning(f"Busca por status de agendamento inexistente. ID: {id}")
            return jsonify({"erro": "Status de agendamento não encontrado."}), 404

        return jsonify(status_schema.dump(status)), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao buscar status de agendamento ID {id}: {str(e)}")
        return jsonify({"erro": "Erro ao buscar status de agendamento.", "detalhes": str(e)}), 500
    