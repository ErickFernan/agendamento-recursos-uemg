import os
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from loguru import logger
from app.models import db, Unidade
from app.schemas.unidade_schema import UnidadeSchema
from sqlalchemy.exc import IntegrityError

unidades_bp = Blueprint('unidades', __name__)

unidade_schema = UnidadeSchema()
unidades_schema = UnidadeSchema(many=True)

# Descobre o caminho exato da pasta 'app' dinamicamente
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@unidades_bp.route('/unidades', methods=['POST'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'unidades', 'post_unidade.yml'))
def criar_unidade():
    json_data = request.get_json()
    
    erros = unidade_schema.validate(json_data)
    if erros:
        logger.warning(f"Tentativa de criar unidade com dados inválidos: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400
    
    try:
        nova_unidade = Unidade(
            nome=json_data['nome'],
            sigla=json_data['sigla'],
            cidade=json_data['cidade'],
            estado=json_data['estado']
        )
        
        db.session.add(nova_unidade)
        db.session.commit()

        logger.info(f"Unidade '{nova_unidade.nome}' criada com sucesso!")
        
        return jsonify({
            "mensagem": "Unidade criada com sucesso!", 
            "unidade": unidade_schema.dump(nova_unidade)
        }), 201

    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Conflito de integridade ao tentar criar unidade: {json_data.get('nome')}")
        return jsonify({"erro": "Já existe uma unidade com estes dados."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico ao criar unidade: {str(e)}") 
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@unidades_bp.route('/unidades', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'unidades', 'get_unidades.yml'))
def listar_unidades():
    try:
        unidades = Unidade.query.all()
        resultado = unidades_schema.dump(unidades)
        logger.info(f"Listagem de unidades solicitada. Total retornado: {len(unidades)}")
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao listar unidades: {str(e)}")
        return jsonify({"erro": "Erro ao buscar unidades.", "detalhes": str(e)}), 500


@unidades_bp.route('/unidades/<int:id>', methods=['PUT'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'unidades', 'put_unidade.yml'))
def atualizar_unidade_total(id):
    unidade = Unidade.query.get(id)
    if not unidade:
        logger.warning(f"Tentativa de atualização total (PUT) em unidade inexistente. ID: {id}")
        return jsonify({"erro": "Unidade não encontrada."}), 404

    json_data = request.get_json()
    
    erros = unidade_schema.validate(json_data)
    if erros:
        logger.warning(f"Dados inválidos recebidos no PUT para a unidade {id}: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    try:
        nome_antigo = unidade.nome
        unidade.nome = json_data['nome']
        unidade.sigla = json_data['sigla']
        unidade.cidade = json_data['cidade']
        unidade.estado = json_data['estado']
        
        db.session.commit()
        logger.info(f"Unidade ID {id} atualizada com sucesso via PUT. ('{nome_antigo}' -> '{unidade.nome}')")
        return jsonify({"mensagem": "Unidade atualizada com sucesso!", "unidade": unidade_schema.dump(unidade)}), 200
    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Conflito de integridade ao tentar atualizar (PUT) a unidade {id}")
        return jsonify({"erro": "Erro de integridade no banco de dados."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico no PUT da unidade {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@unidades_bp.route('/unidades/<int:id>', methods=['PATCH'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'unidades', 'patch_unidade.yml'))
def atualizar_unidade_parcial(id):
    unidade = Unidade.query.get(id)
    if not unidade:
        logger.warning(f"Tentativa de atualização parcial (PATCH) em unidade inexistente. ID: {id}")
        return jsonify({"erro": "Unidade não encontrada."}), 404

    json_data = request.get_json()
    
    erros = unidade_schema.validate(json_data, partial=True)
    if erros:
        logger.warning(f"Dados inválidos recebidos no PATCH para a unidade {id}: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    try:
        if 'nome' in json_data: unidade.nome = json_data['nome']
        if 'sigla' in json_data: unidade.sigla = json_data['sigla']
        if 'cidade' in json_data: unidade.cidade = json_data['cidade']
        if 'estado' in json_data: unidade.estado = json_data['estado']
        
        db.session.commit()
        logger.info(f"Unidade ID {id} atualizada parcialmente com sucesso via PATCH.")
        return jsonify({"mensagem": "Unidade atualizada parcialmente com sucesso!", "unidade": unidade_schema.dump(unidade)}), 200
    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Conflito de integridade ao tentar atualizar parcialmente (PATCH) a unidade {id}")
        return jsonify({"erro": "Erro de integridade no banco de dados."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico no PATCH da unidade {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@unidades_bp.route('/unidades/<int:id>', methods=['DELETE'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'unidades', 'delete_unidade.yml'))
def deletar_unidade(id):
    unidade = Unidade.query.get(id)
    if not unidade:
        logger.warning(f"Tentativa de exclusão (DELETE) em unidade inexistente. ID: {id}")
        return jsonify({"erro": "Unidade não encontrada."}), 404

    try:
        nome_deletado = unidade.nome
        db.session.delete(unidade)
        db.session.commit()
        logger.info(f"Unidade '{nome_deletado}' (ID {id}) deletada com sucesso.")
        return jsonify({"mensagem": "Unidade deletada com sucesso!"}), 200
    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Tentativa de deletar unidade com dependentes barrada pelo banco. ID: {id} ('{unidade.nome}')")
        return jsonify({"erro": "Não é possível deletar esta unidade pois existem recursos ou usuários vinculados a ela."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico ao tentar deletar a unidade {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500