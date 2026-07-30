@echo off
rem ATLAS - Claude Code CLI baslatici (opencode_Run.cmd / kilo_Run.cmd kalibi).
rem Claude Code AI cekirdegi tasinabilirlik istisnasidir: gomulmez, ayri kurulur
rem (npm install -g @anthropic-ai/claude-code), hesap kullanicinin ~/.claude'unda.
rem Bu launcher yalniz bin'i bulur, PATH'e ATLAS koku ekler, %H%'de calistirir.
setlocal enableextensions

set "H=%~dp0"

rem --- Bin arama: env override -> where PATH ---
set "CLAUDE_BIN="

if defined ATLAS_LLM_CLAUDE_BIN set "CLAUDE_BIN=%ATLAS_LLM_CLAUDE_BIN%"
if defined CLAUDE_BIN if not exist "%CLAUDE_BIN%" goto :bad_override

if not defined CLAUDE_BIN call :find_bin claude
if not defined CLAUDE_BIN call :find_bin claude.cmd
if not defined CLAUDE_BIN goto :not_found

rem --- ATLAS launcher'lari PATH'e (claude oturumundan atlas komutlari cagirilabilsin) ---
set "PATH=%H%;%PATH%"

rem --- Calisma dizini depo koku (Claude Code CLAUDE.md'yi buradan okur) ---
cd /d "%H%"

"%CLAUDE_BIN%" %*
exit /b %ERRORLEVEL%

:find_bin
for /f "delims=" %%G in ('where %1 2^>nul') do if not defined CLAUDE_BIN set "CLAUDE_BIN=%%G"
exit /b 0

:bad_override
echo [HATA] ATLAS_LLM_CLAUDE_BIN=%ATLAS_LLM_CLAUDE_BIN% dosya degil.
exit /b 1

:not_found
echo [HATA] claude bulunamadi. Cozum yollari:
echo   1. npm install -g @anthropic-ai/claude-code
echo   2. PATH'e ekle
echo   3. ATLAS_LLM_CLAUDE_BIN=^<mutlak yol^> ile isaret et
exit /b 1
