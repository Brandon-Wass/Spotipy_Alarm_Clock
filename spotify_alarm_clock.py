import pygame
import math
import datetime
import re
import psutil
import json
from gpiozero import CPUTemperature
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import threading
import time

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080  # Assuming a common resolution, can be dynamically set
FONT_SIZE = 30
CLICK_INTERVAL = 500
CPU_UPDATE_INTERVAL = 1000  # 1 second in milliseconds
CURSOR_HIDE_TIME = 5000  # Time in milliseconds after which cursor is hidden
click_time = 0

# Colors
WHITE, BLACK, GREY, RED, GREEN = (255, 255, 255), (0, 0, 0), (200, 200, 200), (255, 0, 0), (0, 255, 0)

# Load Spotify API credentials from JSON file
with open('spotify_config.json', 'r') as file:
    config = json.load(file)
    spotify_credentials = config['spotify_credentials']
    client_id = spotify_credentials['client_id']
    client_secret = spotify_credentials['client_secret']
    redirect_uri = spotify_credentials['redirect_uri']
    username = spotify_credentials['username']

# Scope for user's currently playing track
scope = 'user-read-currently-playing'

def activate_device(device_name, retry_count=5):
    for _ in range(retry_count):
        try:
            devices = sp.devices()['devices']
            device_id = next((device['id'] for device in devices if device['name'] == device_name), None)

            if device_id:
                sp.transfer_playback(device_id, force_play=False)
                print(f"Playback transferred to {device_name}.")
                return
            else:
                print(f"Device {device_name} not found. Retrying...")
                time.sleep(5)  # Wait for 5 seconds before retrying

        except spotipy.SpotifyException as e:
            print(f"Error in activating device {device_name}: {e}")

    print(f"Failed to activate device {device_name} after {retry_count} retries.")

# Authorization
auth_manager = SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope, username=username, cache_path="token_info.json")
sp = spotipy.Spotify(auth_manager=auth_manager)

# Try to activate "Pi 5"
activate_device("Pi 5")

# Variable to keep track of the last song or podcast
last_played = None

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Clock")
font = pygame.font.Font(None, FONT_SIZE)
clock = pygame.time.Clock()

# Load alarm sound
alarm_sound = pygame.mixer.Sound('alarm.wav')

# Alarm and input management
input_box = pygame.Rect(50, 50, 200, 40)
alarm_box = pygame.Rect(50, 100, 200, 500)
stop_button = pygame.Rect(50, 610, 200, 50)
input_text = ''
alarms = []

# Define Spotify control buttons
button_width, button_height = 120, 50
right_margin, bottom_margin = 10, 110
prev_button = pygame.Rect(SCREEN_WIDTH - 3 * button_width - 3 * right_margin, SCREEN_HEIGHT - bottom_margin, button_width, button_height)
play_pause_button = pygame.Rect(SCREEN_WIDTH - 2 * button_width - 2 * right_margin, SCREEN_HEIGHT - bottom_margin, button_width, button_height)
next_button = pygame.Rect(SCREEN_WIDTH - button_width - right_margin, SCREEN_HEIGHT - bottom_margin, button_width, button_height)

# Cursor visibility control
last_mouse_movement = pygame.time.get_ticks()
cursor_hidden = False

# Get CPU temperature
cpu_temp = CPUTemperature()

# Global variables for CPU info
last_cpu_update = 0
cpu_usage = 0
cpu_temp_value = 0

def write_current_song_to_json():
    global last_played

    while True:
        # Fetch current playing song or podcast
        current_track = sp.current_user_playing_track()

        if current_track is not None and current_track['item'] is not None:
            if current_track['currently_playing_type'] == 'track':
                song_name = current_track['item']['name']
                artist_name = current_track['item']['artists'][0]['name']
            else:
                # For podcasts or other types, set song and artist to N/A
                song_name = "N/A"
                artist_name = "N/A"
        else:
            # When nothing is playing
            song_name = "N/A"
            artist_name = "N/A"

        play_data = {
            'song_name': song_name,
            'artist_name': artist_name
        }

        # Check if the play data has changed
        if play_data != last_played:
            last_played = play_data
            # Write to JSON file
            with open('now_playing.json', 'w') as json_file:
                json.dump(play_data, json_file, indent=4)
        print("Spotify write thread is working.")
        time.sleep(10)

