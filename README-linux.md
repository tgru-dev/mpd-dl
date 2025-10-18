# N_m3u8DL-RE Web UI - Linux/Debian Installation

Ein modernes Web-Interface für die N_m3u8DL-RE Binary, das eine benutzerfreundliche Oberfläche für das Herunterladen von MPD/M3U8-Streams bietet.

## Features

- 🎨 **Modernes UI-Design** mit responsivem Layout
- 🔑 **Automatische Key-Generierung** - extrahiert PSSH aus MPD und generiert Keys über API
- 🔑 **Manuelle Key-Eingabe** als Alternative
- 📁 **Format-Auswahl** (MKV, MP4, TS, M4S)
- 🏆 **Beste Qualität** - lädt automatisch die höchste Video- und Audioqualität herunter
- 👁️ **Live-Befehlsvorschau** vor dem Download
- 📋 **Copy-to-Clipboard** Funktionalität
- 📊 **Live-Download-Logs** mit Streaming-Output
- 💾 **Auto-Save** der Formulardaten
- ✅ **Input-Validierung** mit Fehlermeldungen

## Installation auf Linux/Debian

### Voraussetzungen

- **Python 3.7+** (empfohlen: Python 3.9+)
- **N_m3u8DL-RE Binary** für Linux
- **Internetverbindung** für API-Calls

### Systemvoraussetzungen installieren

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv curl wget
```

#### CentOS/RHEL/Fedora:
```bash
# CentOS/RHEL
sudo yum install python3 python3-pip curl wget

# Fedora
sudo dnf install python3 python3-pip curl wget
```

#### Arch Linux:
```bash
sudo pacman -S python python-pip curl wget
```

### N_m3u8DL-RE Binary herunterladen

```bash
# Für Linux x64
wget https://github.com/nilaoda/N_m3u8DL-RE/releases/latest/download/N_m3u8DL-RE_Beta_linux-x64.tar.gz
tar -xzf N_m3u8DL-RE_Beta_linux-x64.tar.gz
chmod +x N_m3u8DL-RE
```

### Setup

1. **Projekt herunterladen:**
   ```bash
   git clone <repository-url>
   cd mpd-dl
   ```

2. **Dependencies installieren:**
   ```bash
   ./start-linux.sh
   ```

3. **Server starten:**
   ```bash
   ./start-linux.sh
   ```

4. **Web-Interface öffnen:**
   Öffne deinen Browser und gehe zu: `http://localhost:7421`

## Verwendung

### 1. MPD/M3U8 URL eingeben
Gib die URL zu deinem MPD oder M3U8-Stream ein.

### 2. License URL eingeben
Gib die Widevine-Lizenz-URL ein (z.B. `https://cwip-shaka-proxy.appspot.com/no_auth`).

### 3. Decryption Key generieren oder eingeben
**Option A - Automatisch generieren:**
- Klicke auf **"Auto Generate"** - das System extrahiert automatisch die PSSH aus der MPD-Datei und generiert den Key über die API.

**Option B - Manuell eingeben:**
- Gib den Decryption Key im Format `key:iv` ein:
```
5af20cdb999358b1b53ba0d5e3ed2d63:4512c0c303c785401fcd24b0cf1d83ae
```

### 4. Format auswählen
Wähle das gewünschte Output-Format:
- **MKV** (Standard)
- **MP4**
- **TS**
- **M4S**

### 5. Optionale Parameter
- **Output Directory:** Verzeichnis für Downloads (Standard: `./downloads`)
- **Custom Filename:** Eigener Dateiname (ohne Extension)

### 6. Download starten
- Klicke auf **"Command Preview"** um den generierten Befehl zu sehen
- Klicke auf **"Start Download"** um den Download zu beginnen
- Verfolge den Fortschritt im Live-Log

## Beispiel-Command

Das Web-UI generiert Befehle wie diesen:

```bash
./N_m3u8DL-RE -M format=mkv --key 5af20cdb999358b1b53ba0d5e3ed2d63:4512c0c303c785401fcd24b0cf1d83ae --select-video best --select-audio best --save-dir "./downloads" --save-name "my_video" https://example.com/playlist.mpd
```

## Linux-spezifische Features

### Systemd Service (Optional)

Erstelle einen systemd Service für automatischen Start:

```bash
sudo nano /etc/systemd/system/mpd-dl.service
```

Inhalt:
```ini
[Unit]
Description=N_m3u8DL-RE Web UI
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/mpd-dl
ExecStart=/path/to/mpd-dl/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Service aktivieren:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mpd-dl
sudo systemctl start mpd-dl
```

### Firewall konfigurieren

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 7421

# firewalld (CentOS/RHEL/Fedora)
sudo firewall-cmd --permanent --add-port=7421/tcp
sudo firewall-cmd --reload
```

### Nginx Reverse Proxy (Optional)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:7421;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Python nicht gefunden
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip
```

### Binary nicht ausführbar
```bash
chmod +x N_m3u8DL-RE
```

### Port bereits belegt
```bash
# Prüfen welcher Prozess Port 7421 verwendet
sudo netstat -tulpn | grep 7421
sudo lsof -i :7421

# Prozess beenden
sudo kill -9 <PID>
```

### Berechtigungen für Downloads-Verzeichnis
```bash
chmod 755 downloads/
```

## API Endpoints

- `GET /` - Hauptseite
- `POST /api/generate-key` - Automatische Key-Generierung
- `POST /api/download` - Download starten
- `GET /api/status/<download_id>` - Download-Status abfragen
- `GET /api/downloads` - Alle aktiven Downloads auflisten
- `POST /api/stop/<download_id>` - Download stoppen
- `POST /api/validate` - Input validieren
- `GET /api/health` - Health Check

## Projektstruktur

```
mpd-dl/
├── N_m3u8DL-RE          # Binary (muss vorhanden sein)
├── index.html           # Hauptseite
├── style.css            # Styling
├── script.js            # Frontend JavaScript
├── server.py            # Flask Backend
├── requirements.txt     # Python Dependencies
├── start-linux.sh       # Linux Start-Script
└── README-linux.md      # Diese Datei
```

## Lizenz

Dieses Projekt ist für Bildungszwecke gedacht. Stelle sicher, dass du die entsprechenden Rechte für die Inhalte hast, die du herunterlädst.

## Support

Bei Problemen oder Fragen erstelle ein Issue oder kontaktiere den Entwickler.
