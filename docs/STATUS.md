# Estado atual — EcoDeck

Atualizado em 10/11/2026. Projeto independente, repositório Toled0o/EcoDeck.
Versão 0.1.0, primeira entrega para testes (pré-release).

## Implementado

Biblioteca local com cópias de arquivos e JSON atômico; MP3/WAV/OGG/FLAC;
categorias, favoritos, busca e edição; mixer estéreo a 48 kHz com dois destinos;
voz real apenas na saída virtual; volumes, cancelamento de playback pendente;
atalhos RegisterHotKey; bandeja, início opt-in e temas. Exportação JSON portátil
inclui áudios; importação valida e não ativa captura ou autostart vindo do pacote.

Sem gravador nesta versão. Sem servidor, rede, telemetria, conta ou driver próprio.
VB-CABLE é externo e tem licença donationware; o código original é MIT.

## Arquitetura

- `models.py` valida estado, nomes, limites, caminhos e conflitos de atalhos.
- `storage.py` faz cópia de mídia, commit atômico e import/export transacional.
- `audio.py` contém mixers testáveis, buffer limitado de voz, cache LRU,
  resampling SoXR e adaptadores sounddevice. Decodificação fora da thread UI.
- `hotkeys.py` e `startup.py` encapsulam Win32 e Run do usuário, sem admin.
- `ui.py` é a janela Qt; `app.py` trata perfil, instância única e argumentos.
- `qa.py` exercita interface e codecs com dados temporários, sem abrir áudio.

Saídas têm relógios independentes. Não prometer sincronismo de amostra ou latência
fixa. Não fazer fallback de dispositivo ausente. Streams iniciam somente por
ação explícita; abrir na bandeja não captura automaticamente.

## Validação local

- Python 3.13.5, Windows 11 x64; dependências e hashes em `requirements-dev.lock`.
- 49 testes passaram, incluindo quatro formatos, persistência, roteamento falso,
  filtros/temas e registro de hotkey Win32 em janela oculta com mensagem sintética.
  Não foram injetadas teclas nem reproduzido/capturado áudio real.
- Ruff passou e código foi formatado.
- Primeiro build PyInstaller onedir e smoke do EXE passaram; ZIP aproximadamente
  50 MiB. Build final e publicação são verificados na etapa de entrega.
- Capturas QA nos temas claro/escuro foram inspecionadas. Não são prova auditiva.

## Pendências reais

Checklist de hardware em `TESTING.md`: ouvir no headset, receber no Discord,
misturar voz, medir latência, jogar minimizado, testar desconexões e login Windows.
Não marcar como estável antes disso. Gravador, normalização, instalador e assinatura
digital ficam no roadmap. Arquivos removidos da lista ficam órfãos no perfil para
recuperação manual; ocupam disco. Cache de áudio limitado não é limite de RAM total.

## Próximo comando seguro

```powershell
git status --short
.\.venv\Scripts\python.exe -m pytest -q
```

Não usar sons ou perfil pessoal nos testes. Preserve o copyright por arquivo.
Não alterar painel de buffet ou publicar dados reais como efeito deste projeto.
