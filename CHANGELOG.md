# Changelog

Mudanças relevantes do EcoDeck. Versões seguem Semantic Versioning.

## [0.1.0] — 2026-11-10

Primeira versão para teste no Windows.

### Adicionado

- Biblioteca local MP3/WAV/OGG/FLAC, categorias, favoritos e busca.
- Saída simultânea para fones e dispositivo virtual, com captura de voz opcional.
- Volumes geral/individual, parar sons e atalhos globais Win32.
- Temas claro/escuro, bandeja e inicialização automática opt-in.
- Exportação/importação portátil em JSON, validação e persistência atômica.
- Build Windows x64, testes isolados e workflows de qualidade/release.

### Limitações conhecidas

- Gravador não incluído nesta versão.
- Dois dispositivos físicos não são sincronizados em nível de amostra.
- Dispositivos precisam aceitar estéreo/48 kHz nas saídas e mono/48 kHz na captura.
- Aplicativo e executável ainda precisam de teste auditivo no headset/cabo/Discord.
- Executável sem assinatura digital; confira a origem e o SHA-256.
