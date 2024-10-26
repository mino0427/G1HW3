import socket
import threading
import re

MAX_CLIENTS = 4
connections = []  # 클라이언트 연결을 저장할 리스트

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

# 클라이언트로부터 수신한 수식을 처리하고 결과를 반환하는 함수
def handle_client(client_socket, address):
    print(f"[클라이언트 연결] {address} 연결됨.")
    try:

        # 클라이언트와의 통신 (연산 결과 전송)
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            
            print(f"[{address}] 받은 수식: {data}")
            result = calculate_expression(data)
            print(f"[{address}] 계산 결과: {result}")
            
            client_socket.send(str(result).encode())
        
    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        client_socket.close()

# 서버 실행
def start_server(host="127.0.0.1", port=9999):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(MAX_CLIENTS)
    print(f"[서버 시작] {host}:{port}에서 대기 중...")

    client_id = 1
    while len(connections) < MAX_CLIENTS:
        client_socket, addr = server.accept()
        connections.append((client_socket, addr))  # 연결을 리스트에 추가
        print(f"클라이언트 연결 완료: {addr}, 할당된 ID: {client_id}")

        # 각 클라이언트에 대해 handle_client 스레드 시작, ID 할당
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()
    
    for client in connections:
                # 접속 순서에 따라 FLAG 전송
        client[0].send(f"FLAG:{client_id}\n".encode())
        client_id += 1  # 다음 클라이언트에 대한 ID 증가

if __name__ == "__main__":
    start_server()
