# Remote Access V1

## Current decision

Remote access is enabled at the **Web edge**, not by publishing infrastructure ports.

Target:

```text
Internet
   |
 HTTPS
   v
Reverse Proxy
   |
   v
Laravel Web 127.0.0.1:8001
   |
   | server-to-server token
   v
FastAPI Agent 127.0.0.1:8000
   |
   +-- PostgreSQL 127.0.0.1:5433
   +-- Qdrant 127.0.0.1:6333
   +-- Ollama 127.0.0.1:11434
```

## Important boundary

The current Agent credential is a server-to-server secret for Laravel -> Agent. It must not be embedded in Flutter or browser code.

Therefore Remote Access V1 publishes Laravel Web only.

A future Flutter direct-to-Agent flow requires a separate user/client authentication contract (for example OAuth2/OIDC or another short-lived user token model) before the Agent endpoint is published directly.

## Reverse proxy

The repository includes `deploy/Caddyfile.example`.

The reverse proxy should:

- terminate HTTPS;
- forward only to Laravel Web;
- preserve the original host/scheme as required by Laravel;
- never expose PostgreSQL, Qdrant or Ollama;
- never expose the Laravel -> Agent server token.

## DNS / firewall

The machine hosting the Local Server must have a stable reachable path from the Internet, either through:

- router port forwarding to HTTPS;
- a secure tunnel;
- VPN/private network;
- another controlled ingress.

The specific provider is not selected yet.

## Local verification before enabling remote

1. Laravel `/up` returns HTTP 200 locally.
2. Laravel Chat Test works locally.
3. Laravel -> Agent works locally.
4. Agent `/health/dependencies` is healthy.
5. PostgreSQL/Qdrant/Ollama remain bound to localhost.
6. The reverse proxy can reach Laravel on `127.0.0.1:8001`.
7. Google OAuth redirect URI is changed to the final HTTPS URL before using Google login remotely.

## Security rule

Do not enable remote access by changing Docker ports to `0.0.0.0`. Infrastructure remains localhost/private.
