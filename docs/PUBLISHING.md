# GitHub, releases e continuidade

Repositório: **https://github.com/Toled0o/CrashSounds**. O painel de buffet não faz parte dele.

## Publicar a primeira vez

Para uma cópia sem remoto (se já publicado, confira `git remote -v` e não recrie):

```powershell
cd D:\EcoDeck
git status --short
git init -b main
git add .
git diff --cached --stat
git commit -m "feat: cria primeira versão do CrashSounds"
gh auth login
gh repo create Toled0o/CrashSounds --public --source . --remote origin --push
```

Execute somente dentro do CrashSounds, nunca no painel. Ambiente virtual, sons,
dados, capturas QA, cache e builds ficam fora do Git. Use a identidade configurada.

## Publicar uma release

1. Atualize `version` em `pyproject.toml`, `__version__` em `src/ecodeck/__init__.py`,
   badge no README e changelog. O workflow valida a tag contra `__version__`.
2. Rode `python -m pytest -q`, `python -m ruff check .` e `python scripts/build.py` (inclui instalador, portátil e QA de desinstalação)
   no ambiente virtual. Faça o checklist auditivo antes de anunciar estabilidade.
3. Commit e `git push origin main`.
4. Publique uma release com a tag correspondente, por exemplo:

```powershell
gh release create v0.4.1 --target main --title "CrashSounds 0.4.1" --notes-file docs/RELEASE-0.4.1.md --prerelease
```

O workflow `release: published` anexa o instalador `*-setup.exe`, o ZIP, o SHA-256
e o inventário do compilador NSIS. O ZIP inclui os scripts de criação de atalho. Mantenha a primeira versão
como pré-release enquanto faltarem testes auditivos. Confira o resultado na aba
Actions: existir uma release não significa que o build passou.
Execução manual do workflow gera artifacts sem criar release.

## Continuar em outra sessão

```powershell
git clone https://github.com/Toled0o/CrashSounds.git
cd CrashSounds
git switch main
```

Depois siga o README. Envie uma mensagem como:

> Continue o CrashSounds em https://github.com/Toled0o/CrashSounds, branch main.
> Leia AGENTS.md e docs/STATUS.md. Quero alterar: [...].

Em cópia existente, confira alterações antes de `git pull --ff-only`.
Se for privado, conecte uma conta com acesso. Nunca envie tokens, o perfil real
de `%LOCALAPPDATA%\EcoDeck` ou sons pessoais para o repositório.

O checkout desta sessão permanece em D:\EcoDeck por compatibilidade com o ambiente
virtual. Novas clonagens podem usar a pasta CrashSounds normalmente.
