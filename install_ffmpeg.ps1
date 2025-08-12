# --- Script Final para Instalação Automática do FFmpeg no Windows ---
# Versão 4.0 - Focado em compatibilidade máxima de codificação.

# --- Bloco de Verificação de Administrador ---
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "[ERRO] Este script precisa ser executado como Administrador." -ForegroundColor Red
    Write-Host "Por favor, clique com o botão direito no icone do PowerShell e selecione 'Executar como Administrador'." -ForegroundColor Yellow
    Read-Host -Prompt "Pressione Enter para sair"
    exit
}

# --- Configurações ---
$FfmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z"
$InstallDir = "C:\ffmpeg"
$ArchiveName = "ffmpeg.7z"
$ArchivePath = Join-Path $InstallDir $ArchiveName
$BinPath = Join-Path $InstallDir "bin"

# --- Início da Execução ---
Write-Host "================================================="
Write-Host "Iniciando a instalacao automatica do FFmpeg..." -ForegroundColor Cyan
Write-Host "================================================="

# 1. Verifica se o FFmpeg já está no PATH
if (Get-Command "ffmpeg" -ErrorAction SilentlyContinue) {
    Write-Host "[PASSO 1/4] FFmpeg ja foi encontrado. Nenhuma acao necessaria." -ForegroundColor Green
} else {
    Write-Host "[PASSO 1/4] FFmpeg nao encontrado. Iniciando instalacao..."

    # 2. Baixa o FFmpeg
    if (-not (Test-Path $ArchivePath)) {
        Write-Host "[PASSO 2/4] Baixando o FFmpeg..."
        New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
        Invoke-WebRequest -Uri $FfmpegUrl -OutFile $ArchivePath -UseBasicParsing
        Write-Host "   -> Download concluido." -ForegroundColor Green
    } else {
        Write-Host "[PASSO 2/4] Arquivo do FFmpeg ja encontrado." -ForegroundColor Green
    }

    # 3. Extrai o FFmpeg
    if (-not (Test-Path $BinPath)) {
        Write-Host "[PASSO 3/4] Extraindo os arquivos..."
        Expand-Archive -Path $ArchivePath -DestinationPath "$InstallDir-temp" -Force
        $ExtractedFolder = Get-ChildItem -Path "$InstallDir-temp" | Select-Object -First 1
        Move-Item -Path (Join-Path $ExtractedFolder.FullName "bin") -Destination $InstallDir
        Remove-Item -Path "$InstallDir-temp" -Recurse -Force
        Write-Host "   -> Arquivos extraidos com sucesso." -ForegroundColor Green
    } else {
         Write-Host "[PASSO 3/4] Pasta 'bin' do FFmpeg ja existe." -ForegroundColor Green
    }

    # 4. Adiciona o FFmpeg ao PATH do Sistema
    Write-Host "[PASSO 4/4] Adicionando ao PATH do sistema..."
    $SystemPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    if (-not $SystemPath.Contains($BinPath)) {
        $NewPath = "$SystemPath;$BinPath"
        [System.Environment]::SetEnvironmentVariable("Path", $NewPath, "Machine")
        Write-Host "   -> FFmpeg adicionado ao seu PATH com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "   -> FFmpeg ja esta configurado no seu PATH." -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "================================================="
Write-Host "Instalacao concluida com sucesso!" -ForegroundColor Green
Write-Host "IMPORTANTE: Feche e reabra TODOS os terminais para que a alteracao tenha efeito." -ForegroundColor Yellow
Write-Host "================================================="
Read-Host -Prompt "Pressione Enter para fechar"
