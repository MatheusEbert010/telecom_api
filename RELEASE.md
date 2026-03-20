# Processo de Release

Este arquivo documenta um fluxo simples e seguro para publicar novas versoes da Telecom API.

## Quando criar uma tag

Crie uma tag apenas quando:

- os arquivos da release estiverem commitados
- os testes estiverem passando
- o `README` e o `CHANGELOG` refletirem o estado real do projeto

## Passo a passo recomendado

### 1. Revisar o estado do repositório

```powershell
git status
```

### 2. Rodar qualidade local

```powershell
venv\Scripts\python.exe -m ruff check app tests alembic
venv\Scripts\python.exe -m pytest
```

### 3. Criar commit da release

Exemplo:

```powershell
git add .
git commit -m "Prepare release v1.0.0"
```

### 4. Criar tag anotada

```powershell
git tag -a v1.0.0 -m "Release v1.0.0"
```

### 5. Enviar branch e tag

```powershell
git push origin main
git push origin v1.0.0
```

### 6. Publicar release no GitHub

Ao abrir a tela de Releases no GitHub:

- escolha a tag `v1.0.0`
- use o `CHANGELOG.md` como base das notas
- revise o titulo e a descricao
- publique a release

## Convencao sugerida

- `v1.0.0` para primeira release estavel
- `v1.0.1` para correcoes
- `v1.1.0` para novas funcionalidades compativeis
- `v2.0.0` para mudancas quebrando compatibilidade
