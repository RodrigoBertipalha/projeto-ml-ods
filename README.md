# Previsão de risco de desmatamento na Caatinga (ODS 15)

Projeto Integrador de Machine Learning — FACAPE, 2026.2.

## Configuração (uma vez por clone)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
git config core.hooksPath .githooks   # ativa o bloqueio de arquivos > 20 MB no commit
```

Os dados (`data/raw/`, `data/interim/`, `data/processed/`) nunca são versionados.
