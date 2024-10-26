import socket
import threading
import re
import queue

MAX_CLIENTS = 4  # 클라이언트 4개 대기
clients = []  # 클라이언트 연결을 저장할 리스트
waiting_queue = queue.Queue(30)  # 힙/공유 메모리를 기반으로 한 대기 리스트

# 수식을 파싱하고 계산하는 함수
def calculate_expression(expression):
    def apply_operator(operators, values):
        operator = operators.pop()
        right = values.pop()
        left = values.pop()
        if operator == '+':
            values.append(left + right)
        elif operator == '-':
            values.append(left - right)
        elif operator == '*':
            values.append(left * right)
        elif operator == '/':
            values.append(left / right)

    precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
    operators = []
    values = []

    tokens = re.findall(r'\d+|[+*/()-]', expression)

    for token in tokens:
        if token.isdigit():
            values.append(int(token))
        elif token in precedence:
            while (operators and operators[-1] in precedence and
                   precedence[operators[-1]] >= precedence[token]):
                apply_operator(operators, values)
            operators.append(token)
        elif token == '(':
            operators.append(token)
        elif token == ')':
            while operators[-1] != '(':
                apply_operator(operators, values)
            operators.pop()

    while operators:
        apply_operator(operators, values)

    return values[0]

# 하나의 스레드에서 대기 리스트 관리 및 계산 수행
def waiting():
    print("[대기 스레드 시작] 클라이언트로부터 수식을 대기 중...")
    while True:
        for client_socket, address in clients:
            try:
                # 클라이언트로부터 수식 수신
                data = client_socket.recv(1024).decode()
                if data:
                    print(f"[{address}] 수신된 수식: {data}")
                    
                   # 대기 리스트가 가득 찬 경우 오류 메시지 전송
                    if waiting_queue.full():
                        error_message = f"대기 리스트가 가득 찼습니다. 수식: {data}"
                        print(f"[오류] {error_message}")
                        client_socket.send(error_message.encode())
                    else:
                        # 대기 리스트에 수식 추가
                        waiting_queue.put((client_socket, address, data))
                        print(f"[{address}] 수식 대기 리스트에 추가됨: {data}")
                        
            except Exception as e:
                print(f"[에러] {address}에서 수식을 수신하는 중 오류 발생: {e}")
                clients.remove((client_socket, address))
                client_socket.close()

# 대기 리스트에서 수식을 처리하고 결과를 반환하는 management 스레드 함수
def management():
    print("[관리 스레드 시작] 대기 리스트에서 수식을 처리 중...")
    while True:
        if not waiting_queue.empty():
            client_socket, address, expression = waiting_queue.get()  # 대기 리스트에서 수식 가져오기
            print(f"[{address}] 계산할 수식: {expression}")
            result = calculate_expression(expression)
            print(f"[{address}] 계산 결과: {result}")
            
            # 계산 결과를 해당 클라이언트에게 반환
            try:
                client_socket.send(str(result).encode())
            except Exception as e:
                print(f"[에러] {address}로 결과 전송 중 오류 발생: {e}")
                clients.remove((client_socket, address))
                client_socket.close()

# 서버 실행
def start_server(host="127.0.0.1", port=9999):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"[서버 시작] {host}:{port}에서 대기 중...")


    client_id = 1
    while len(clients) < MAX_CLIENTS:
        client_socket, addr = server.accept()
        clients.append((client_socket, addr))  # 연결을 리스트에 추가
        print(f"클라이언트 연결 완료: {addr}, 할당된 ID: {client_id}")

    # 대기 스레드 시작
    waiting_thread = threading.Thread(target=waiting, daemon=True)
    waiting_thread.start()

    # 관리 스레드 시작
    management_thread = threading.Thread(target=management, daemon=True)
    management_thread.start()       

    for client in clients:# 접속 순서에 따라 FLAG 전송
        client[0].send(f"FLAG:{client_id}\n".encode())
        client_id += 1  # 다음 클라이언트에 대한 ID 증가




if __name__ == "__main__":
    start_server()
