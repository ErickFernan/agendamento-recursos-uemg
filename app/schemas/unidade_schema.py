from marshmallow import Schema, fields, validate

class UnidadeSchema(Schema):
    id = fields.Int(dump_only=True) # dump_only significa que só sai na resposta, o usuário não envia o ID
    
    nome = fields.Str(
        required=True, 
        validate=validate.Length(min=3, max=150), 
        error_messages={"required": "O nome da unidade é obrigatório."}
    )
    
    sigla = fields.Str(
        required=True, 
        validate=validate.Length(min=2, max=20),
        error_messages={"required": "A sigla da unidade é obrigatória."}
    )
    
    cidade = fields.Str(
        required=True, 
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "A cidade é obrigatória."}
    )
    
    estado = fields.Str(
        required=True, 
        validate=validate.Length(equal=2), # O estado deve ter exatamente 2 letras (ex: MG)
        error_messages={"required": "O estado (UF) é obrigatório."}
    )