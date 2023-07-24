import threading
import requests
import tkinter as tk
from tkinter import *
import pandas as pd
from pandastable import Table
import time
import RPi.GPIO as GPIO

flag = False #blink_background 함수를 한 번만 작동시키기 위한 flag
blink_finished = threading.Event() #blink_background 작업 완료 여부를 알려주는 이벤트 객체
exit_con = ""

def infinite_loop():
    global exit_con
    #exit 컨테이너에서 con 값 들고 오기
    while True:
        #exit 컨테이너에서 마지막 값 들고 오기
        exit_url = "http://114.71.220.109:7579/Mobius/test/exit/la"
        payload = {}
        headers = {
            'Accept': 'application/json',
            'X-M2M-RI': '12345',
            'X-M2M-Origin': 'St6mqRLPHQd'
        }
        try:
            response = requests.request("GET", exit_url, headers=headers, data=payload)
            data = response.json()
            exit_con = data["m2m:cin"]["con"]
            #만약 하차벨을 누른 사람이 있을 때(exit 컨테이너에 1이 들어 왔을 때)
            if exit_con == "1":
                #exit 컨테이너에 0값 POST하기
                request_url = "http://114.71.220.109:7579/Mobius/test/exit"
                payload = "{\n    \"m2m:cin\": {\n        \"con\": \"0\"\n    }\n}"
                post_headers = {
                    'Accept': 'application/json',
                    'X-M2M-RI': '12345',
                    'X-M2M-Origin': 'St6mqRLPHQd',
                    'Content-Type': 'application/vnd.onem2m-res+json; ty=4'
                }

                response = requests.request("POST", request_url, headers=post_headers, data=payload)

                print(response.text)
                #BUZZER 울리기
                buzzer = 18
                buzzer_scale = [392, 415, 440, 392, 415, 440, 392, 415, 440]
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(buzzer, GPIO.OUT)
                GPIO.setwarnings(False)

                pwm = GPIO.PWM(buzzer, 1.0)
                pwm.start(50.0)

                for i in range(0, 9):
                    pwm.ChangeFrequency(buzzer_scale[i])
                    time.sleep(0.4)
                pwm.ChangeFrequency(523)
                time.sleep(0.5)

                pwm.ChangeDutyCycle(0.0)
                pwm.stop()
                GPIO.cleanup()
        #모든 컨테이너에 con 값이 없어도 실행되게 하기 위해 필요
        except KeyError as e:
            # KeyError 발생 시 예외 처리
            print(f"Exit_KeyError occurred: {e}")
        
        #2초마다 exit값 GET하기
        time.sleep(2)
#스레드 생성 및 실행
my_thread = threading.Thread(target=infinite_loop)
my_thread.start()

# 데이터를 가져올 url의 기본 구조
base_url = "http://114.71.220.109:7579/Mobius/test/No.{}/la"

# 헤더 설정
headers = {
  'Accept': 'application/json',
  'X-M2M-RI': '12345',
  'X-M2M-Origin': 'St6mqRLPHQd'
}

# 데이터를 받아올 url의 개수
url_count = 12

# 값을 저장할 딕셔너리
value_dict = {i: {'1': 0, '2': 0} for i in range(1, url_count+1)}

def update_data():
    try:
        # 각각의 url로부터 데이터 받아오기
        for i in range(1, url_count+1):
            url = base_url.format(i)
            response = requests.get(url, headers=headers)
            data = response.json()
            value = data['m2m:cin']['con']

            # 값이 '1' 또는 '2'이면 해당 값 증가('1'이면 탑승 희망 / '2' 탑승 완료)
            if value in ['1', '2']:
                value_dict[i][value] += 1
                # 값 가져오고 해당 버스정류장 컨테이너에 0 POST 하기
                request_url = "http://114.71.220.109:7579/Mobius/test/No." + str(i)
                payload = "{\n    \"m2m:cin\": {\n        \"con\": \"0\"\n    }\n}"
                post_headers = {
                    'Accept': 'application/json',
                    'X-M2M-RI': '12345',
                    'X-M2M-Origin': 'St6mqRLPHQd',
                    'Content-Type': 'application/vnd.onem2m-res+json; ty=4'
                }

                response = requests.request("POST", request_url, headers=post_headers, data=payload)

                print(response.text)
    #모든 컨테이너에 con 값이 없어도 실행되게 하기 위해 필요
    except KeyError as e:
        # KeyError 발생 시 예외 처리
        print(f"KeyError occurred: {e}")

    # 증가한 값을 각 행의 2열과 3열에 저장하고, 해당 행의 2열과 3열 값을 비교 후 4열 값 갱신
    for i in range(1, url_count+1):
        df.iloc[i, 1] = value_dict[i]['1']
        df.iloc[i, 2] = value_dict[i]['2']

        if df.iloc[i, 1] == df.iloc[i, 2]:
            if df.iloc[i, 1] == 0:
                df.iloc[i, 3] = "승객 대기중"
            else:
                df.iloc[i, 3] = "탑승 완료"
        else:
            df.iloc[i, 3] = "승객 대기중"

    # 표 갱신
    table.redraw()

    # 1초 후에 다시 update_data 함수 호출
    root.after(1000, update_data)

# pandas로 10행 4열의 데이터프레임 만들기
df = pd.DataFrame([[""]*4 for _ in range(13)], 
                  columns=[f'Column {j+1}' for j in range(4)])

df.iloc[0, 1:4] = ["탑승 희망", "탑승 완료", "탑승 여부"]
df.iloc[1:, 0] = ["부산역", "송도해수욕장", "암남공원", "감천문화마을", "다대포해수욕장", "아미산 전망대", "부네치아 장림항", "부산현대미술관",
                  "낙동강 하구 에코센터", "석당박물관", "국제시장", "용두산 공원"]

# tkinter로 창 만들기
root = tk.Tk()
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))

# 프레임 생성
frame = tk.Frame(root)
frame.pack(expand=True, fill='both')

# 데이터프레임 표시
table = Table(frame, dataframe=df, showtoolbar=True, showstatusbar=True)

table.show()

# 처음 데이터 갱신
update_data()

root.mainloop()