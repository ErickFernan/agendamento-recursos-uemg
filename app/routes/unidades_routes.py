import os
from flask import Blueprint, request, jsonify
from flasgger import swag_from
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
        
        return jsonify({
            "mensagem": "Unidade criada com sucesso!", 
            "unidade": unidade_schema.dump(nova_unidade)
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"erro": "Já existe uma unidade com estes dados."}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@unidades_bp.route('/unidades', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'unidades', 'get_unidades.yml'))
def listar_unidades():
    try:
        unidades = Unidade.query.all()
        resultado = unidades_schema.dump(unidades)
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"erro": "Erro ao buscar unidades.", "detalhes": str(e)}), 500


@unidades_bp.route('/unidades/<int:id>', methods=['PUT'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'unidades', 'put_unidade.yml'))
def atualizar_unidade_total(id):
    unidade = Unidade.query.get(id)
    if not unidade:
        return jsonify({"erro": "Unidade não encontrada."}), 404

    json_data = request.get_json()
    
    erros = unidade_schema.validate(json_data)
    if erros:
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    try:
        unidade.nome = json_data['nome']
        unidade.sigla = json_data['sigla']
        unidade.cidade = json_data['cidade']
        unidade.estado = json_data['estado']
        
        db.session.commit()
        return jsonify({"mensagem": "Unidade atualizada com sucesso!", "unidade": unidade_schema.dump(unidade)}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"erro": "Erro de integridade no banco de dados."}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@unidades_bp.route('/unidades/<int:id>', methods=['PATCH'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'unidades', 'patch_unidade.yml'))
def atualizar_unidade_parcial(id):
    unidade = Unidade.query.get(id)
    if not unidade:
        return jsonify({"erro": "Unidade não encontrada."}), 404

    json_data = request.get_json()
    
    erros = unidade_schema.validate(json_data, partial=True)
    if erros:
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    try:
        if 'nome' in json_data: unidade.nome = json_data['nome']
        if 'sigla' in json_data: unidade.sigla = json_data['sigla']
        if 'cidade' in json_data: unidade.cidade = json_data['cidade']
        if 'estado' in json_data: unidade.estado = json_data['estado']
        
        db.session.commit()
        return jsonify({"mensagem": "Unidade atualizada parcialmente com sucesso!", "unidade": unidade_schema.dump(unidade)}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"erro": "Erro de integridade no banco de dados."}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@unidades_bp.route('/unidades/<int:id>', methods=['DELETE'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'unidades', 'delete_unidade.yml'))
def deletar_unidade(id):
    unidade = Unidade.query.get(id)
    if not unidade:
        return jsonify({"erro": "Unidade não encontrada."}), 404

    try:
        db.session.delete(unidade)
        db.session.commit()
        return jsonify({"mensagem": "Unidade deletada com sucesso!"}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"erro": "Não é possível deletar esta unidade pois existem recursos ou usuários vinculados a ela."}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500