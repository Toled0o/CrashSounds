# Como contribuir

Abra uma issue contando o que você tentou, o esperado e o que aconteceu.
Informe Windows, versão do EcoDeck e nomes dos dispositivos; não envie sons
privados, gravações de terceiros sem permissão ou sua biblioteca pessoal.

Para código: crie uma branch, prepare o ambiente do README, altere só o necessário
e rode `python -m pytest -q` e `python -m ruff check .`. Mudanças no áudio precisam
preservar o isolamento entre voz e monitor e os limites de memória.

Use commits como `feat: adiciona repetição de som` ou `fix: trata headset desconectado`.
Atualize o changelog e mantenha o cabeçalho de copyright nos arquivos de código.
Contribuições são disponibilizadas sob a licença MIT do projeto; dependências
mantêm suas próprias licenças. Consulte `docs/TESTING.md` antes de testes auditivos.
