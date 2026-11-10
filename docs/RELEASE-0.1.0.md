# EcoDeck 0.1.0 — primeira pré-release

Soundboard livre para Windows, criado por Murilo Siqueira Toledo, com código MIT.

- Biblioteca MP3/WAV/OGG/FLAC, busca, favoritos e categorias.
- Atalhos globais, volumes e reprodução em fones + cabo virtual.
- Mistura opcional de microfone real, temas, bandeja e início com Windows opt-in.
- Backup portátil em JSON com os arquivos de áudio.

**Como usar:** baixe `EcoDeck-windows-x64.zip`, extraia toda a pasta e abra
`EcoDeck.exe`. Mantenha `_internal` junto do executável. Não precisa de Python.
O guia do cabo virtual e os passos para desenvolver estão no README.

**Validação:** 49 testes locais, Ruff, QA nos dois temas e teste do EXE com os quatro
codecs passaram. O workflow Qualidade também passou no GitHub Actions.

**Ainda precisa de teste no seu hardware:** headset + VB-CABLE + Discord, latência,
atalhos em jogos, desconexão e início ao entrar no Windows. Gravador não incluído.
O EXE não tem assinatura digital. Confira a origem e `SHA256SUMS.txt`.
O driver VB-CABLE é externo, donationware e não acompanha o aplicativo.

Ao abrir o app, o áudio começa desligado. Ative nas preferências após escolher os
dispositivos. Parar sons mantém sua voz; Desativar áudio encerra a captura.

Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos
da licença MIT. Dependências mantêm suas próprias licenças.
