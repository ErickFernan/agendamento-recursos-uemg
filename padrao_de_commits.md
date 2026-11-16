# 📖 Padrão de Commits (Conventional Commits)

Este projeto utiliza o padrão de Commits Convencionais para manter o histórico de versionamento limpo, legível e automatizável.

## 1. A Estrutura do Commit
Todo commit deve seguir a seguinte estrutura obrigatória:

```text
<tipo>(<escopo opcional>): <descrição curta no imperativo>

[corpo opcional explicando o POR QUÊ e O QUÊ foi feito, não o COMO]

[rodapé opcional indicando fechamento de issues ou breaking changes]
```

## 2. Tipos de Commits Permitidos (`<tipo>`)

*   ✨ **`feat`**: Uma nova funcionalidade (feature) para o usuário ou para a API.
*   🐛 **`fix`**: Correção de um bug ou erro no código.
*   📚 **`docs`**: Alterações exclusivas na documentação (README, Swagger, comentários).
*   ♻️ **`refactor`**: Uma alteração de código que não corrige um bug nem adiciona uma feature (ex: renomear variáveis, simplificar uma função).
*   🛠️ **`chore`**: Atualizações de tarefas de build, configuração, dependências (ex: `requirements.txt`, `docker-compose`, `.gitignore`).
*   🎨 **`style`**: Alterações que não afetam o significado do código (espaçamento, formatação, linting, PEP8).
*   ⚡ **`perf`**: Uma mudança de código que melhora o desempenho (performance).
*   ✅ **`test`**: Adição de testes ausentes ou correção de testes existentes.
*   👷 **`ci`**: Mudanças em arquivos e scripts de configuração de CI/CD (GitHub Actions, etc).

## 3. Regras de Ouro da Descrição (Título)
1. **Use o tempo verbal IMPERATIVO:** Escreva como se estivesse dando uma ordem ao sistema. (✅ *Use: "adiciona", "corrige", "implementa"*. ❌ *Não use: "adicionado", "corrigindo", "implementei"*).
2. **Comece com letra minúscula** logo após os dois pontos.
3. **Não coloque ponto final (`.`)** no fim do título.
4. **Limite de 50 a 72 caracteres** no título para não quebrar a visualização no GitHub.

---

## 4. Exemplos Práticos (Casos de Uso do Projeto)

### Exemplo 1: Adicionando uma nova funcionalidade (Sem corpo)
O caso mais comum do dia a dia, alteração direta e reta.
```text
feat(unidades): implementa rota POST para cadastro de unidades
```

### Exemplo 2: Corrigindo um Bug (Com escopo e corpo)
Use o corpo (pulando uma linha após o título) para explicar o motivo da correção.
```text
fix(banco): resolve erro 500 ao deletar unidade com dependentes

O banco estava disparando um IntegrityError sem tratamento ao 
tentar deletar uma Unidade que possuía Recursos vinculados.
Foi adicionado um bloco except para retornar erro 409 (Conflict).
```

### Exemplo 3: Atualizando Dependências / Configurações (Chore)
```text
chore(deps): adiciona loguru e flasgger ao requirements.txt
```

### Exemplo 4: Escrevendo Documentação (Docs)
```text
docs(swagger): cria arquivo yaml para documentar GET de unidades
```

### Exemplo 5: Refatoração de Código
O código já funcionava, mas você deixou ele mais limpo ou mais rápido.
```text
refactor(rotas): move lógica de validação do marshmallow para um decorator
```

### Exemplo 6: Fechando uma Issue do GitHub (Rodapé)
Se você usa a aba "Issues" do GitHub ou GitHub Projects (Kanban), ao citar `Closes #numero`, o GitHub fecha a tarefa automaticamente quando o merge é feito na branch principal.
```text
feat(crud): finaliza rotas PUT, PATCH e DELETE de unidades

Implementado o método de soft update e validação parcial com 
Marshmallow para a entidade Unidade.

Closes #1
```

### Exemplo 7: Mudança Crítica (Breaking Change)
Quando você faz uma alteração que vai quebrar o código de quem tentar rodar a versão antiga. Deve conter `BREAKING CHANGE:` no rodapé ou uma `!` após o tipo.
```text
feat(auth)!: altera o método de login para exigir token JWT

BREAKING CHANGE: As rotas da API agora exigem o cabeçalho 
'Authorization: Bearer <token>' para serem acessadas. O acesso 
público foi revogado.
```