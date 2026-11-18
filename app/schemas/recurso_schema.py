from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields, validate
from app.models import Recurso


class RecursoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Recurso
        include_fk = True
        load_instance = True

    id = fields.Int(dump_only=True)
    nome = fields.Str(
        required=True,
        validate=validate.Length(
            min=2,
            max=150,
            error="O nome do recurso deve ter entre 2 e 150 caracteres."
        )
    )
    capacidade = fields.Int(
        required=True,
        validate=validate.Range(
            min=0,
            error="A capacidade deve ser um número inteiro maior ou igual a zero."
        )
    )
    unidade_id = fields.Int(required=True)
    categoria_id = fields.Int(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    