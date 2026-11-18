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
- **Segurança & Autenticação:** Flask-JWT-Extended (Tokens JWT + RBAC)
- **Documentação API:** Flasgger (Swagger UI)
- **Monitoramento & Logs:** Loguru
- **Testes Automatizados:** Pytest
- **Integração Contínua (CI):** GitHub Actions

---

## 🔗 Links Úteis e Documentação

* 📄 **Documentação Interativa (Swagger):** Com os containers rodando, acesse a documentação completa e teste as rotas diretamente no navegador através de `http://localhost:5000/apidocs/`
* 📊 **Quadro Kanban (Roadmap):** Acompanhe o status de desenvolvimento, as *issues* atuais e as próximas entregas do projeto no nosso [Painel do GitHub Projects](https://github.com/users/ErickFernan/projects/4/views/1).

---

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
Solicite ao Tech Lead o arquivo `.env` do projeto (ou utilize o `env_example.txt` como base para preencher o seu `.env`). Coloque este arquivo na raiz do repositório (ele contém as senhas do banco de dados e chaves secretas do JWT e nunca deve ser "commitado").

**Passo C: Subir os Containers**
Construa e inicie a infraestrutura via Docker:
```bash
docker compose up
# Ou
docker compose up -d
# Se quiser deixar rodando em background
```

**Passo D: Criar as Tabelas e Povoar o Banco (`seed.py`)**
Com os containers rodando, aplique as migrações para criar as tabelas no PostgreSQL:
```bash
docker compose exec web flask db upgrade
```

Em seguida, execute o script de **Seed** para alimentar o banco com os dados iniciais obrigatórios do sistema:
```bash
docker compose exec web python seed.py
```

**O que o `seed.py` cria automaticamente?**
O script é *idempotente* (pode ser rodado várias vezes sem duplicar registros) e popula as tabelas base:
- **Perfis de Acesso:** `admin`, `professor`, `aluno`, `comunidade`
- **Status de Agendamento:** `Pendente`, `Confirmado`, `Cancelado`, `Rejeitado`, `Concluído`
- **Categorias de Recursos:** `Laboratório`, `Sala de Aula`, `Auditório`, `Espaço Esportivo`, `Equipamento`
- **Unidade Padrão:** UEMG - Carangola (MG)
- **Usuário Administrador Inicial:**
  - **E-mail:** `admin@uemg.br`
  - **Senha:** `AdminSegura123`

Pronto! A API já estará respondendo em `http://localhost:5000`.

---

## 🔑 Como Acessar o Swagger e Criar Usuários Autenticados

Com exceção da rota de login (`POST /api/login`), todas as rotas da API são protegidas por Token JWT. Para testar as rotas no Swagger (como criar novos usuários ou unidades), siga o fluxo abaixo:

### 1. Gerar o Token de Acesso
1. Acesse `http://localhost:5000/apidocs/`.
2. Abra a seção **Autenticação** e expanda a rota **`POST /api/login`**.
3. Clique em **Try it out** e envie as credenciais do administrador criado pelo `seed.py`:
```json
{
  "email": "admin@uemg.br",
  "senha": "AdminSegura123"
}
```
4. Na resposta `200 OK`, copie **apenas o texto** do campo `access_token` (sem as aspas duplas e sem espaços/quebras de linha extras).

### 2. Autenticar no Swagger (Botão Authorize)
1. Clique no botão verde **Authorize** (ícone de cadeado) no topo direito da página do Swagger.
2. No campo `Value`, digite a palavra `Bearer`, dê **um único espaço** e cole o seu token:
   ```text
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
   ```
3. Clique em **Authorize** e depois em **Close**.

> 💡 **Dica para o Postman:** Na aba **Authorization**, selecione o tipo **Bearer Token** e cole apenas o token puro (o Postman adiciona a palavra `Bearer` automaticamente).

### 3. Criar Novos Usuários e Testar Rotas Protegidas
Com o cadeado fechado como `admin`, você já pode expandir **`POST /api/usuarios`**, clicar em **Try it out** e cadastrar novos usuários informando `nome`, `email`, `senha` e `unidade_id`.
- Se tentar acessar sem token ou com token adulterado/expirado, a API retornará **`401 Unauthorized`**.
- Se tentar acessar uma rota administrativa com um usuário comum (ex: `aluno`), a API retornará **`403 Forbidden`**.

---

## 🔒 Segurança e Autorização (Padrão para Novas Rotas)

A nossa API utiliza o padrão **Stateless JWT** com **RBAC (Role-Based Access Control)**. Os privilégios (ex: `admin`, `aluno`) e o ID do usuário (`sub`) são embutidos dentro do próprio token no momento do login.

Ao criar uma nova rota que exige segurança, você **DEVE** seguir este padrão:

### 1. Proteger a Rota (Autenticação)
Use o decorador `@jwt_required()` logo abaixo do Swagger e antes da função. Isso garante que apenas usuários logados (com um Header `Bearer Token` válido) acessem a rota.
```python
from flask_jwt_extended import jwt_required, get_jwt

@meu_bp.route('/minha-rota', methods=['GET'])
@swag_from(...)
@jwt_required()
def minha_funcao():
    # Código executado apenas se o token for válido
```

### 2. Restringir por Perfil (Autorização)
Se a rota fizer alterações críticas (`POST`, `PUT`, `PATCH`, `DELETE`), extraia as *claims* do token e valide se o usuário possui a *role* necessária (ex: `admin`). Caso não tenha, retorne o Erro HTTP `403` (Forbidden).
```python
@meu_bp.route('/minha-rota', methods=['POST'])
@swag_from(...)
@jwt_required()
def minha_funcao_critica():
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        return jsonify({"erro": "Acesso negado. Requer privilégios de administrador."}), 403
    
    # Continua o fluxo normal...
```
> **Permissão Granular (Dono do Recurso):** Em rotas onde o próprio usuário pode alterar seus dados (como `PUT` e `PATCH /api/usuarios/<id>`), valide tanto o perfil de administrador quanto se o ID da rota corresponde ao dono do token (`str(id) == claims.get('sub')`).

### 3. Atualizar a Documentação (Swagger)
Todo arquivo `.yml` de rota protegida precisa ter as seguintes adições:
1. O bloco `security: - Bearer: []` (na raiz do documento).
2. O código de resposta `401` para token inválido/ausente.
3. O código de resposta `403` caso a rota exija privilégios específicos.

---

## 🧪 Testes Automatizados e Integração Contínua (CI)

O projeto conta com uma suíte de testes automatizados utilizando **Pytest** integrada ao **GitHub Actions** para garantir que novas alterações não quebrem funcionalidades existentes.

### Rodando os testes localmente
Para validar seu código antes de abrir um Pull Request, execute os testes dentro do container:
```bash
docker compose exec web pytest -v
```

### Pipeline de CI no GitHub Actions
Sempre que um **Pull Request** é aberto ou atualizado apontando para as branches `dev` ou `master`, o workflow `.github/workflows/ci-tests.yml` é disparado automaticamente na nuvem:
1. Sobe um ambiente Python 3.11 limpo.
2. Instala as dependências do `requirements.txt`.
3. Executa toda a suíte com `pytest -v`.

> 🛑 **Trava de Segurança (Branch Protection):** As branches `dev` e `master` possuem regras de proteção ativas no GitHub. **Se qualquer teste falhar no CI, o botão de Merge fica bloqueado automaticamente** até que o problema seja corrigido e todos os checks fiquem verdes (`All checks have passed`).

---

## 👨‍💻 Regras de Desenvolvimento e Fluxo de Trabalho

Para mantermos o código organizado e profissional, adotamos as seguintes regras baseadas no **Git Flow** e metodologias ágeis.

### 1. A Regra de Ouro das Branches
- **`master` (ou `main`):** É o ambiente de Produção. Código sagrado, nunca tocamos nela diretamente.
- **`dev`:** É o ambiente de Integração. Todo código novo vai para cá primeiro. Também **nunca** fazemos commits diretos nela (bloqueado via Rulesets no GitHub).
- **Branches Temporárias (`feat/`, `bugfix/`, `test/`, `chore/`):** Todo o trabalho deve ser feito em uma branch temporária criada a partir da `dev`.
  - Exemplo: `git checkout -b feat/crud-recursos`

### 2. O Ciclo da Tarefa (Issue)
1. Pegue uma tarefa no nosso Kanban e mova para **In Progress**.
2. Crie sua branch (`feat/...`).
3. Programe, rode o `pytest` localmente e faça seus commits referenciando a Issue. Exemplo: `feat: cria rotas de recursos. Closes #5`.
4. Envie sua branch para o GitHub: `git push -u origin feat/sua-branch`.
5. Abra um **Pull Request (PR)** apontando para a branch `dev`.
6. Aguarde a execução do **GitHub Actions** e verifique se todos os testes passaram.

### 3. Revisão de Código (Code Review)
**É estritamente proibido aprovar o próprio código!**
Após abrir o Pull Request e passar nos testes do CI, solicite a revisão do Tech Lead. O código só será integrado à branch `dev` após ser lido, validado e aprovado.

### 4. Estratégia de Merge: O que é "Squash and Merge"?
Nosso repositório está configurado para aceitar exclusivamente o método **Squash and Merge** nos Pull Requests.

**O que isso significa?**
Enquanto você desenvolve, é normal criar dezenas de pequenos commits ("salva arquivo", "corrige erro de digitação", "testa rota"). Se juntássemos tudo isso, o histórico do projeto viraria uma bagunça ilegível.
O **Squash** "esmaga" (agrupa) todos os commits da sua branch temporária e os transforma em **um único commit limpo e semântico** no momento em que o código entra na `dev`.

**Vantagem:** O histórico da nossa branch principal fica linear e limpo, parecendo um livro onde cada parágrafo (commit) é uma funcionalidade inteira concluída e testada.