# Instalador e portátil — EcoDeck 0.2

O build completo é `python scripts/build.py`. Gera EXE onedir, ZIP portátil,
instalador NSIS e SHA256SUMS.txt. Para só o ZIP, use `--portable-only`.

O NSIS 3.11 é baixado do projeto oficial no SourceForge para `.tools/`.
O SHA-256 fixado em `scripts/build_installer.py` é conferido antes da extração.
Não há instalação global do compilador. A compilação não precisa de administrador.

O instalador usa RequestExecutionLevel user e instala por padrão em
%LOCALAPPDATA%\Programs\EcoDeck. Todas as entradas de registro pertencem à conta:
Uninstall\EcoDeck em HKCU e, se selecionado, Run\EcoDeck. Menu Iniciar é sempre
criado; atalho de Desktop começa selecionado, autostart começa desmarcado.
Na atualização, uma entrada de autostart desta instalação pode ser mantida marcada.

Feche o EcoDeck pela bandeja antes de atualizar/desinstalar. A desinstalação usa
uma lista gerada dos arquivos distribuídos e remove somente diretórios vazios.
Não há RMDir /r da instalação e o perfil %LOCALAPPDATA%\EcoDeck é preservado.

O portátil inclui criar-atalho.bat e criar-atalho.ps1. O PowerShell usa o Known
Folder DesktopDirectory do Windows, respeitando redirecionamento ao OneDrive.
O parâmetro -DesktopDirectory existe para QA: não é preciso usá-lo normalmente.

O ICO versionado em assets/EcoDeck.ico contém nove imagens PNG, de 16 a 256 px,
geradas pelo mesmo desenho da bandeja. Para regenerar: python scripts/make_icon.py.

## Testes

O build roda scripts/smoke_installer.py. O instalador recebe /S /QA /D=<temporário>.
Esse modo extrai os arquivos e gera o desinstalador, mas não escreve atalhos,
entrada em Aplicativos instalados nem início automático da conta.
O EXE extraído executa o smoke sem áudio. Depois o teste desinstala e confirma
a preservação de um arquivo extra. O atalho portátil é criado e inspecionado
apenas em um diretório Desktop QA temporário. Nenhum pressionamento é simulado.

Ainda conferir interativamente as páginas do instalador, a exibição em Aplicativos
instalados, os atalhos reais, login Windows e desinstalação pela interface.
O aviso SmartScreen depende de reputação/política do Windows e não é emulado pelo QA.

O destino QA também é obrigatório na variável ECODECK_INSTALLER_QA_DIR, fornecida
pelo script de teste ao processo filho. Sem ela, /QA aborta antes de copiar arquivos.
