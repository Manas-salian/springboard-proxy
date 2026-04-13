# Springboard Proxy

HTTPS intercepting proxy built on [mitmproxy](https://mitmproxy.org/). Routes browser traffic through a local proxy, logs all requests/responses, and intercepts specific API responses for processing.

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
git clone <repo-url> && cd sprinboard-proxy
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Running

```bash
python proxy.py
```

Options:

| Flag | Default | Description |
|---|---|---|
| `-p`, `--port` | `9876` | Proxy listen port |
| `--listen-host` | `127.0.0.1` | Proxy listen host |
| `-q`, `--quiet` | off | Suppress mitmproxy event log |

### Browser Setup (FoxyProxy)

1. Install [FoxyProxy](https://addons.mozilla.org/en-US/firefox/addon/foxyproxy-standard/) in Firefox
2. Add a new proxy: **Type** HTTP, **Host** `127.0.0.1`, **Port** `9876`
3. Activate the proxy profile

### Trusting the CA Certificate (required for HTTPS)

With the proxy running and FoxyProxy active:

1. Navigate to **http://mitm.it**
2. Download and install the certificate for your OS/browser

Alternatively, import `~/.mitmproxy/mitmproxy-ca-cert.pem` manually:
- **Firefox**: Settings > Privacy & Security > Certificates > Import
- **System (Debian/Ubuntu)**:
  ```bash
  sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy.crt
  sudo update-ca-certificates
  ```

## Project Structure

```
sprinboard-proxy/
├── proxy.py                  # Entry point
├── requirements.txt
├── .env                      # Webhook URLs (not committed)
├── addons/
│   ├── logger.py             # Console + file logging for all traffic
│   ├── interceptor.py        # Target endpoint interception + question extraction
│   └── discord_helper.py     # Discord webhook file upload
└── logs/
    └── proxy.log             # Daily-rotated log (30-day retention)
```

## Interceptor

The interceptor targets `POST /backend/TakeContest/Proceed` on `lex-iap.infosysapps.com`. When matched, it:

1. Extracts `sectionData[*].objectiveQuestionsData` from the response
2. Saves the flattened question list to `assessment_sectionData.json`
3. Uploads the file to Discord via webhook

To change the target, edit `TARGET_HOST`, `TARGET_PATH`, and `TARGET_METHOD` in `addons/interceptor.py`.

## Logs

All traffic is logged to `logs/proxy.log` with daily rotation and 30-day retention. Log entries include request/response headers and body previews for text-based content types.
