import socket
import time
import os

# 서버에 연결하고 수식을 전송하는 클라이언트 함수
def start_client(host="127.0.0.1", port=9999):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    print(f"[서버 연결] {host}:{port}에 연결됨.")
    
    # 서버로부터 플래그 수신
    flag_msg = client.recv(4096).decode().strip()
    client_id = int(flag_msg.split(":")[1])  # FLAG:1, FLAG:2 등에서 숫자만 추출
    # 클라이언트 접속 순서에 맞는 파일 선택
    path = os.path.dirname(os.path.abspath(__file__))
    expression_file = path + f"/Expression{client_id}.txt"

    if client_id>0 :

        try:
            # 파일에서 수식 읽기
            with open(expression_file, 'r') as file:
                for line in file:
                    expression = line.strip()
                    if expression:
                        print(f"[수식 전송] {expression}")
                        client.send(expression.encode())
                        
                        # 결과 수신
                        result = client.recv(1024).decode()
                        print(f"[서버 응답] 수식: {expression}, 결과: {result}")
                        time.sleep(1)  # 1초 간격으로 요청 전송
        except KeyboardInterrupt:
            print("[클라이언트 종료] 클라이언트 종료.")
        finally:
            client.close()

if __name__ == "__main__":
    start_client()
