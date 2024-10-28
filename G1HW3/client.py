import socket
import time
import os
import threading
import queue

MAX_RESULTS = 1000
failed_queue = queue.Queue()

# 수식을 서버에 전송하는 함수
def send_expressions(client, expression_file, send_cnt, log_file):
    try:
        with open(expression_file, 'r') as file:
            expressions = file.readlines()
            while send_cnt[0] < MAX_RESULTS:
                # 재전송 요청이 있는 경우 큐에서 꺼내어 다시 전송
                if not failed_queue.empty():
                    failed_count = failed_queue.get() - 1
                    expression = expressions[failed_count].strip()
                    message = f"SEND:{failed_count+1}:{expression}"
                    log_file.write(f"[재전송] {failed_count+1}번 수식 전송: {expression}\n")
                    print(f"[재전송] {failed_count+1}번 수식 전송: {expression}")
                    client.send((message + "\n").encode())
                else:
                    # 일반 전송 처리
                    expression = expressions[send_cnt[0]].strip()
                    if expression:
                        message = f"SEND:{send_cnt[0]+1}:{expression}"
                        log_file.write(f"[{send_cnt[0]+1}번 수식 전송]: {expression}\n")
                        print(f"[{send_cnt[0]+1}번 수식 전송]: {expression}")
                        client.send((message + "\n").encode())
                        time.sleep(0.1)  # 전송 간격 조절
                    send_cnt[0] += 1
    except Exception as e:
        log_file.write(f"[전송 오류] {e}\n")
        print(f"[전송 오류] {e}")

# 서버로부터 결과를 수신하는 함수
def receive_results(client, received_cnt, log_file):
    try:
        buffer = ""  # 수신한 메시지를 임시로 저장할 버퍼
        while received_cnt[0] < MAX_RESULTS:
            data = client.recv(1024).decode()
            if not data:
                break  # 서버 연결이 종료된 경우 루프 탈출

            buffer += data
            messages = buffer.split("\n")
            buffer = messages.pop()  # 마지막 요소는 완전하지 않을 수 있으므로 버퍼에 남김

            for result in messages:
                result = result.strip()
                if not result:
                    continue
                # 실패 메시지 확인 및 재요청 처리
                if result.startswith("FAILED:"):
                    parts = result.split(":")
                    if len(parts) >= 2:
                        failed_count = int(parts[1])  # 순번 추출
                        failed_queue.put(failed_count)  # 재전송 요청
                        log_file.write(f"[오류] 누락된 데이터 재전송 요청 (순번: {failed_count})\n")
                        print(f"[오류] 누락된 데이터 재전송 요청 (순번: {failed_count})")
                else:
                    # 정상 결과 수신
                    received_cnt[0] += 1
                    log_file.write(f"[{received_cnt[0]}번 결과 수신]: {result}\n")
                    print(f"[{received_cnt[0]}번 결과 수신]: {result}")
                time.sleep(0.1)

        if received_cnt[0] >= MAX_RESULTS:
            client.send("EXIT\n".encode())
            log_file.write("[종료 요청] 1000개의 결과 수신 완료, 서버에 종료 요청 전송\n")
            print("[종료 요청] 1000개의 결과 수신 완료, 서버에 종료 요청 전송")

    except Exception as e:
        log_file.write(f"[수신 오류] {e}\n")
        print(f"[수신 오류] {e}")

# 서버에 연결하고 수식을 전송하는 클라이언트 함수
def start_client(host="34.68.170.234", port=9999):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    print(f"[서버 연결] {host}:{port}에 연결됨.")

    # 서버로부터 플래그 수신
    flag_msg = client.recv(4096).decode().strip()
    client_id = int(flag_msg.split(":")[1])  # FLAG:1, FLAG:2 등에서 숫자만 추출
    print(f"[클라이언트 ID 설정] ID: {client_id}")

    # 클라이언트 ID에 따라 로그 파일 지정
    log_file_path = f"Client{client_id}.txt"
    log_file = open(log_file_path, 'w')  # 로그 파일 직접 열기
    log_file.write(f"[로그 시작] 클라이언트 {client_id} 로그 파일\n")

    # 클라이언트 접속 순서에 맞는 파일 선택
    path = os.path.dirname(os.path.abspath(__file__))
    expression_file = path + f"/Expression{client_id}.txt"
    log_file.write(f"[파일 선택] {expression_file}\n")
    print(f"[파일 선택] {expression_file}")

    # 전송 스레드와 수신 스레드 시작
    received_cnt = [0]  # 결과 수신 횟수 저장
    send_cnt = [0]      # 계산 전송 횟수 저장
    send_thread = threading.Thread(target=send_expressions, args=(client, expression_file, send_cnt, log_file))
    receive_thread = threading.Thread(target=receive_results, args=(client, received_cnt, log_file))

    send_thread.start()
    receive_thread.start()

    # 스레드가 완료될 때까지 대기
    send_thread.join()
    receive_thread.join()

    client.close()
    log_file.write("[연결 종료] 서버와의 연결이 종료됨.\n")
    print("[연결 종료] 서버와의 연결이 종료됨.")
    log_file.close()

if __name__ == "__main__":
    start_client()
