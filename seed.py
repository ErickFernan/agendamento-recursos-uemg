from app import create_app, db
from app.models import Perfil, StatusAgendamento, CategoriaRecurso, Unidade, Usuario
from werkzeug.security import generate_password_hash
from loguru import logger

app = create_app()

def seed_database():
    with app.app_context():
        logger.info("Iniciando o povoamento (Seed) do banco de dados...")

        # 1. Perfis de Acesso (RBAC)
        perfis_iniciais = ['admin', 'professor', 'aluno', 'comunidade']
        for nome_perfil in perfis_iniciais:
            if not Perfil.query.filter_by(nome=nome_perfil).first():
                db.session.add(Perfil(nome=nome_perfil))
                logger.info(f"Perfil criado: {nome_perfil}")

        # 2. Status de Agendamento
        status_iniciais = ['Pendente', 'Confirmado', 'Cancelado', 'Rejeitado', 'Concluído']
        for nome_status in status_iniciais:
            if not StatusAgendamento.query.filter_by(nome=nome_status).first():
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
            if not CategoriaRecurso.query.filter_by(nome=cat["nome"]).first():
                db.session.add(CategoriaRecurso(nome=cat["nome"], descricao=cat["descricao"]))
                logger.info(f"Categoria criada: {cat['nome']}")

        # 4. Unidade Padrão
        unidade_padrao = Unidade.query.filter_by(nome="Universidade do Estado de Minas Gerais", cidade="Carangola").first()
        if not unidade_padrao:
            unidade_padrao = Unidade(
                nome="Universidade do Estado de Minas Gerais",
                sigla="UEMG",
                cidade="Carangola",
                estado="MG"
            )
            db.session.add(unidade_padrao)
            logger.info("Unidade padrão criada: UEMG - Carangola")

        # Salva as entidades independentes para gerar os IDs no banco
        db.session.commit()

        # 5. Usuário Administrador Inicial (Para destravar o primeiro acesso)
        email_admin = "admin@uemg.br"
        admin_user = Usuario.query.filter_by(email=email_admin).first()
        if not admin_user:
            perfil_admin = Perfil.query.filter_by(nome='admin').first()
            
            novo_admin = Usuario(
                nome="Administrador UEMG",
                email=email_admin,
                senha_hash=generate_password_hash("AdminSegura123"),
                unidade_id=unidade_padrao.id
            )
            # O SQLAlchemy preenche a tabela associativa 'usuario_perfil' automaticamente aqui:
            novo_admin.perfis.append(perfil_admin)
            
            db.session.add(novo_admin)
            db.session.commit()
            logger.info(f"Usuário Admin criado! E-mail: {email_admin} | Senha: AdminSegura123")
        else:
            logger.info("Usuário Admin padrão já existe.")

        logger.success("Seed concluído com sucesso! O banco está pronto para uso.")

if __name__ == '__main__':
    seed_database()

    