# Start spotify write thread
spotify_write_thread = threading.Thread(target=write_current_song_to_json, daemon=True)
spotify_write_thread.start()

# Helper functions
def draw_text_input_box(screen, font):
    pygame.draw.rect(screen, GREY, input_box, 2)
    text_surface = font.render(input_text, True, WHITE)
    screen.blit(text_surface, (input_box.x + 5, input_box.y + 5))

def draw_alarm_box(screen, font, alarms):
    pygame.draw.rect(screen, GREY, alarm_box, 2)
    for i, alarm in enumerate(alarms):
        alarm_text = font.render(alarm, True, WHITE)
        screen.blit(alarm_text, (alarm_box.x + 5, alarm_box.y + 30 * i + 5))

def draw_stop_button(screen, font):
    pygame.draw.rect(screen, RED, stop_button)
    stop_text = font.render('Stop Alarm', True, WHITE)
    text_rect = stop_text.get_rect(center=stop_button.center)
    screen.blit(stop_text, text_rect)

def draw_spotify_controls(screen, font):
    # Draw Previous Button
    pygame.draw.rect(screen, GREEN, prev_button, 2)  # Change fill to transparent and border to green
    prev_text = font.render('Prev', True, WHITE)
    prev_text_rect = prev_text.get_rect(center=prev_button.center)
    screen.blit(prev_text, prev_text_rect)

    # Draw Play/Pause Button
    pygame.draw.rect(screen, GREEN, play_pause_button, 2)  # Change fill to transparent and border to green
    play_pause_text = font.render('Play/Pause', True, WHITE)
    play_pause_text_rect = play_pause_text.get_rect(center=play_pause_button.center)
    screen.blit(play_pause_text, play_pause_text_rect)

    # Draw Next Button
    pygame.draw.rect(screen, GREEN, next_button, 2)  # Change fill to transparent and border to green
    next_text = font.render('Next', True, WHITE)
    next_text_rect = next_text.get_rect(center=next_button.center)
    screen.blit(next_text, next_text_rect)

def validate_and_format_alarm_time(time_input):
    pattern = re.compile(r"^([01]?\d|2[0-3])([:.])([0-5]\d)$")
    match = pattern.match(time_input)
    if match:
        return f"{match.group(1)}:{match.group(3)}"
    return None

def draw_clock(screen, font):
    now = datetime.datetime.now()
    center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    radius = min(SCREEN_WIDTH, SCREEN_HEIGHT) // 2

    pygame.draw.circle(screen, WHITE, center, radius, 5)

    for tick in range(60):
        angle = math.radians(tick * 6 - 90)
        start, thickness = (0, 0), 1
        if tick % 5 == 0:
            start = (center[0] + radius * 0.9 * math.cos(angle), center[1] + radius * 0.9 * math.sin(angle))
            thickness = 3
            hour = tick // 5 if tick > 0 else 12
            text = font.render(str(hour), True, WHITE)
            text_rect = text.get_rect(center=(center[0] + radius * 0.85 * math.cos(angle), center[1] + radius * 0.85 * math.sin(angle)))
            screen.blit(text, text_rect)
        else:
            start = (center[0] + radius * 0.95 * math.cos(angle), center[1] + radius * 0.95 * math.sin(angle))

        end = (center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle))
        pygame.draw.line(screen, WHITE, start, end, thickness)

    second_angle = math.radians((now.second + now.microsecond / 1000000) * 6 - 90)
    minute_angle = math.radians(now.minute * 6 + now.second * 0.1 - 90)
    hour_angle = math.radians((now.hour % 12) * 30 - 90 + now.minute / 2)

    second_hand = (center[0] + radius * 0.9 * math.cos(second_angle), center[1] + radius * 0.9 * math.sin(second_angle))
    minute_hand = (center[0] + radius * 0.7 * math.cos(minute_angle), center[1] + radius * 0.7 * math.sin(minute_angle))
    hour_hand = (center[0] + radius * 0.5 * math.cos(hour_angle), center[1] + radius * 0.5 * math.sin(hour_angle))

    pygame.draw.line(screen, WHITE, center, second_hand, 2)
    pygame.draw.line(screen, WHITE, center, minute_hand, 4)
    pygame.draw.line(screen, WHITE, center, hour_hand, 6)

