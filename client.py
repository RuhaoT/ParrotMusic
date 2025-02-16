# load server_info.json
import json
import os
import sys
import time

import pygame
import requests
import tinytag

with open('server_info.json', 'r', encoding="utf-8") as f:
    server_info = json.load(f)
    SERVER_IP = server_info['server_ip']
    HANDSHAKE_INTERVAL = server_info['handshake_interval']
    RETRY_INTERVAL = server_info['retry_interval']
    LOCAL_AUDIO_DIR = server_info['local_audio_dir']
    CLIENT_ID = server_info['client_id']

# 初始化pygame
pygame.mixer.init()

def handshake():
    try:
        response = requests.get(f"{SERVER_IP}/handshake/{CLIENT_ID}", timeout=15,verify=False)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Handshake failed: {e}")
        return None

def download_audio(file_path, audio_file):
    # 如果本地没有该文件，则下载
    local_path = os.path.join(LOCAL_AUDIO_DIR, audio_file)
    if not os.path.exists(local_path):
        try:
            response = requests.get(f"{SERVER_IP}/download_audio/{audio_file}", timeout=15)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded {audio_file}.")
            else:
                print(f"Failed to download {audio_file}.")
        except Exception as e:
            print(f"Error downloading audio: {e}")

def play_audio(audio_file, volume):
    local_path = os.path.join(LOCAL_AUDIO_DIR, audio_file)
    if os.path.exists(local_path):
        # obtain audio duration
        audio = tinytag.TinyTag.get(local_path)
        audio_duration_pad = audio.duration + 3
        print(f"Audio duration: {audio.duration} seconds.")
        print(f"Playing {audio_file}...")
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.load(local_path)
        pygame.mixer.music.play()
        # wait for playback to finish
        time.sleep(audio_duration_pad)
        print(f"Finished playing {audio_file}.")
    else:
        print(f"Audio file {audio_file} not found locally.")

def main():
    status = handshake()
    if status and status['status'] == 'ready':
        print(status['message'])
        download_audio(status['file_path'], status['file_path'].split('/')[-1])
        play_audio(status['file_path'].split('/')[-1], status['volume'])
    elif status and status['status'] == 'waiting':
        print(status['message'])
        time.sleep(HANDSHAKE_INTERVAL)
    else:
        print(status['message'] if status else "Error during handshake.")
        time.sleep(RETRY_INTERVAL)
        
    # to prevent memory leak, restart the client
    os.execv(sys.executable, ['python'] + sys.argv)


if __name__ == "__main__":
    main()