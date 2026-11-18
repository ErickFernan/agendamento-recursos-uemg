from marshmallow import Schema, fields, validate

class LoginSchema(Schema):
    email = fields.Email(required=True, error_messages={"invalid": "Formato de e-mail inválido."})
    senha = fields.String(required=True, validate=validate.Length(min=6, error="Senha deve ter no mínimo 6 caracteres."))
    