# Frontend Demo

Frontend inicial em `Next.js + React` para consumir a Telecom API, testar o fluxo publico e validar autenticacao antes de evoluir para o produto final.

## O que ja vem pronto

- painel visual com status da API
- listagem publica de planos
- cadastro de usuario
- login com armazenamento da sessao no `sessionStorage`
- consulta de `/users/me` e `/users/me/plan`

## Como rodar

1. Entre na pasta:

```powershell
cd frontend
```

2. Instale as dependencias:

```powershell
npm.cmd install
```

3. Crie o arquivo de ambiente:

```powershell
Copy-Item .env.local.example .env.local
```

4. Ajuste a URL da API em `.env.local`:

```env
NEXT_PUBLIC_API_URL=https://sua-url.trycloudflare.com
```

5. Inicie o frontend:

```powershell
npm.cmd run dev
```

6. Abra:

```text
http://localhost:3000
```

## Reset da base de demonstracao

Para limpar o banco externo e recriar o cenario inicial:

```powershell
cd ..
venv\Scripts\python.exe -m app.scripts.reset_demo_data
```

Credenciais iniciais do admin:

```text
email: matheus.admin@telecomdemo.com
senha: MatheusAdmin@2026!
```

## Observacoes

- Se voce reiniciar o `cloudflared`, a URL `trycloudflare.com` muda e voce precisa atualizar `NEXT_PUBLIC_API_URL`.
- O frontend assume que a API responde em `/api/v1`.
- Para o frontend funcionar com chamadas reais, deixe a API local e o tunnel ativos ao mesmo tempo.
- O script `npm.cmd run dev` usa `--webpack` por compatibilidade. Na sua maquina, o Turbopack falhou por incompatibilidade de CPU com a instrucao `bmi2`.
- Se quiser testar o Turbopack depois, use `npm.cmd run dev:turbo`.
