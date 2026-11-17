# 🎓 API de Agendamento de Recursos - UEMG

Bem-vindo ao repositório oficial da API de Agendamento de Recursos da UEMG! 
Este projeto tem como objetivo fornecer uma plataforma robusta para a gestão e reserva de espaços físicos (salas, laboratórios, quadras) e equipamentos da universidade.

> ⚠️ **AVISO IMPORTANTE:** A versão mais atualizada e em desenvolvimento ativo deste projeto encontra-se na branch `dev`. A branch `master` contém apenas versões estáveis e finalizadas. Se você acabou de clonar o repositório, certifique-se de mudar para a branch correta!

## 🛠️ Tecnologias Utilizadas
- **Linguagem:** Python 3
- **Framework Web:** Flask
- **Banco de Dados:** PostgreSQL
- **ORM & Migrations:** SQLAlchemy + Alembic
- **Infraestrutura:** Docker & Docker Compose
- **Validação de Dados:** Marshmallow

---

## 🔗 Links Úteis e Documentação

* 📄 **Documentação Interativa (Swagger):** Com os containers rodando, acesse a documentação completa e teste as rotas diretamente no navegador através de `http://localhost:5000/apidocs/`
* 📊 **Quadro Kanban (Roadmap):** Acompanhe o status de desenvolvimento, as *issues* atuais e as próximas entregas do projeto no nosso [Painel do GitHub Projects](https://github.com/users/ErickFernan/projects/4/views/1).

## 🚀 Como Inicializar o Projeto (Onboarding)

Para rodar este projeto na sua máquina local, siga os passos abaixo:

### 1. Pré-requisitos
Certifique-se de ter instalado em sua máquina:
- [Docker](https://www.docker.com/) e Docker Compose
- [Git](https://git-scm.com/) (com chave SSH configurada no GitHub)
- [VS Code](https://code.visualstudio.com/) (ou outra IDE de sua preferência)
- [DBeaver](https://dbeaver.io/) (para visualizar o banco de dados)
- [Postman](https://www.postman.com/) ou Insomnia (para testar as requisições da API)

### 2. Passo a Passo de Instalação

**Passo A: Clonar o Repositório**
Abra o seu terminal e rode o comando:
```bash
git clone git@github.com:ErickFernan/agendamento-recursos-uemg.git
cd agendamento-recursos-uemg
```
> **Nota:** Após clonar, lembre-se de mudar para a branch de desenvolvimento com o comando `git checkout dev`.

**Passo B: Configurar Variáveis de Ambiente**
Solicite ao Tech Lead (Erick) o arquivo `.env` do projeto. Coloque este arquivo na raiz do repositório (ele contém as senhas do banco de dados e segredos da aplicação e nunca deve ser "commitado").

**Passo C: Subir os Containers**
Construa e inicie a infraestrutura via Docker:
```bash
docker compose up
# Ou
docker compose up -d
# Se quiser deixar rodando em background
```

**Passo D: Criar as Tabelas no Banco de Dados**
Com os containers rodando, aplique as migrações para criar as tabelas no PostgreSQL:
```bash
docker compose exec web flask db upgrade
```
Pronto! A API já estará respondendo em `http://localhost:5000`.

---

## 👨‍💻 Regras de Desenvolvimento e Fluxo de Trabalho

Para mantermos o código organizado e profissional, adotamos as seguintes regras baseadas no **Git Flow** e metodologias ágeis.

### 1. A Regra de Ouro das Branches
- **`master` (ou `main`):** É o ambiente de Produção. Código sagrado, nunca tocamos nela diretamente.
- **`dev`:** É o ambiente de Integração. Todo código novo vai para cá primeiro. Também **nunca** fazemos commits diretos nela.
- **Branches Temporárias (`feat/`, `bugfix/`):** Todo o trabalho deve ser feito em uma branch temporária criada a partir da `dev`. 
- Exemplo: `git checkout -b feat/crud-usuarios`

### 2. O Ciclo da Tarefa (Issue)
1. Pegue uma tarefa no nosso Kanban e mova para **In Progress**.
2. Crie sua branch (`feat/...`).
3. Programe e faça seus commits referenciando a Issue. Exemplo: `feat: cria rotas de usuario. Closes #5`.
4. Envie sua branch para o GitHub: `git push -u origin feat/sua-branch`.
5. Abra um **Pull Request (PR)** apontando para a branch `dev`.

### 3. Revisão de Código (Code Review)
**É estritamente proibido aprovar o próprio código!**
Após abrir o Pull Request, você deve solicitar a revisão do Tech Lead. O código só será integrado à branch `dev` após ser lido, validado e aprovado. 

### 4. Estratégia de Merge: O que é "Squash and Merge"?
Quando o Tech Lead for aprovar o seu código, ele não fará um merge tradicional, mas sim um **Squash and Merge**.

**O que isso significa?**
Enquanto você desenvolve, é normal criar dezenas de pequenos commits ("salva arquivo", "corrige erro de digitação", "testa rota"). Se juntássemos tudo isso, o histórico do projeto viraria uma bagunça ilegível.
O **Squash** "esmaga" (agrupa) todos os commits da sua branch temporária e os transforma em **um único commit limpo e semântico** no momento em que o código entra na `dev`. 

**Vantagem:** O histórico da nossa branch principal fica perfeito, parecendo um livro onde cada parágrafo (commit) é uma funcionalidade inteira concluída e testada.