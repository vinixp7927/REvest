# Iniciar o projeto no Windows (um passo)
- Dê **duplo clique** no arquivo `start.bat`
  - Ele vai criar a `venv` automaticamente (se não existir), instalar as dependências,
    criar uma SECRET_KEY temporária e **iniciar** o servidor Flask.
- Alternativamente, você pode rodar o `start.ps1` no PowerShell (mesma função).

## Comandos manuais (opcional)
```powershell
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
$env:SECRET_KEY = $([guid]::NewGuid().ToString())
python app.py
```

## Produção
- Defina `SESSION_COOKIE_SECURE=True` no `app.py` e rode com HTTPS.
- Defina `SECRET_KEY` forte via variável de ambiente do seu sistema/servidor.


**ATUALIZAÇÃO:** Agora o launcher usa **apenas .BAT/.CMD** (nada de PowerShell). Dê duplo clique em `start.bat` ou `start.cmd`.
