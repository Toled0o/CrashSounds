# CrashSounds 0.4.1 — vídeos e sons a partir de links

Agora o CrashSounds tem **Baixar por link** na lateral.

- Cole um link HTTPS público e salve o vídeo MP4 na pasta escolhida.
- Ou extraia um trecho de até 120 segundos e adicione direto à biblioteca.
- Escolha resolução, início, duração e categoria; acompanhe progresso e velocidade.
- Cancele o download sem deixar processos de conversão rodando.
- yt-dlp, FFmpeg e Node já acompanham instalador e portátil.

Não há login, leitura de cookies do navegador ou telemetria. A rede é usada
quando você inicia o download. A compatibilidade depende do site e do vídeo;
lives, playlists e conteúdos que exigem login não são suportados.

Instale CrashSounds-0.4.1-setup.exe ou extraia o ZIP completo. O pacote ficou maior
por incluir as ferramentas de mídia; elas só rodam quando necessárias.
Consulte o README para limites, atalhos, cabo virtual e aviso SmartScreen.

Testes automatizados usam mídia sintética local, incluindo vídeo, áudio e
cancelamento de processos. Sites públicos e áudio no seu hardware seguem
como validações manuais. Esta versão permanece pré-release.

Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos
da licença MIT. Dependências mantêm suas próprias licenças.

Correção adicional: salvar vídeo aceita arquivos sem trilha de áudio. A opção de
extrair áudio continua validando a existência dessa trilha antes de converter.
