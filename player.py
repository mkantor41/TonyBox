#!/usr/bin/env python3

# --------------------------------------------
# DIY Toniebox: NFC Spotify Player with Buttons
# --------------------------------------------
# This script uses an RFID reader to scan NFC tags,
# matches the tag ID to a Spotify URI from a database,
# and plays music using the Spotify Web API.
# It also reads 3 physical buttons connected to GPIO:
# Play/Pause, Next Track, and Previous Track.

# -------------------------
# Standard Library Imports
# -------------------------
import os                      # For reading environment variables
import sqlite3                 # To access the local SQLite database
from time import sleep         # To pause between loops or actions

# -------------------------
# External Library Imports
# -------------------------
from dotenv import load_dotenv           # To load Spotify credentials from a .env file
import spotipy                          # Spotify Web API library
from spotipy.oauth2 import SpotifyOAuth  # Spotify login/auth system

# -------------------------
# GPIO + RFID Library Imports
# -------------------------
import RPi.GPIO as GPIO              # Raspberry Pi GPIO pin control
from mfrc522 import SimpleMFRC522    # Library for the MFRC522 NFC/RFID reader

# -------------------------
# Load environment variables (like Spotify keys)
# -------------------------
load_dotenv()  # Loads variables from .env file into the script's environment

# Assign environment variables to Python variables
DEVICE_ID = os.getenv("DEVICE_ID")  # Spotify device ID for playback (usually the Pi)
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# -------------------------
# Set up Spotify API access
# -------------------------
# This allows us to control playback, skip tracks, etc.
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-read-playback-state,user-modify-playback-state",
    cache_path=os.path.expanduser("~/.cache/spotipy")  # Where auth tokens are stored
))

# -------------------------
# GPIO Setup (for buttons)
# -------------------------
GPIO.setmode(GPIO.BCM)        # Use Broadcom GPIO pin numbering
GPIO.setwarnings(False)       # Disable warnings about pin reuse

# Define which pins the buttons are connected to
BTN_PLAY_PAUSE = 22  # Physical button for Play/Pause
BTN_NEXT = 27        # Physical button for Next Track
BTN_PREV = 17        # Physical button for Previous Track

# Store buttons in a dictionary for easy iteration
buttons = {
    BTN_PLAY_PAUSE: "Play/Pause",
    BTN_NEXT: "Next Track",
    BTN_PREV: "Previous Track"
}

# Configure each button pin as an input with a pull-up resistor
for pin in buttons:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Pull-up: normally HIGH

# -------------------------
# Set up RFID reader
# -------------------------
reader = SimpleMFRC522()  # This uses SPI and GPIO under the hood
last_tag_id = None         # Used to prevent duplicate scans

# -------------------------
# Look up Spotify URI from scanned tag
# -------------------------
def get_tag_data(tag_id):
    """
    Search the SQLite database for the given tag ID.
    Returns a tuple: (spotify_uri, media_type) or None if not found.
    """
    conn = sqlite3.connect("nfc_tags.db")  # Open database
    cursor = conn.cursor()
    cursor.execute("SELECT spotify_uri, media_type FROM tags WHERE tag_id = ?", (tag_id,))
    result = cursor.fetchone()  # Get one matching result
    conn.close()  # Close connection
    return result

# -------------------------
# Start playing the music
# -------------------------
def play_media(uri, media_type):
    """
    Play a Spotify track, album, or playlist depending on media_type.
    """
    try:
        # Make sure the Pi is the active playback device
        sp.transfer_playback(device_id=DEVICE_ID, force_play=True)
        sleep(1)  # Give Spotify time to switch devices
    except spotipy.exceptions.SpotifyException:
        print("⚠️ Couldn't transfer playback. Is the speaker online?")
        return

    try:
        if media_type == "track":
            sp.start_playback(device_id=DEVICE_ID, uris=[uri])
        elif media_type in ["album", "playlist"]:
            sp.start_playback(device_id=DEVICE_ID, context_uri=uri)
        else:
            print(f"Unknown media type '{media_type}' for URI: {uri}")
    except Exception as e:
        print(f"❌ Error starting playback: {e}")

# -------------------------
# Button Functions
# -------------------------
def handle_play_pause():
    """Toggle play/pause on current Spotify playback."""
    print("⏯️ Play/Pause button pressed")
    try:
        playback = sp.current_playback()
        if playback and playback["is_playing"]:
            sp.pause_playback()
        else:
            sp.start_playback()
    except Exception as e:
        print(f"⚠️ Error toggling playback: {e}")

def handle_next():
    """Skip to the next track."""
    print("⏭️ Next Track button pressed")
    try:
        sp.next_track()
    except Exception as e:
        print(f"⚠️ Error skipping track: {e}")

def handle_previous():
    """Go back to the previous track."""
    print("⏮️ Previous Track button pressed")
    try:
        sp.previous_track()
    except Exception as e:
        print(f"⚠️ Error going to previous track: {e}")

# -------------------------
# Main Program Loop
# -------------------------
print("📻 DIY Toniebox ready. Scan a tag or press a button.")

try:
    while True:
        # --- Read from NFC tag ---
        try:
            tag_id = str(reader.read()[0])  # Read tag ID only
            if tag_id != last_tag_id:  # Skip if it's the same tag
                print(f"Tag scanned: {tag_id}")
                tag_data = get_tag_data(tag_id)  # Lookup in DB
                if tag_data:
                    spotify_uri, media_type = tag_data
                    print(f"Playing {media_type}: {spotify_uri}")
                    play_media(spotify_uri, media_type)
                    last_tag_id = tag_id
                else:
                    print("🚫 Tag not found in database.")
            else:
                print("🔁 Duplicate scan detected; ignoring.")
        except Exception as e:
            print(f"AUTH ERROR!!\n{e}")

        # --- Poll buttons ---
        if GPIO.input(BTN_PLAY_PAUSE) == GPIO.LOW:
            handle_play_pause()
            sleep(0.3)  # Debounce delay

        if GPIO.input(BTN_NEXT) == GPIO.LOW:
            handle_next()
            sleep(0.3)

        if GPIO.input(BTN_PREV) == GPIO.LOW:
            handle_previous()
            sleep(0.3)

        sleep(0.1)  # Loop delay to reduce CPU usage

# -------------------------
# Graceful Exit
# -------------------------
except KeyboardInterrupt:
    print("Exiting gracefully...")

finally:
    GPIO.cleanup()  # Reset GPIO pins to a safe state
