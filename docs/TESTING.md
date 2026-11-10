# Validação do EcoDeck

## Automatizada, sem áudio real

`python -m pytest -q` usa diretórios temporários e sons sintéticos. Streams são
substituídos por dispositivos falsos. A interface roda offscreen, sem bandeja ou
hotkeys registrados. O teste específico Win32 usa um subprocesso com janela
oculta real e registra temporariamente Ctrl+Alt+Shift+F11; entrega uma mensagem
à própria janela, sem simular pressionamentos. Remove o registro ao encerrar.

Comportamentos testados: quatro formatos e resampling; volumes e sobreposição;
fim de voz e polifonia; fila de microfone limitada; voz isolada dos fones;
clipping; falha parcial e ausência de dispositivo sem fallback; cancelamento de
reprodução pendente; cache limitado; persistência atômica; exportação portátil;
JSON/paths/base64 inválidos; atalhos inválidos/duplicados; filtros e dois temas.

`python -m ecodeck --smoke-test --screenshot qa-artifacts/preview.png` cria um
perfil temporário e salva os dois temas. Não toca, grava, instala drivers,
registra atalhos ou modifica a inicialização. O build repete o QA dentro do EXE.

## Checklist manual no Windows — ainda necessário

Use volume baixo e perfil fictício:
`python -m ecodeck --data-dir qa-artifacts/perfil-manual`.
No pacote: `EcoDeck.exe --data-dir C:\caminho\qa-ecodeck`.

- [ ] Abrir o pacote em Windows x64 sem Python instalado.
- [ ] Ouvir um arquivo real de cada formato, do início ao fim.
- [ ] Receber o som nos fones e no teste de entrada do Discord pelo cabo virtual.
- [ ] Misturar voz e confirmar que não retorna nos fones.
- [ ] Ajustar volumes durante reprodução e sobrepor sons.
- [ ] Usar atalhos minimizado, com outro app em foco; parar todos os sons.
- [ ] Conferir aviso de conflito de atalho e comportamento nos jogos usados.
- [ ] Desconectar headset durante playback e conferir reativação manual.
- [ ] Exportar/importar em outro perfil; conferir nomes, arquivos e favoritos.
- [ ] Habilitar início com Windows, sair/entrar na conta e conferir bandeja,
      áudio desligado e ausência de captura automática. Desmarcar depois do teste.
- [ ] Sair pela bandeja e confirmar liberação de dispositivos e atalhos.
- [ ] Anotar latência percebida e alertas de áudio.

QA não certifica desempenho em hardware real. Screenshot não demonstra driver
instalado nem que o Discord recebeu áudio.
