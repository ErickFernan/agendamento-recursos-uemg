from marshmallow import Schema, fields, validate


class CategoriaRecursoSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100, error="O nome deve ter entre 2 e 100 caracteres.")
    )
    descricao = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=255, error="A descrição deve ter no máximo 255 caracteres.")
    )
    