def check_and_play_alarm(alarms):
    now = datetime.datetime.now()
    if now.second == 0 and now.strftime("%H:%M") in alarms and not pygame.mixer.get_busy():
        alarm_sound.play(loops=-1)

def draw_cpu_info(screen, font, current_time):
    global last_cpu_update, cpu_usage, cpu_temp_value
    if current_time - last_cpu_update >= CPU_UPDATE_INTERVAL:
        cpu_usage = psutil.cpu_percent()
        cpu_temp_value = cpu_temp.temperature
        last_cpu_update = current_time

    right_margin = 10
    box_width = 200

    cpu_text = f"CPU Usage: {cpu_usage}%"
    cpu_surface = font.render(cpu_text, True, WHITE)
    cpu_rect = cpu_surface.get_rect(bottomright=(SCREEN_WIDTH - right_margin, SCREEN_HEIGHT - 150))
    cpu_rect.left = SCREEN_WIDTH - right_margin - box_width
    screen.blit(cpu_surface, cpu_rect)

    temp_text = f"CPU Temp: {cpu_temp_value:.2f}°C"
    temp_surface = font.render(temp_text, True, WHITE)
    temp_rect = temp_surface.get_rect(bottomright=(SCREEN_WIDTH - right_margin, SCREEN_HEIGHT - 120))
    temp_rect.left = SCREEN_WIDTH - right_margin - box_width
    screen.blit(temp_surface, temp_rect)

def read_now_playing():
    try:
        with open('now_playing.json', 'r') as file:
            data = json.load(file)
            return data['song_name'], data['artist_name']
    except (FileNotFoundError, json.JSONDecodeError):
        return "N/A", "N/A"

def draw_song_info(screen, font, song_name, artist_name):

    right_margin = 10

    song_info_text = f"Now Playing: {song_name} - {artist_name}"
    song_info_surface = font.render(song_info_text, True, WHITE)
    song_info_rect = song_info_surface.get_rect(bottomright=(SCREEN_WIDTH - right_margin, SCREEN_HEIGHT - 30))
    screen.blit(song_info_surface, song_info_rect)

# Main loop
running = True
while running:
    current_time = pygame.time.get_ticks()
    screen.fill(BLACK)

    if pygame.time.get_ticks() - last_mouse_movement > CURSOR_HIDE_TIME and not cursor_hidden:
        pygame.mouse.set_visible(False)
        cursor_hidden = True
    elif pygame.mouse.get_rel() != (0, 0):
        pygame.mouse.set_visible(True)
        last_mouse_movement = pygame.time.get_ticks()
        cursor_hidden = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_RETURN:
                formatted_time = validate_and_format_alarm_time(input_text)
                if formatted_time:
                    alarms.append(formatted_time)
                input_text = ''
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            else:
                input_text += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y = event.pos
                if alarm_box.collidepoint(mouse_x, mouse_y):
                    if current_time - click_time < CLICK_INTERVAL:
                        index = (mouse_y - alarm_box.y) // 30
                        if index < len(alarms):
                            del alarms[index]
                    click_time = current_time
                if stop_button.collidepoint(event.pos):
                    alarm_sound.stop()
                # Spotify control event handling
                if prev_button.collidepoint(mouse_x, mouse_y):
                    sp.previous_track()
                if play_pause_button.collidepoint(mouse_x, mouse_y):
                    current_playback = sp.current_playback()
                    if current_playback and current_playback['is_playing']:
                        sp.pause_playback()
                    else:
                        sp.start_playback()
                if next_button.collidepoint(mouse_x, mouse_y):
                    sp.next_track()

    check_and_play_alarm(alarms)
    draw_clock(screen, font)
    draw_text_input_box(screen, font)
    draw_alarm_box(screen, font, alarms)
    draw_stop_button(screen, font)
    draw_cpu_info(screen, font, current_time)
    draw_spotify_controls(screen, font)
    
    song_name, artist_name = read_now_playing()
    draw_song_info(screen, font, song_name, artist_name)

    pygame.display.flip()
    clock.tick(30)  # Limit to 30 FPS

pygame.quit()
