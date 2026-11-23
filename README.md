# 🎓 API de Agendamento de Recursos - UEMG

Bem-vindo ao repositório oficial da API de Agendamento de Recursos da UEMG!  
Este projeto tem como objetivo fornecer uma plataforma robusta, segura e documentada para a gestão e reserva de espaços físicos (salas, laboratórios, auditórios, quadras) e equipamentos da universidade.

> ⚠️ **AVISO IMPORTANTE:** A versão mais atualizada e em desenvolvimento ativo deste projeto encontra-se na branch `dev`. A branch `master` contém apenas versões estáveis e finalizadas. Se você acabou de clonar o repositório, certifique-se de mudar para a branch correta!

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.11
- **Framework Web:** Flask
- **Banco de Dados:** PostgreSQL (Produção/Desenvolvimento) e SQLite em memória (Testes Automatizados)
- **ORM & Migrations:** SQLAlchemy 2.0 + Flask-Migrate (Alembic)
- **Infraestrutura:** Docker & Docker Compose
- **Validação e Serialização:** Marshmallow
- **Segurança & Autenticação:** Flask-JWT-Extended (Tokens JWT + RBAC)
- **Documentação API:** Flasgger (Swagger UI)
- **Monitoramento & Logs:** Loguru
- **Testes Automatizados:** Pytest
- **Integração Contínua (CI):** GitHub Actions + Rulesets

---

## 🔗 Links Úteis e Documentação

