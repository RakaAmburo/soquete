# soquete

Servicio WebSocket en Python (picows) con autenticación, procesamiento desacoplado y mensajes salientes desde el backend.

## Setup

```bash
cd /home/pablo/repos/soquete
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # editar AUTH_KEY
```

## Correr

```bash
python main.py
# o con PM2:
pm2 start ecosystem.config.js
pm2 save
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Configuración (.env)

| Variable   | Default     | Descripción              |
|------------|-------------|--------------------------|
| WS_HOST    | 0.0.0.0     | Interfaz de escucha      |
| WS_PORT    | 18690       | Puerto WebSocket         |
| AUTH_KEY   | changeme    | Clave de autenticación   |
| LOG_LEVEL  | INFO        | Nivel de log             |

## Protocolo

1. Cliente conecta
2. Cliente envía `{"key": "<AUTH_KEY>"}`
3. Servidor responde `{"msg": "authenticated"}`
4. Cliente envía `{"msg": "texto"}`
5. Servidor responde `{"msg": "mensaje recibido"}`

Mensajes salientes (backend → cliente): el servidor puede enviar `{"msg": "..."}` en cualquier momento vía `OutboundBus.send()`.
