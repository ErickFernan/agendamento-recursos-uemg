from marshmallow import Schema, fields


class StatusAgendamentoSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)