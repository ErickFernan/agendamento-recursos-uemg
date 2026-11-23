import os
from flask import Blueprint, jsonify
from flasgger import swag_from
from loguru import logger
from flask_jwt_extended import jwt_required
from app.models import db, Perfil
from app.schemas.perfil_schema import PerfilSchema

perfis_bp = Blueprint('perfis', __name__)

perfil_schema = PerfilSchema()
perfis_schema = PerfilSchema(many=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@perfis_bp.route('/perfis', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'perfis', 'get_perfis.yml'))
@jwt_required()
def listar_perfis():
    """
    Lista todos os perfis de acesso cadastrados.
    Autorização: Qualquer usuário autenticado.
    """
    try:
        perfis = db.session.scalars(db.select(Perfil)).all()
        resultado = perfis_schema.dump(perfis)
        logger.info(f"Listagem de perfis solicitada. Total retornado: {len(perfis)}")
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao listar perfis: {str(e)}")
        return jsonify({"erro": "Erro ao buscar perfis.", "detalhes": str(e)}), 500


@perfis_bp.route('/perfis/<int:id>', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'perfis', 'get_perfil_by_id.yml'))
@jwt_required()
def buscar_perfil_por_id(id):
    """
    Busca um perfil de acesso específico pelo ID.
    Autorização: Qualquer usuário autenticado.
    """
    try:
        perfil = db.session.get(Perfil, id)
        if not perfil:
            logger.warning(f"Busca por perfil inexistente. ID: {id}")
            return jsonify({"erro": "Perfil não encontrado."}), 404

        return jsonify(perfil_schema.dump(perfil)), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao buscar perfil ID {id}: {str(e)}")
        return jsonify({"erro": "Erro ao buscar perfil.", "detalhes": str(e)}), 500
    