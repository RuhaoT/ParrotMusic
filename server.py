import time
import queue
import os
import pandas as pd
import random
from flask import Flask, jsonify, send_file
import threading

app = Flask(__name__)

# 定义音频播放队列
audio_queue = queue.Queue()

# 定义音频文件目录
AUDIO_DIRECTORY = 'music'

# roulette
def roulette(names, possibilities):
    # names: list of music names
    # possibilities: list of play_possibility
    # return: selected music name
    total_possibility = sum(possibilities)
    random_number = random.uniform(0, total_possibility)
    for i in range(len(names)):
        if random_number < possibilities[i]:
            return names[i]
        random_number -= possibilities[i]
    return names[-1]

# 模拟的音频调度器函数
def music_scheduler():
    # 假设每个小时调用一次，返回一个播放时间范围和音频文件
    current_time = time.localtime(time.time())
    play = False
    # # 在这个例子中，我们假设每到10:00到11:00之间播放某个音频
    # if current_time.tm_hour == 10:  # 例如，10:00-11:00播放某个音频
    #     audio_file = 'audio1.mp4'
    #     file_path = AUDIO_DIRECTORY + audio_file
    #     play_start_time = 10  # 播放开始时间段，单位小时
    #     play_end_time = 11  # 播放结束时间段，单位小时
    #     audio_queue.put((audio_file, file_path, play_start_time, play_end_time))
    #     print(f"Scheduled {audio_file} for playback between {play_start_time}:00 and {play_end_time}:00.")
    
    #debug
    if True:  # 例如，10:00-11:00播放某个音频
        play = True
        audio_file = 'AnotherStory.mp3'
        file_path = os.path.join(AUDIO_DIRECTORY, audio_file)
        volume = 1.0
        print(f"Scheduled {audio_file} for playback.")
        
        return play, audio_file, file_path, volume
    
    # step 1. read schedule/schedule.csv
    # schedule format: music_name, start_time, end_time, play_possibility, volume_mean, volume_std
    schedule = pd.read_csv('schedule/schedule.csv')
    # step 2: obtain current time
    current_time = time.localtime(time.time())
    # step 3: select all music that can be played at current time--current_time within start_time and end_time
    current_schedule = schedule[(schedule['start_time'] <= current_time.tm_hour) & (schedule['end_time'] > current_time.tm_hour)]
    # check if current_schedule is empty
    if current_schedule.empty:
        return False, None, None, None
    # step 4: select one music from current_schedule, based on play_possibility
    name_array = current_schedule['music_name'].values
    possibility_array = current_schedule['play_possibility'].values
    selected_name = roulette(name_array, possibility_array)
    # step 5: select volume from uniform distribution
    selected_volume = random.uniform(current_schedule['volume_mean'], current_schedule['volume_std'])
    # step 6: return selected music name and volume
    return True, selected_name, os.path.join(AUDIO_DIRECTORY, selected_name), selected_volume
    

# 音频下载接口
@app.route('/download_audio/<audio_file>', methods=['GET'])
def download_audio(audio_file):
    file_path = os.path.join(AUDIO_DIRECTORY, audio_file)
    if os.path.exists(file_path):
        print(f"Sending {audio_file} to client.")
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"status": "error", "message": f"File {audio_file} not found."}), 404

# 客户端握手接口
@app.route('/handshake/<client_id>', methods=['GET'])
def handshake(client_id):
    play, audio_file, file_path, volume = music_scheduler()
    if play:
        return jsonify({
            "status": "ready",
            "message": f"Client is ready to play {audio_file}.",
            "file_path": file_path,
            "volume": volume,
        }), 200
    else:
        return jsonify({"status": "waiting", "message": "No audio scheduled at the moment."}), 200

# 播放音频控制接口
@app.route('/play_audio/<client_id>/<audio_file>', methods=['POST'])
def play_audio(client_id, audio_file):
    # 这里假设控制客户端播放音频的逻辑
    print(f"Server instructed to play {audio_file} for client {client_id}.")
    return jsonify({"status": "playing", "message": f"Playing {audio_file}."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6324)