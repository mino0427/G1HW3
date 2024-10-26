import socket
import time
import os
import threading

MAX_RESULTS = 1000

# 수식을 서버에 전송하는 함수
def send_expressions(client, expression_file):
    try:
        with open(expression_file, 'r') as file:
            for line in file:
                expression = line.strip()
                if expression:
                    print(f"[수식 전송] {expression}")
                    client.send(expression.encode())
                    time.sleep(0.1)  # 전송 간격 조절
    except Exception as e:
        print(f"[전송 오류] {e}")

# 서버로부터 결과를 수신하는 함수
def receive_results(client, results_received):
    try:
        # while True:
        while results_received < MAX_RESULTS:
            result = client.recv(1024).decode()
            if not result:
                break  # 서버 연결이 종료된 경우 루프 탈출
            
            # 실패 메시지 확인 및 재요청 처리
            if result.startswith("FAILED:"):
                expression = result.split(":")[1]  # 실패한 수식 추출
                print("[오류] 큐가 가득참")
                print(f"[재전송] {expression}")
                time.sleep(0.1)
                client.send(expression.encode())  # 수식 재전송
            else:
                # 정상 결과 수신
                print(f"[서버 응답] 결과: {result}")
                results_received += 1
                time.sleep(0.1)

                # 결과 수신 완료 후 서버에 종료 신호 전송
        if results_received >= MAX_RESULTS:
            client.send("EXIT".encode())
            print("[종료 요청] 1000개의 결과 수신 완료, 서버에 종료 요청 전송")

    except Exception as e:
        print(f"[수신 오류] {e}")

# 서버에 연결하고 수식을 전송하는 클라이언트 함수
def start_client(host="127.0.0.1", port=9999):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    print(f"[서버 연결] {host}:{port}에 연결됨.")
    
    # 서버로부터 플래그 수신
    flag_msg = client.recv(4096).decode().strip()
    client_id = int(flag_msg.split(":")[1])  # FLAG:1, FLAG:2 등에서 숫자만 추출
    print(f"[클라이언트 ID 설정] ID: {client_id}")

    # 클라이언트 접속 순서에 맞는 파일 선택
    path = os.path.dirname(os.path.abspath(__file__))
    expression_file = path + f"/Expression{client_id}.txt"
    
    # 전송 스레드와 수신 스레드 시작
    results_received = 0  # 결과 수신 횟수 저장 (리스트로 참조 가능하게 만듦)
    send_thread = threading.Thread(target=send_expressions, args=(client, expression_file))
    receive_thread = threading.Thread(target=receive_results, args=(client, results_received))

    send_thread.start()
    receive_thread.start()

    # 스레드가 완료될 때까지 대기
    send_thread.join()
    receive_thread.join()

    client.close()
    print("[연결 종료] 서버와의 연결이 종료됨.")

if __name__ == "__main__":
    start_client()
