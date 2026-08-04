<#
.SYNOPSIS
  SPEC 048: ATLAS vault backup Windows Task Scheduler kurulumu.

.DESCRIPTION
  Bu betik `atlas-vault-backup.xml` şablonunu placeholder'ları doldurup
  `schtasks /Create` ile kurar. Task Scheduler'da "\ATLAS\Vault Backup"
  altında görünür.

.PARAMETER Keep
  Retention (kaç yedek tutulacak). Varsayılan: 30.

.PARAMETER RepoRoot
  ATLAS git repo kökü. Varsayılan: betik dizininden 2 üst.

.PARAMETER AtlasBin
  `atlas.exe` mutlak yolu. Varsayılan: `Get-Command atlas` sonucu.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -Keep 14
#>
[CmdletBinding()]
param(
    [int]$Keep = 30,
    [string]$RepoRoot = $null,
    [string]$AtlasBin = $null
)

$ErrorActionPreference = "Stop"

if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
if (-not $AtlasBin) {
    $atlasCmd = Get-Command atlas -ErrorAction SilentlyContinue
    if (-not $atlasCmd) {
        Write-Error "HATA: 'atlas' PATH'te bulunamadi. Once ATLAS'i kur: uv pip install -e $RepoRoot"
        exit 1
    }
    $AtlasBin = $atlasCmd.Source
}

$ArchiveRoot = Join-Path $RepoRoot "archive"

$TemplatePath = Join-Path $PSScriptRoot "atlas-vault-backup.xml"
if (-not (Test-Path $TemplatePath)) {
    Write-Error "Sablon dosyasi yok: $TemplatePath"
    exit 1
}

$xml = Get-Content -Raw -Encoding Unicode -Path $TemplatePath
$xml = $xml.Replace("__ATLAS_BIN__",    $AtlasBin)
$xml = $xml.Replace("__ARCHIVE_ROOT__", $ArchiveRoot)
$xml = $xml.Replace("__REPO_ROOT__",    $RepoRoot)
$xml = $xml.Replace("__KEEP__",         $Keep.ToString())

$TempXml = Join-Path $env:TEMP "atlas-vault-backup.xml"
[System.IO.File]::WriteAllText($TempXml, $xml, [System.Text.Encoding]::Unicode)

# Var olan gorevi sil (idempotent)
$null = schtasks /Delete /TN "ATLAS Vault Backup" /F 2>$null

# Yeni gorevi kur
$rc = schtasks /Create /TN "ATLAS Vault Backup" /XML "$TempXml"
if ($LASTEXITCODE -ne 0) {
    Write-Error "schtasks /Create basarisiz: exit $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "OK: 'ATLAS Vault Backup' gorevi kuruldu." -ForegroundColor Green
Write-Host "  repo:      $RepoRoot"
Write-Host "  atlas:     $AtlasBin"
Write-Host "  archive:   $ArchiveRoot"
Write-Host "  keep:      $Keep"
Write-Host "  schedule:  gunluk 03:00 UTC (+-10 dk jitter)"
Write-Host ""
Write-Host "Durum:        schtasks /Query /TN 'ATLAS Vault Backup' /V /FO LIST"
Write-Host "Manuel tetik: schtasks /Run   /TN 'ATLAS Vault Backup'"
Write-Host "Kaldirma:     schtasks /Delete /TN 'ATLAS Vault Backup' /F"

Remove-Item $TempXml -Force
