import requests
import time
import pygame
import os

SERVER_IP = 'http://localhost:6324'
CLIENT_ID = 'client1'
HANDSHAKE_INTERVAL = 300  # 握手间隔时间，单位秒
RETRY_INTERVAL = 15  # 重试间隔时间，单位秒
LOCAL_AUDIO_DIR = './music_cache'

# 初始化pygame
pygame.mixer.init()

def handshake():
    try:
        response = requests.get(f"{SERVER_IP}/handshake/{CLIENT_ID}", timeout=15)
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
        print(f"Playing {audio_file}...")
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.load(local_path)
        pygame.mixer.music.play()
        # wait for playback to finish
        while pygame.mixer.music.get_busy():
            time.sleep(1)
        print(f"Finished playing {audio_file}.")
    else:
        print(f"Audio file {audio_file} not found locally.")

def main():
    while True:
        status = handshake()
        if status and status['status'] == 'ready':
            print(status['message'])
            download_audio(status['file_path'], status['file_path'].split('/')[-1])
            play_audio(status['file_path'].split('/')[-1], status['volume'])
            continue
        elif status and status['status'] == 'waiting':
            print(status['message'])
            time.sleep(HANDSHAKE_INTERVAL)
        else:
            print(status['message'] if status else "Error during handshake.")
            time.sleep(RETRY_INTERVAL)


if __name__ == "__main__":
    main()