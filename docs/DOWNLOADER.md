# Baixar por link — CrashSounds 0.4

Na lateral do app, abra **Baixar por link** e cole um endereço HTTPS de um vídeo
público. Nada é consultado antes de clicar em Baixar.

- **Salvar vídeo MP4:** escolha até 360p, 720p ou 1080p e o arquivo de destino.
  O site precisa disponibilizar um formato compatível nessa resolução.
- **Trecho de áudio para a biblioteca:** informe início em segundos, duração
  máxima (1–120 s) e categoria. Ao concluir, um WAV estéreo/48 kHz entra na
  biblioteca com o título do vídeo. Nenhuma reprodução acontece automaticamente.
- Acompanhe progresso e velocidade. Cancelar encerra o worker e seus processos
  FFmpeg/Node; arquivos temporários são removidos. Parar sons não cancela downloads.

## Limites e disponibilidade

Um vídeo individual por vez; sem playlists ou lives. Fontes de até uma hora,
vídeo final até 1 GiB, fonte de áudio até 256 MiB e trabalho de até 15 minutos.
O arquivo fonte do áudio pode ser baixado por inteiro antes de recortar.
Conversão/merge podem exigir espaço temporário além do arquivo final.

yt-dlp fornece os extratores. Não há garantia para qualquer site/link: login,
restrições do site, formatos indisponíveis, bloqueios e mudanças de plataforma
podem impedir o download. Esta versão não lê cookies do navegador, senhas,
netrc ou contas e não oferece desbloqueio de conteúdo protegido. Atualize o
CrashSounds quando um extrator precisar de correção. Não há auto-update silencioso.

O app acessa o site e seus servidores de mídia somente durante a solicitação.
A URL não é gravada em um histórico pelo CrashSounds. O título/arquivo importados
ficam na biblioteca, conforme a escolha do usuário. Sons locais continuam offline.
Use conteúdo que você tenha permissão para baixar e compartilhar.

## Arquitetura e manutenção

- download_types.py: valida URL, modo, tamanho, duração e local das ferramentas.
- download_worker.py: usa yt-dlp com EJS local e ferramentas fixadas. Não importa Qt.
- download_client.py: executa worker pelo mesmo EXE; IPC JSON UTF-8 por pipes,
  salvamento atômico, temporários no volume do destino e cancelamento.
- child_process.py: Windows Job Object com kill-on-close para os descendentes
  desta operação. Não usa encerramento genérico por nome de processo.
- download_ui.py: janela de links e importação do WAV na thread da interface.
- download_qa.py: cria mídia sintética, serve em loopback/porta efêmera e exercita
  vídeo, conversão e biblioteca com o worker real. Sem internet ou áudio audível.

No EXE windowed, sys.std* pode ser None: o worker recupera os handles herdados
dos pipes Win32. A falha de IPC retorna código de erro, sem abrir diálogo oculto.
O processo espera stdin antes de criar filhos, permitindo associá-lo ao job.

## Empacotamento

python scripts/prepare_media_tools.py baixa arquivos oficiais em .tools/, verifica
SHA-256 e prepara FFmpeg LGPL compartilhado e Node. Não instala nada globalmente.
As fontes, versões e hashes estão em scripts/media-tools.json e acompanham o
pacote como MEDIA_TOOLS.json. Licenças originais ficam junto das ferramentas.

O build inclui yt-dlp, EJS e dados JavaScript locais. Componentes remotos EJS e
busca de plugins no perfil/CWD estão desativados. NODE_OPTIONS/NODE_PATH não
são herdados pelo worker. Dependências Python estão fixadas no lockfile.

Para testar: prepare as ferramentas e rode pytest; --smoke-test do EXE repete
o fluxo completo com a fixture HTTP local. Sites públicos reais precisam de
validação manual, sem anunciar compatibilidade apenas pelo resultado do QA.
