# Estado atual — CrashSounds

Atualizado em 10/11/2026. Versão 0.4.1 em preparação para pré-release.
Repositório: https://github.com/Toled0o/CrashSounds.
Checkout desta sessão: D:\EcoDeck, mantido para compatibilidade do ambiente virtual.

## Produto

Soundboard Windows com biblioteca MP3/WAV/OGG/FLAC, categorias, favoritos, busca,
atalhos, volumes, dois destinos e captura opcional de microfone para cabo virtual.
Temas, bandeja, autostart opt-in e backup JSON portátil. Instalador NSIS por
usuário e ZIP com criar-atalho.bat. Sem anúncios, conta ou telemetria.

## Links 0.4

Baixar por link abre uma janela modeless. Vídeo MP4 até 360/720/1080p ou trecho
WAV de 1–120 s para a biblioteca, com início e categoria. Progresso, velocidade,
cancelamento e abrir pasta. Nenhuma reprodução/captura é iniciada pelo download.

A biblioteca continua offline. Rede somente após o clique em Baixar, para o site
e seus servidores de mídia. Sem cookies do navegador/netrc/contas ou componentes
remotos EJS. URLs não são persistidas em histórico do aplicativo.

Worker separado pelo mesmo EXE, antes de importar Qt; pipes JSON UTF-8 com
recuperação dos handles no build windowed. Windows Job Object encerra apenas
o worker e descendentes desta operação. Temporários no volume do destino,
commit atômico do arquivo, importação de áudio em uma só transação JSON.
Um vídeo individual; sem lives/playlists; até 1 hora, 1 GiB de vídeo ou 256 MiB
de fonte de áudio, 15 min por trabalho. Fonte pode ser baixada antes de recortar.

yt-dlp/EJS, FFmpeg LGPL compartilhado e Node ficam no pacote, executados sob demanda.
Versões/hashes/fontes em scripts/media-tools.json e requirements-dev.lock.
prepare_media_tools.py só baixa em .tools, sem instalação global. CI prepara
ferramentas antes da suíte e guarda os arquivos originais em cache por hash.
Guia técnico e limites em DOWNLOADER.md.

## Compatibilidade

Nome visível CrashSounds. Módulo Python/formato JSON mantêm ecodeck; perfil
%LOCALAPPDATA%\EcoDeck e trava preservados. Não mover dados nem ler perfil real
para montar contexto. Backup antigo aceito. AppId Uninstall\EcoDeck continua
estável; DisplayName/Run são CrashSounds. Upgrade trata legados só quando
InstallLocation/entrada Run pertencem à instalação. Mais em INSTALLER.md.

## Validação

104 testes passaram: áudio, biblioteca, UI, Win32 e downloads. Novos casos:
URLs/limites, arquivo anterior preservado em falha, path inesperado do worker,
protocolo inválido/timeout, cancelamento real com descendente, vídeo sintético
HTTP em loopback/porta efêmera, recorte e importação, UI sem rede antes do clique
e importação do título sem entrada parcial em erro.

Primeiro build 0.4 completo passou: smoke no EXE windowed e no EXE instalado,
vídeo + áudio + biblioteca usando fixture local, desinstalação QA e atalho.
Scripts EJS incluídos no pacote. Ajustes finais de contraste/campos por modo
foram testados e o build 0.4.0 foi publicado com sucesso. A 0.4.1 corrige vídeo
silencioso, com teste do caso também dentro do smoke do executável.

## Pendências reais

Links públicos dos sites utilizados precisam de teste manual. Não prometer
compatibilidade com qualquer site com base na fixture local; bloqueios, login
e mudanças de extrator podem impedir download. Testar rede lenta/cancelamento,
espaço, fechamento no download, headset/cabo/Discord/jogos e latência real.
Gravador, assinatura digital e sincronismo em nível de amostra não entregues.

## Próximo comando seguro

git status --short
.venv\Scripts\python.exe scripts/prepare_media_tools.py
.venv\Scripts\python.exe -m pytest -q

Somente o soundboard está autorizado para commits/push/releases.
Não alterar ou versionar o painel de buffet por consequência deste projeto.

Leitura de metadados do exemplo público do YouTube presente na documentação do
yt-dlp funcionou, com 597 s e 47 formatos. Nenhum vídeo real foi salvo nesse teste.
O fluxo completo permanece validado com fixtures locais; disponibilidade de
outros links/sites e conteúdo real precisam de validação manual.
Workflow 0.4.0: https://github.com/Toled0o/CrashSounds/actions/runs/42869424410.
