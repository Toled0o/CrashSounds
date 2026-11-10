# Estado atual — CrashSounds

Atualizado em 10/11/2026. Versão 0.3.0 publicada como pré-release.
Repositório: https://github.com/Toled0o/CrashSounds.
Checkout desta sessão: D:\EcoDeck (mantido para não quebrar o ambiente virtual).
É o mesmo projeto antes chamado EcoDeck, com histórico e releases preservados.

## Produto

Soundboard local Windows com biblioteca MP3/WAV/OGG/FLAC, categorias, favoritos,
busca, atalhos globais, volumes e reprodução em fones + cabo virtual. Captura
opcional do microfone somente para a saída virtual. Temas, bandeja, início opt-in
e importação/exportação JSON portátil. Sem rede, conta, telemetria ou driver próprio.

Instalador NSIS por usuário sem administrador, Desktop/Menu Iniciar e opção de
autostart. ZIP portátil com criar-atalho.bat/ps1. ICO de nove resoluções.
Documentação de build e testes em INSTALLER.md e TESTING.md.

## Renomeação 0.3

Nome visível, EXE, ícone, instalador, atalhos, banner, links e artifacts:
CrashSounds. O módulo Python e o formato de backup mantêm o identificador ecodeck.
Perfil permanece %LOCALAPPDATA%\EcoDeck; biblioteca e trava mantidas, sem mover
ou copiar dados. Backups antigos continuam aceitos. Novos exports usam extensão
.crashsounds.json. Não ler dados pessoais para testar compatibilidade.

A identidade de desinstalação HKCU Uninstall\EcoDeck é estável para reconhecer
a instalação anterior. DisplayName agora é CrashSounds. O instalador remove
binário/atalhos legados somente quando InstallLocation corresponde à pasta alvo.
A opção de autostart é preservada quando a entrada antiga aponta ao app instalado.
A chave Run atual é CrashSounds; aliases legados são tratados só quando pertencem
ao próprio executável. Não excluir chaves de outra instalação.

## Validação

59 testes locais passaram, com diretórios temporários, sons sintéticos, dispositivos
falsos e registro de hotkey em janela oculta. Ruff passou. Novos testes cobrem
perfil legado e autostart sem gravar no registro real.

Build 0.3 e smoke do instalador concluídos: EXE instalado, desinstalação preservando
arquivo extra, atalho CrashSounds.lnk e ícone corretos em Desktop QA.
Prévia da interface CrashSounds inspecionada nos dois temas.
Publicação 0.3: https://github.com/Toled0o/CrashSounds/releases/tag/v0.3.0. As versões 0.1 e 0.2 passaram em Actions; a 0.2 validou
instalação/desinstalação QA e atalho portátil com destino/ícone corretos.
O QA do instalador exige ECODECK_INSTALLER_QA_DIR no processo filho, sem fallback
para a pasta padrão, e não grava atalhos reais, Run ou entrada de desinstalação.

## Pendências

Validar auditivamente headset, cabo, Discord/jogos, latência e desconexões.
Conferir interativamente telas/atalhos/login e atualização de instalação real 0.2.
Gravador, normalização, instalador assinado e sincronismo de amostra não estão
entregues. As duas saídas têm relógios independentes. Desativar áudio encerra
captura; parar sons mantém a voz se a mixagem estiver ativa.

## Próximo comando seguro

git status --short
.venv\Scripts\python.exe -m pytest -q

Somente este soundboard está autorizado para commits/push/releases.
Não versionar nem alterar o painel de buffet como consequência deste trabalho.

## Publicação confirmada

Workflow 0.3 concluído com sucesso, incluindo 59 testes e QA do instalador:
https://github.com/Toled0o/CrashSounds/actions/runs/42852396451.
Instalador CrashSounds-0.3.0-setup.exe, ZIP CrashSounds-windows-x64.zip,
SHA256SUMS.txt e BUILD_TOOLS.json anexados à release.
