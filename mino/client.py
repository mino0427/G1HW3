import socket
import time
import os

# 서버에 연결하고 수식을 전송하는 클라이언트 함수
def start_client(expression_file, host="127.0.0.1", port=9999):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    print(f"[서버 연결] {host}:{port}에 연결됨.")
    
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

    path = os.path.dirname(os.path.abspath(__file__))
    print(path)
    expression_files = [
        path+"\Expression1.txt",  # 첫 번째 클라이언트용 파일
        path+"\Expression2.txt",  # 두 번째 클라이언트용 파일
        path+"\Expression3.txt",  # 세 번째 클라이언트용 파일
        path+"\Expression4.txt"   # 네 번째 클라이언트용 파일
    ]

    start_client(expression_files[0])
