param(
    [string]$ArquivoEnv = ".env",
    [string]$NomeAdmin,
    [string]$EmailAdmin,
    [string]$TelefoneAdmin,
    [switch]$SemAdmin,
    [int]$TentativasSaude = 30,
    [int]$IntervaloSegundos = 2
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ler-VariaveisDotEnv {
    param([string]$CaminhoArquivo)

    $variaveis = @{}

    if (-not (Test-Path -Path $CaminhoArquivo)) {
        return $variaveis
    }

    foreach ($linhaBruta in Get-Content -Path $CaminhoArquivo) {
        $linha = $linhaBruta.Trim()
        if (-not $linha -or $linha.StartsWith("#")) {
            continue
        }

        $partes = $linha -split "=", 2
        if ($partes.Count -ne 2) {
            continue
        }

        $chave = $partes[0].Trim()
        $valor = $partes[1].Trim()

        if ($valor.StartsWith('"') -and $valor.EndsWith('"')) {
            $valor = $valor.Trim('"')
        }
        elseif ($valor.StartsWith("'") -and $valor.EndsWith("'")) {
            $valor = $valor.Trim("'")
        }

        $variaveis[$chave] = $valor
    }

    return $variaveis
}

function Obter-ValorConfiguracao {
    param(
        [string]$Nome,
        [string]$ValorExplicito,
        [hashtable]$VariaveisDotEnv,
        [string]$ValorPadrao = ""
    )

    if ($ValorExplicito) {
        return $ValorExplicito
    }

    if ($VariaveisDotEnv.ContainsKey($Nome) -and $VariaveisDotEnv[$Nome]) {
        return $VariaveisDotEnv[$Nome]
    }

    $variavelAmbiente = [Environment]::GetEnvironmentVariable($Nome)
    if ($variavelAmbiente) {
        return $variavelAmbiente
    }

    return $ValorPadrao
}

function Ler-SegredoSeguro {
    param([string]$Mensagem)

    $secureValue = Read-Host -Prompt $Mensagem -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)

    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        if ($bstr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }
}

$raizProjeto = Resolve-Path (Join-Path $PSScriptRoot "..")
$caminhoEnv = Join-Path $raizProjeto $ArquivoEnv
$variaveisDotEnv = Ler-VariaveisDotEnv -CaminhoArquivo $caminhoEnv

$nomeAdminResolvido = Obter-ValorConfiguracao -Nome "ADMIN_BOOTSTRAP_NOME" -ValorExplicito $NomeAdmin -VariaveisDotEnv $variaveisDotEnv -ValorPadrao "Administrador Docker"
$emailAdminResolvido = Obter-ValorConfiguracao -Nome "ADMIN_BOOTSTRAP_EMAIL" -ValorExplicito $EmailAdmin -VariaveisDotEnv $variaveisDotEnv
$senhaAdminResolvida = Obter-ValorConfiguracao -Nome "ADMIN_BOOTSTRAP_SENHA" -ValorExplicito $null -VariaveisDotEnv $variaveisDotEnv
$telefoneAdminResolvido = Obter-ValorConfiguracao -Nome "ADMIN_BOOTSTRAP_TELEFONE" -ValorExplicito $TelefoneAdmin -VariaveisDotEnv $variaveisDotEnv -ValorPadrao "11999990000"
$portaApi = Obter-ValorConfiguracao -Nome "API_PORT" -ValorExplicito $null -VariaveisDotEnv $variaveisDotEnv -ValorPadrao "8000"

Push-Location $raizProjeto
try {
    Write-Host "Subindo a stack Docker local..."
    & docker compose up -d --build

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao subir os containers com docker compose."
    }

    $urlHealth = "http://127.0.0.1:$portaApi/health"
    Write-Host "Aguardando a API responder em $urlHealth ..."

    $apiDisponivel = $false
    for ($tentativa = 1; $tentativa -le $TentativasSaude; $tentativa++) {
        try {
            $resposta = Invoke-WebRequest -UseBasicParsing -Uri $urlHealth -TimeoutSec 5
            if ($resposta.StatusCode -eq 200) {
                $apiDisponivel = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds $IntervaloSegundos
            continue
        }
    }

    if (-not $apiDisponivel) {
        throw "A API nao respondeu com sucesso dentro do tempo esperado."
    }

    Write-Host "API pronta."

    if ($SemAdmin) {
        Write-Host "Bootstrap finalizado sem criacao de administrador."
        return
    }

    if (-not $emailAdminResolvido) {
        throw "Defina ADMIN_BOOTSTRAP_EMAIL no .env ou informe -EmailAdmin."
    }

    if (-not $senhaAdminResolvida) {
        $senhaAdminResolvida = Ler-SegredoSeguro -Mensagem "Digite a senha do administrador"
    }

    if (-not $senhaAdminResolvida) {
        throw "Defina ADMIN_BOOTSTRAP_SENHA no .env ou informe a senha quando solicitado."
    }

    $comandoAdmin = @(
        "compose",
        "exec",
        "-T",
        "api",
        "python",
        "-m",
        "app.scripts.criar_admin",
        "--nome",
        $nomeAdminResolvido,
        "--email",
        $emailAdminResolvido,
        "--senha-stdin"
    )

    if ($telefoneAdminResolvido) {
        $comandoAdmin += @("--telefone", $telefoneAdminResolvido)
    }

    Write-Host "Criando ou promovendo administrador..."
    $senhaAdminResolvida | & docker @comandoAdmin

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao executar o bootstrap do administrador."
    }

    Write-Host "Bootstrap concluido."
    Write-Host "API: http://127.0.0.1:$portaApi"
}
finally {
    Pop-Location
}
