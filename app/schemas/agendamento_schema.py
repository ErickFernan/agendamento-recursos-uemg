from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class ParticipanteResumoSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(dump_only=True)
    email = fields.Email(dump_only=True)


class AgendamentoSchema(Schema):
    id = fields.Int(dump_only=True)
    data_hora_inicio = fields.DateTime(required=True)
    data_hora_fim = fields.DateTime(required=True)
    finalidade = fields.Str(
        required=True,
        validate=validate.Length(
            min=3,
            max=255,
            error="A finalidade deve ter entre 3 e 255 caracteres."
        )
    )

    recurso_id = fields.Int(required=True)
    # Opcional na entrada: apenas Admin pode informar o ID de outro usuário
    usuario_id = fields.Int(load_default=None)
    status_id = fields.Int(load_default=None)

    # Entrada: lista de IDs de usuários convidados (tabela participante_agendamento)
    participantes_ids = fields.List(
        fields.Int(),
        load_only=True,
        load_default=[]
    )

    # Saída: dados resumidos dos participantes já vinculados
    participantes = fields.List(
        fields.Nested(ParticipanteResumoSchema),
        dump_only=True
    )

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates_schema
    def validar_intervalo_datas(self, data, **kwargs):
        inicio = data.get("data_hora_inicio")
        fim = data.get("data_hora_fim")
        erros = {}

        if inicio and (inicio.minute != 0 or inicio.second != 0 or inicio.microsecond != 0):
            erros["data_hora_inicio"] = [
                "O horário de início deve ser uma hora inteira (ex: 14:00:00)."
            ]

        if fim and (fim.minute != 0 or fim.second != 0 or fim.microsecond != 0):
            erros["data_hora_fim"] = [
                "O horário de término deve ser uma hora inteira (ex: 16:00:00)."
            ]

        if inicio and fim:
            if (inicio.tzinfo is None) != (fim.tzinfo is None):
                erros.setdefault("data_hora_fim", []).append(
                    "As datas de início e fim devem usar o mesmo padrão de fuso horário."
                )
            elif fim <= inicio:
                erros.setdefault("data_hora_fim", []).append(
                    "A data/hora de término deve ser posterior à data/hora de início."
                )

        if erros:
            raise ValidationError(erros)