import threading
import requests
import tkinter as tk
from tkinter import *
import pandas as pd
from pandastable import Table
import time
import RPi.GPIO as GPIO

flag = False #blink_background �Լ��� �� ���� �۵���Ű�� ���� flag
blink_finished = threading.Event() #blink_background �۾� �Ϸ� ���θ� �˷��ִ� �̺�Ʈ ��ü
exit_con = ""

def infinite_loop():
    global exit_con
    #exit �����̳ʿ��� con �� ��� ����
    while True:
        #exit �����̳ʿ��� ������ �� ��� ����
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
            #���� �������� ���� ����� ���� ��(exit �����̳ʿ� 1�� ��� ���� ��)
            if exit_con == "1":
                #exit �����̳ʿ� 0�� POST�ϱ�
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
                #BUZZER �︮��
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
        #��� �����̳ʿ� con ���� ��� ����ǰ� �ϱ� ���� �ʿ�
        except KeyError as e:
            # KeyError �߻� �� ���� ó��
            print(f"Exit_KeyError occurred: {e}")
        
        #2�ʸ��� exit�� GET�ϱ�
        time.sleep(2)
#������ ���� �� ����
my_thread = threading.Thread(target=infinite_loop)
my_thread.start()

# �����͸� ������ url�� �⺻ ����
base_url = "http://114.71.220.109:7579/Mobius/test/No.{}/la"

# ��� ����
headers = {
  'Accept': 'application/json',
  'X-M2M-RI': '12345',
  'X-M2M-Origin': 'St6mqRLPHQd'
}

# �����͸� �޾ƿ� url�� ����
url_count = 12

# ���� ������ ��ųʸ�
value_dict = {i: {'1': 0, '2': 0} for i in range(1, url_count+1)}

def update_data():
    try:
        # ������ url�κ��� ������ �޾ƿ���
        for i in range(1, url_count+1):
            url = base_url.format(i)
            response = requests.get(url, headers=headers)
            data = response.json()
            value = data['m2m:cin']['con']

            # ���� '1' �Ǵ� '2'�̸� �ش� �� ����('1'�̸� ž�� ��� / '2' ž�� �Ϸ�)
            if value in ['1', '2']:
                value_dict[i][value] += 1
                # �� �������� �ش� ���������� �����̳ʿ� 0 POST �ϱ�
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
    #��� �����̳ʿ� con ���� ��� ����ǰ� �ϱ� ���� �ʿ�
    except KeyError as e:
        # KeyError �߻� �� ���� ó��
        print(f"KeyError occurred: {e}")

    # ������ ���� �� ���� 2���� 3���� �����ϰ�, �ش� ���� 2���� 3�� ���� �� �� 4�� �� ����
    for i in range(1, url_count+1):
        df.iloc[i, 1] = value_dict[i]['1']
        df.iloc[i, 2] = value_dict[i]['2']

        if df.iloc[i, 1] == df.iloc[i, 2]:
            if df.iloc[i, 1] == 0:
                df.iloc[i, 3] = "�°� �����"
            else:
                df.iloc[i, 3] = "ž�� �Ϸ�"
        else:
            df.iloc[i, 3] = "�°� �����"

    # ǥ ����
    table.redraw()

    # 1�� �Ŀ� �ٽ� update_data �Լ� ȣ��
    root.after(1000, update_data)

# pandas�� 10�� 4���� ������������ �����
df = pd.DataFrame([[""]*4 for _ in range(13)], 
                  columns=[f'Column {j+1}' for j in range(4)])

df.iloc[0, 1:4] = ["ž�� ���", "ž�� �Ϸ�", "ž�� ����"]
df.iloc[1:, 0] = ["�λ꿪", "�۵��ؼ�����", "�ϳ�����", "��õ��ȭ����", "�ٴ����ؼ�����", "�ƹ̻� ������", "�γ�ġ�� �帲��", "�λ�����̼���",
                  "������ �ϱ� ���ڼ���", "����ڹ���", "��������", "��λ� ����"]

# tkinter�� â �����
root = tk.Tk()
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))

# ������ ����
frame = tk.Frame(root)
frame.pack(expand=True, fill='both')

# ������������ ǥ��
table = Table(frame, dataframe=df, showtoolbar=True, showstatusbar=True)

table.show()

# ó�� ������ ����
update_data()

root.mainloop()