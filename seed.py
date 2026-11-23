from datetime import datetime
from app import create_app, db
from app.models import (
    Perfil,
    StatusAgendamento,
    CategoriaRecurso,
    Unidade,
    Usuario,
    Recurso,
    Agendamento,
)
from werkzeug.security import generate_password_hash
from loguru import logger

app = create_app()


def seed_database():
    with app.app_context():
        logger.info("Iniciando o povoamento (Seed) do banco de dados...")

        # 1. Perfis de Acesso (RBAC)
        perfis_iniciais = ['admin', 'professor', 'aluno', 'comunidade']
        for nome_perfil in perfis_iniciais:
            if not db.session.scalar(db.select(Perfil).filter_by(nome=nome_perfil)):
                db.session.add(Perfil(nome=nome_perfil))
                logger.info(f"Perfil criado: {nome_perfil}")

        # 2. Status de Agendamento
        status_iniciais = ['Pendente', 'Confirmado', 'Cancelado', 'Rejeitado', 'Concluído']
        for nome_status in status_iniciais:
            if not db.session.scalar(db.select(StatusAgendamento).filter_by(nome=nome_status)):
                db.session.add(StatusAgendamento(nome=nome_status))
                logger.info(f"Status criado: {nome_status}")

        # 3. Categorias de Recursos
        categorias_iniciais = [
            {"nome": "Laboratório", "descricao": "Laboratórios de informática, química, física e práticas."},
            {"nome": "Sala de Aula", "descricao": "Salas de aula padrão com projetor e quadro."},
            {"nome": "Auditório", "descricao": "Espaços amplos para palestras, defesas e eventos."},
            {"nome": "Espaço Esportivo", "descricao": "Quadras poliesportivas e áreas de educação física."},
            {"nome": "Equipamento", "descricao": "Projetores móveis, notebooks, caixas de som e periféricos."}
        ]
        for cat in categorias_iniciais:
            if not db.session.scalar(db.select(CategoriaRecurso).filter_by(nome=cat["nome"])):
                db.session.add(CategoriaRecurso(nome=cat["nome"], descricao=cat["descricao"]))
                logger.info(f"Categoria criada: {cat['nome']}")

        # 4. Unidades
        unidades_iniciais = [
            {
                "nome": "Universidade do Estado de Minas Gerais",
                "sigla": "UEMG",
                "cidade": "Carangola",
                "estado": "MG"
            },
            {
                "nome": "UEMG - Unidade Ubá",
                "sigla": "UEMG-UBA",
                "cidade": "Ubá",
                "estado": "MG"
            }
        ]
        for u in unidades_iniciais:
            if not db.session.scalar(db.select(Unidade).filter_by(nome=u["nome"])):
                db.session.add(Unidade(**u))
                logger.info(f"Unidade criada: {u['nome']} ({u['cidade']})")

        # Salva as entidades independentes para gerar os IDs
        db.session.commit()

        # Busca referências salvas
        unidade_carangola = db.session.scalar(
            db.select(Unidade).filter_by(nome="Universidade do Estado de Minas Gerais")
        )
        unidade_uba = db.session.scalar(
            db.select(Unidade).filter_by(nome="UEMG - Unidade Ubá")
        )

        # 5. Usuários (Admin, Professor e Aluno para testar RBAC na apresentação)
        usuarios_iniciais = [
            ("Administrador UEMG", "admin@uemg.br", "AdminSegura123", "admin", unidade_carangola.id),
            ("Professor Sistemas", "professor@uemg.br", "ProfSegura123", "professor", unidade_carangola.id),
            ("Aluno Teste", "aluno@uemg.br", "AlunoSegura123", "aluno", unidade_carangola.id),
        ]
        for nome, email, senha, nome_perfil, unidade_id in usuarios_iniciais:
            if not db.session.scalar(db.select(Usuario).filter_by(email=email)):
                perfil = db.session.scalar(db.select(Perfil).filter_by(nome=nome_perfil))
                novo_usuario = Usuario(
                    nome=nome,
                    email=email,
                    senha_hash=generate_password_hash(senha),
                    unidade_id=unidade_id
                )
                novo_usuario.perfis.append(perfil)
                db.session.add(novo_usuario)
                logger.info(f"Usuário '{nome_perfil}' criado | E-mail: {email} | Senha: {senha}")

        db.session.commit()

        # 6. Recursos
        cat_lab = db.session.scalar(db.select(CategoriaRecurso).filter_by(nome="Laboratório"))
        cat_sala = db.session.scalar(db.select(CategoriaRecurso).filter_by(nome="Sala de Aula"))
        cat_auditorio = db.session.scalar(db.select(CategoriaRecurso).filter_by(nome="Auditório"))
        cat_esporte = db.session.scalar(db.select(CategoriaRecurso).filter_by(nome="Espaço Esportivo"))
        cat_equip = db.session.scalar(db.select(CategoriaRecurso).filter_by(nome="Equipamento"))

        recursos_iniciais = [
            {"nome": "Laboratório de Informática 01", "capacidade": 30, "unidade_id": unidade_carangola.id, "categoria_id": cat_lab.id},
            {"nome": "Auditório Principal", "capacidade": 120, "unidade_id": unidade_carangola.id, "categoria_id": cat_auditorio.id},
            {"nome": "Sala 104 - Bloco A", "capacidade": 40, "unidade_id": unidade_carangola.id, "categoria_id": cat_sala.id},
            {"nome": "Quadra Poliesportiva", "capacidade": 60, "unidade_id": unidade_carangola.id, "categoria_id": cat_esporte.id},
            {"nome": "Projetor Epson 01", "capacidade": 1, "unidade_id": unidade_carangola.id, "categoria_id": cat_equip.id},
            {"nome": "Laboratório de Redes", "capacidade": 25, "unidade_id": unidade_uba.id, "categoria_id": cat_lab.id},
        ]
        for rec in recursos_iniciais:
            existe = db.session.scalar(
                db.select(Recurso).filter_by(nome=rec["nome"], unidade_id=rec["unidade_id"])
            )
            if not existe:
                db.session.add(Recurso(**rec))
                logger.info(f"Recurso criado: {rec['nome']}")

        db.session.commit()

        # 7. Agendamentos (e tabela associativa de participantes)
        professor = db.session.scalar(db.select(Usuario).filter_by(email="professor@uemg.br"))
        aluno = db.session.scalar(db.select(Usuario).filter_by(email="aluno@uemg.br"))
        lab_01 = db.session.scalar(db.select(Recurso).filter_by(nome="Laboratório de Informática 01"))
        auditorio = db.session.scalar(db.select(Recurso).filter_by(nome="Auditório Principal"))
        status_confirmado = db.session.scalar(db.select(StatusAgendamento).filter_by(nome="Confirmado"))
        status_pendente = db.session.scalar(db.select(StatusAgendamento).filter_by(nome="Pendente"))

        agendamentos_iniciais = [
            {
                "data_hora_inicio": datetime(2026, 11, 25, 19, 0, 0),
                "data_hora_fim": datetime(2026, 11, 25, 21, 0, 0),
                "finalidade": "Aula prática de Banco de Dados",
                "recurso_id": lab_01.id,
                "usuario_id": professor.id,
                "status_id": status_confirmado.id,
                "participantes": [professor, aluno],
            },
            {
                "data_hora_inicio": datetime(2026, 11, 26, 14, 0, 0),
                "data_hora_fim": datetime(2026, 11, 26, 16, 0, 0),
                "finalidade": "Seminário de Sistemas de Informação",
                "recurso_id": auditorio.id,
                "usuario_id": aluno.id,
                "status_id": status_pendente.id,
                "participantes": [aluno],
            },
        ]

        for ag in agendamentos_iniciais:
            existe = db.session.scalar(
                db.select(Agendamento).filter_by(
                    finalidade=ag["finalidade"],
                    recurso_id=ag["recurso_id"]
                )
            )
            if not existe:
                participantes = ag.pop("participantes")
                novo_ag = Agendamento(**ag)
                novo_ag.participantes.extend(participantes)
                db.session.add(novo_ag)
                logger.info(f"Agendamento criado: {novo_ag.finalidade}")

        db.session.commit()
        logger.success("Seed concluído com sucesso! Todas as tabelas estão populadas e prontas para uso.")


if __name__ == '__main__':
    seed_database()