* 📄 **Documentação Interativa (Swagger):** Com os containers rodando, acesse a documentação completa e teste as rotas diretamente no navegador através de `http://localhost:5000/apidocs/`
* 📊 **Quadro Kanban (Roadmap):** Acompanhe o status de desenvolvimento, as *issues* atuais e as próximas entregas do projeto no nosso [Painel do GitHub Projects](https://github.com/users/ErickFernan/projects/4/views/1).

---

## 🗺️ Módulos e Endpoints da API

A API segue o padrão RESTful com prefixo `/api` e controle de acesso baseado em perfis (**RBAC**):

| Módulo | Base URL | Métodos | Controle de Acesso e Regras Principais |
| :--- | :--- | :--- | :--- |
| **Autenticação** | `/api/login` | `POST` | Público. Valida credenciais e retorna o Token JWT com `sub` (ID) e `perfis`. |
| **Unidades** | `/api/unidades` | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | Leitura para autenticados; escrita restrita a `admin`. Impede exclusão com vínculos (`409`). |
| **Categorias** | `/api/categorias` | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | Leitura para autenticados; escrita restrita a `admin`. Impede nomes duplicados e exclusão com recursos vinculados (`409`). |
| **Recursos** | `/api/recursos` | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | Leitura para autenticados (com suporte a filtros); escrita restrita a `admin`. Nome único por unidade. |
| **Usuários** | `/api/usuarios` | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | Criação, listagem geral e exclusão restritas a `admin`. Consulta individual e edição liberadas para `admin` ou para o próprio usuário. |
| **Perfis** | `/api/perfis` | `GET` | **Somente leitura** para autenticados. Usado para popular seletores no front-end sem comprometer as regras fixas de RBAC. |
| **Status de Agendamento** | `/api/status-agendamento` | `GET` | **Somente leitura** para autenticados. Protege a máquina de estados (`Pendente`, `Confirmado`, `Cancelado`, `Rejeitado`, `Concluído`). |
| **Agendamentos** | `/api/agendamentos` | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | Qualquer autenticado solicita reservas (com filtros por `recurso_id`, `usuario_id` e `status_id` e vínculo N:N de participantes). Aplica horas inteiras, janela 07h–22h (livre para `admin`), prioridade docente sobre pendentes de alunos e auditoria em log. |

> 💡 **Decisão de Arquitetura:** `Perfis` e `Status de Agendamento` são propositalmente expostos apenas via `GET` e populados via `seed.py`. Como o código da API depende desses nomes exatos para autorização (RBAC) e máquina de estados das reservas, impedir alterações via API evita quebras em produção.

### 📋 Regras de Negócio e Auditoria (Agendamentos)

- **Horas Inteiras:** `data_hora_inicio` e `data_hora_fim` devem ser informados em horas cheias (ex.: `14:00:00` às `16:00:00`), com término obrigatoriamente posterior ao início (`400 Bad Request`).
- **Janela de Funcionamento:** Usuários comuns (`aluno`, `professor`, `comunidade`) só podem reservar em reservas que iniciem e terminem na mesma data, entre **07:00 e 22:00**. Administradores (`admin`) possuem **horário livre** para eventos especiais ou noturnos.
- **Solicitante e Status Inicial:** Usuários comuns reservam apenas para si mesmos e a solicitação nasce como **`Pendente`**. Administradores podem reservar em nome de terceiros (`usuario_id`) e já criar a reserva como **`Confirmado`** (ou definir o status manualmente).
- **Conflito de Horários e Prioridade Docente:**
  - Sobreposição com agendamento **`Confirmado`** bloqueia sempre (`409 Conflict`).
  - Sobreposição apenas com solicitação **`Pendente`** de `aluno`/`comunidade`: **`professor` ou `admin` tem prioridade** — a reserva pendente do aluno é automaticamente movida para **`Rejeitado`** e a API retorna um aviso com os IDs substituídos.
  - Conflitos entre pares (`aluno` × `aluno` ou `professor` × `professor`) retornam `409 Conflict`.
- **Permissões Granulares:** Apenas `admin` pode aprovar (`Confirmado`), rejeitar (`Rejeitado`) ou concluir (`Concluído`). O próprio solicitante pode editar, cancelar (`Cancelado`) ou excluir sua reserva.
- **Auditoria (Loguru):** Criação para terceiros, atualizações (`PUT`/`PATCH`), exclusões (`DELETE`) e sobrescritas por prioridade docente são registradas em log com o ID do usuário responsável pela ação (`[AUDITORIA]`).

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
docker compose up -d --build
```

**Passo D: Criar as Tabelas e Povoar o Banco (`seed.py`)**
Com os containers rodando, aplique as migrações para criar as tabelas no PostgreSQL:
```bash
docker compose exec web flask db upgrade
```

Em seguida, execute o script de **Seed** para alimentar o banco com os dados iniciais do sistema:
```bash
docker compose exec web python seed.py
```

**O que o `seed.py` cria automaticamente?**
O script é **idempotente** (pode ser executado várias vezes sem duplicar registros) e popula todas as tabelas do banco para uso imediato e demonstrações:
- **Perfis de Acesso:** `admin`, `professor`, `aluno`, `comunidade`
- **Status de Agendamento:** `Pendente`, `Confirmado`, `Cancelado`, `Rejeitado`, `Concluído`
- **Categorias de Recursos:** `Laboratório`, `Sala de Aula`, `Auditório`, `Espaço Esportivo`, `Equipamento`
- **Unidades:** UEMG - Carangola (MG) e UEMG - Unidade Ubá (MG)
- **Recursos e Agendamentos de Exemplo:** Salas, laboratórios, auditório, equipamentos e reservas iniciais com participantes vinculados.
- **Usuários Prontos para Teste (RBAC):**

| Perfil | E-mail | Senha | Uso nos Testes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@uemg.br` | `AdminSegura123` | Acesso total (CRUDs administrativos e aprovação de reservas) |
| **Professor** | `professor@uemg.br` | `ProfSegura123` | Solicitação de agendamentos, teste de prioridade docente sobre pendentes de alunos e bloqueio `403` |
| **Aluno** | `aluno@uemg.br` | `AlunoSegura123` | Leitura, solicitação de agendamentos e validação de bloqueio `403` |

Pronto! A API já estará respondendo em `http://localhost:5000`.

---

## 🔑 Como Acessar o Swagger e Testar Rotas Autenticadas

Com exceção da rota de login (`POST /api/login`), todas as rotas da API são protegidas por Token JWT. Para testar as rotas no Swagger, siga o fluxo abaixo:

### 1. Gerar o Token de Acesso
1. Acesse `http://localhost:5000/apidocs/`.
2. Abra a seção **Autenticação** e expanda a rota **`POST /api/login`**.
3. Clique em **Try it out** e envie as credenciais de um dos usuários criados pelo `seed.py` (ex.: administrador):
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

### 3. Validando Autenticação e Autorização
- **Sem token ou token inválido/expirado:** a API retorna **`401 Unauthorized`**.
- **Usuário comum (`aluno`/`professor`) tentando rota administrativa:** a API retorna **`403 Forbidden`**.
- **Administrador (`admin`):** acesso liberado para todas as operações de gestão.

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
> **Permissão Granular (Dono do Recurso):** Em rotas onde o próprio usuário pode consultar ou alterar seus dados (como `GET`/`PUT`/`PATCH /api/usuarios/<id>` ou cancelar o próprio agendamento), valide tanto o perfil de administrador quanto se o ID pertence ao dono do token (`str(id) == claims.get('sub')`).

### 3. Atualizar a Documentação (Swagger)
Todo arquivo `.yml` de rota protegida precisa conter:
1. O bloco `security: - Bearer: []` na raiz do documento.
2. O código de resposta `401` para token inválido/ausente.
3. O código de resposta `403` caso a rota exija privilégios específicos.

---

## 🧪 Testes Automatizados e Integração Contínua (CI/CD)

A qualidade da API é garantida por uma suíte de testes automatizados em **Pytest** integrada diretamente ao fluxo de Pull Requests no **GitHub Actions**.

### Arquitetura dos Testes
- **Padrão Atômico (Arrange-Act-Assert):** Cada função de teste valida um único cenário específico (sucesso, validação `400`, falta de token `401`, bloqueio RBAC `403`, recurso inexistente `404` e conflitos `409`), facilitando o diagnóstico imediato em caso de falha.
- **Banco Isolado em Memória (`SQLite`):** As *fixtures* configuradas em `tests/conftest.py` sobem um banco SQLite em memória a cada teste. Isso garante execução em poucos segundos, isolamento total entre cenários e zero impacto nos dados do PostgreSQL local ou de produção.

### Rodando os testes localmente
Para validar suas alterações antes de subir para o GitHub, execute dentro do container (ou no ambiente virtual local):
```bash
docker compose exec web pytest -v
```

### Pipeline de CI no GitHub Actions
O repositório conta com o workflow **Testes Automatizados (Pytest)** definido em `.github/workflows/ci-tests.yml`. Sempre que um **Pull Request** é aberto ou atualizado apontando para as branches `dev` ou `master`, o pipeline é disparado automaticamente na nuvem:
1. Provisiona um runner Ubuntu com **Python 3.11** limpo.
2. Instala todas as dependências listadas em `requirements.txt`.
3. Executa o job `test` rodando toda a suíte com `pytest -v`.

> 🛑 **Trava de Segurança (GitHub Rulesets):** As branches `dev` e `master` possuem **Rulesets** ativos exigindo Pull Request e aprovação obrigatória dos *status checks* (`test`). **Se qualquer teste falhar no CI, o botão de Merge fica bloqueado automaticamente** até que o erro seja corrigido e todos os checks fiquem verdes (`All checks have passed`).

---

## 👨‍💻 Regras de Desenvolvimento e Fluxo de Trabalho

Para mantermos o código organizado e profissional, adotamos as seguintes regras baseadas no **Git Flow** e metodologias ágeis.

### 1. A Regra de Ouro das Branches
- **`master` (ou `main`):** É o ambiente de Produção. Código estável; nunca fazemos commits diretos nela.
- **`dev`:** É o ambiente de Integração. Todo código novo entra aqui via Pull Request. Commits diretos são bloqueados via **Rulesets** no GitHub.
- **Branches Temporárias (`feat/`, `bugfix/`, `test/`, `chore/`):** Todo o trabalho deve ser feito em uma branch temporária criada a partir da `dev`.
  - Exemplo: `git checkout -b feat/crud-agendamentos`

### 2. O Ciclo da Tarefa (Issue)
1. Pegue uma tarefa no nosso Kanban e mova para **In Progress**.
2. Crie sua branch a partir da `dev` (`feat/...`).
3. Programe, escreva os testes atômicos, rode o `pytest -v` localmente e faça seus commits referenciando a Issue (ex.: `feat: cria rotas de agendamentos. Closes #12`).
4. Envie sua branch para o GitHub: `git push -u origin feat/sua-branch`.
5. Abra um **Pull Request (PR)** apontando para a branch `dev`.
6. Aguarde a execução do **GitHub Actions** e verifique se o job de testes passou.

### 3. Revisão de Código (Code Review)
**É estritamente proibido aprovar o próprio código!**  
Após abrir o Pull Request e passar nos testes do CI, solicite a revisão do Tech Lead. O código só será integrado à branch `dev` após ser lido, validado e aprovado.

### 4. Estratégia de Merge: O que é "Squash and Merge"?
Nosso repositório está configurado para aceitar exclusivamente o método **Squash and Merge** nos Pull Requests.

**O que isso significa?**  
Enquanto você desenvolve, é normal criar dezenas de pequenos commits ("salva arquivo", "corrige erro de digitação", "testa rota"). Se juntássemos tudo isso, o histórico do projeto viraria uma bagunça ilegível.  
O **Squash** agrupa todos os commits da sua branch temporária e os transforma em **um único commit limpo e semântico** no momento em que o código entra na `dev`.

**Vantagem:** O histórico da nossa branch principal fica linear e limpo, onde cada commit representa uma funcionalidade inteira concluída e testada.