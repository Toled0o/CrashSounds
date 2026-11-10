# Plano de implementação — EcoDeck 0.1

1. Estrutura independente, licença MIT, modelo validado e persistência atômica.
2. Decodificação MP3/WAV/OGG/FLAC, resampling, mixer testável, dois destinos,
   captura de microfone opt-in e limites explícitos de memória/polifonia.
3. Interface Qt em português: biblioteca, categorias, favoritos, busca,
   edição, dispositivos, temas, importação/exportação e Sobre.
4. RegisterHotKey nativo, conflitos visíveis, parar tudo, bandeja e início opt-in.
5. Testes isolados, build PyInstaller onedir, documentação e workflow de release.

Decisões: Python 3.11–3.13; PySide6 Essentials para evitar WebEngine;
PortAudio/sounddevice em modo compartilhado a 48 kHz; soundfile/libsndfile
para decodificação; soxr para conversão de taxa. Não há servidor, conta,
telemetria, download de sons ou instalação automática de driver.

As duas saídas têm relógios distintos e não garantem sincronismo de amostra.
A fila da voz descarta dados antigos para evitar atraso crescente. Dispositivos
são persistidos por nome + host API, nunca por índices instáveis do PortAudio.
Não redirecionar silenciosamente um dispositivo ausente para outro.

Limites: 120 s por som, 64 MiB por arquivo, 128 MiB de cache de áudio e
16 vozes por destino. Exportação portátil JSON inclui os arquivos em base64
(limite acumulado de 128 MiB de originais); importação substitui a biblioteca
somente depois de validar tudo e pede confirmação na interface.

Gravador fica no roadmap. Captura para misturar a voz ao cabo está incluída.
O projeto não modifica o driver de microfone, jogos ou configurações do Discord.
