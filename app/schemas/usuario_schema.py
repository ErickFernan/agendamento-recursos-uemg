from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields, validate
from app.models import Usuario

class UsuarioSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Usuario
        load_instance = True
        include_fk = True
        # Excluímos o hash do banco para nunca vazar num GET
        exclude = ("senha_hash",)

    # Validamos se o e-mail tem formato válido (@)
    email = fields.Email(required=True, error_messages={"invalid": "Formato de e-mail inválido."})
    
    # Campo virtual que só existe na hora de RECEBER o JSON (POST/PUT)
    senha = fields.String(
        required=True, 
        load_only=True, 
        validate=validate.Length(min=6, error="A senha deve ter no mínimo 6 caracteres.")
    )
