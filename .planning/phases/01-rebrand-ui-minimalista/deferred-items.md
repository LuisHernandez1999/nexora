# Deferred Items — Phase 01

Out-of-scope discoveries found during execution. NOT fixed (pre-existing, unrelated to plan tasks).

## 01-01

- **`debug_toolbar` não instalado no ambiente dev.** `python manage.py check` (settings dev) falha com `ModuleNotFoundError: No module named 'debug_toolbar'`. É dependência declarada em `config/settings/dev.py` mas ausente no venv local. Verificação do plano rodada com `--settings=config.settings.prod` (que carrega o `base.py` modificado) — passa sem erros. Pré-existente, não causado pelas mudanças de rebrand. Sugestão: `pip install django-debug-toolbar` ou tornar o import opcional em dev.py.
