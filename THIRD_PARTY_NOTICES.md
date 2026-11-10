# Créditos e dependências

O código original do **EcoDeck** é de Murilo Siqueira Toledo, 2026, sob a licença MIT.
Soundpad é um produto de terceiros; não há afiliação, cópia de código, marca ou assets.
Nenhum pacote de sons protegido acompanha o aplicativo.

As bibliotecas mantêm suas próprias licenças. A distribuição inclui cópias dos
avisos disponíveis nos pacotes em `licenses/`, um inventário em `DEPENDENCIES.json`
e os textos LGPL/GPL aplicáveis. O código do EcoDeck permanece MIT.

| Componente | Licença / origem do código-fonte |
| --- | --- |
| Python | PSF — https://www.python.org/downloads/source/ |
| PySide6 Essentials / Shiboken6 | LGPLv3 (opção open source) — https://code.qt.io/cgit/pyside/pyside-setup.git/ |
| Qt Core, Gui, Widgets e plugins | LGPLv3 e avisos de terceiros — https://code.qt.io/cgit/qt/qtbase.git/ |
| NumPy | BSD-3-Clause e avisos inclusos — https://github.com/numpy/numpy |
| sounddevice | MIT — https://github.com/spatialaudio/python-sounddevice |
| PortAudio | MIT — https://github.com/PortAudio/portaudio |
| SoundFile | BSD-3-Clause — https://github.com/bastibe/python-soundfile |
| libsndfile | LGPL-2.1-or-later e codecs externos — https://github.com/libsndfile/libsndfile |
| python-soxr / SoXR | LGPL-2.1-or-later — https://github.com/dofuuz/python-soxr e https://sourceforge.net/projects/soxr/ |
| CFFI / pycparser | MIT / BSD-3-Clause — https://github.com/python-cffi/cffi e https://github.com/eliben/pycparser |
| PyInstaller (bootloader) | GPL com exceção para aplicativos empacotados — https://github.com/pyinstaller/pyinstaller |

As versões exatas testadas estão em `requirements-dev.lock`; o inventário da
distribuição registra também a versão de libsndfile. Fontes correspondentes podem
ser obtidas pelas tags da versão nos projetos acima e pelos arquivos oficiais:
https://download.qt.io/official_releases/QtForPython/ e https://download.qt.io/archive/qt/.

O aplicativo usa DLLs compartilhadas, sem alterações nas bibliotecas LGPL.
O formato de distribuição é **onedir**: mantenha a pasta `_internal` junto ao EXE.
Você pode modificar o EcoDeck, substituir bibliotecas compatíveis e reconstruir
o pacote com as instruções do README. Não há bloqueio técnico nem proibição de
engenharia reversa para depurar alterações dessas bibliotecas. Preserve os avisos
e disponibilize as fontes e alterações correspondentes ao redistribuir versões.
Consulte as [obrigações LGPL publicadas pelo Qt](https://www.qt.io/development/open-source-lgpl-obligations).

O driver **VB-CABLE** não é incluído, instalado nem modificado pelo EcoDeck.
É um produto externo da VB-Audio, distribuído como donationware, com condições
próprias: https://vb-audio.com/Services/licensing.htm. O EcoDeck não exige conta
ou pagamento, mas não altera a licença de drivers externos.
