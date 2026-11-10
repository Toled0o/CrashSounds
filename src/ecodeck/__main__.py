# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
import os
import sys
import traceback
from pathlib import Path


def dispatch():
    if "--download-worker" in sys.argv:
        from ecodeck.download_worker import main
    else:
        from ecodeck.app import main
    return main()


if __name__ == "__main__":
    try:
        exit_code = dispatch()
    except Exception:
        if "--smoke-test" not in sys.argv and "--download-worker" not in sys.argv:
            raise
        # QA/worker não podem abrir um diálogo modal de erro do bootloader.
        details = traceback.format_exc()
        destination = os.environ.get("CRASHSOUNDS_QA_LOG")
        if destination:
            Path(destination).write_text(details, encoding="utf-8")
        if sys.stderr is not None:
            sys.stderr.write(details)
        exit_code = 1
    raise SystemExit(exit_code)
