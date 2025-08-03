# 📻 DIY Toniebox – NFC Spotify Player with Web UI

This ~Vibe Coded~ project turns a Raspberry Pi into a toddler-friendly **NFC music player**, Each NFC tag plays a specific Spotify album, playlist, or track. 

It includes:

- 🎧 **Physical playback system** (NFC tag reader + buttons)
- 🌐 **Flask-based web UI** for managing tags
- 🐍 Written in **Python**, using `spotipy`, `gpiozero`, `RPi.GPIO`, and `MFRC522`

---

## 🧱 Hardware Requirements

- **Raspberry Pi 3 or 4** (tested on Pi 4)
- **MFRC522 NFC reader** (SPI)
- **Buttons** (for play/pause, next, previous)
- **Speakers** (via 3.5mm jack or USB)
- NFC tags (compatible with MFRC522)
