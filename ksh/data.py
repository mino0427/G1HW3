import socket
import threading
import re

MAX_CLIENTS = 4  # 클라이언트 4개 대기
clients = []  # 클라이언트 연결을 저장할 리스트
waiting_list = []  # 수식을 저장할 대기 리스트 (최대 30개)

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
                    if len(waiting_list) >= 30:
                        error_message = f"대기 리스트가 가득 찼습니다. 수식: {data}"
                        print(f"[오류] {error_message}")
                        client_socket.send(error_message.encode())
                    else:
                        # 대기 리스트에 수식 추가
                        waiting_list.append((client_socket, address, data))
                        print(f"[{address}] 수식 대기 리스트에 추가됨: {data}")
                        
                        # 수식을 꺼내서 계산 수행
                        client_socket, address, expression = waiting_list.pop(0)
                        print(f"[{address}] 계산할 수식: {expression}")
                        result = calculate_expression(expression)
                        print(f"[{address}] 계산 결과: {result}")
                        
                        # 계산 결과 반환
                        client_socket.send(str(result).encode())
                        
            except Exception as e:
                print(f"[에러] {address}에서 수식을 처리하는 중 오류 발생: {e}")
                clients.remove((client_socket, address))
                client_socket.close()

# 클라이언트로부터 수신한 수식을 처리하고 결과를 반환하는 함수
def handle_client(client_socket, address):
    print(f"[클라이언트 연결] {address} 연결됨.")
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            
            print(f"[{address}] 받은 수식: {data}")
            result = calculate_expression(data)
            print(f"[{address}] 계산 결과: {result}")
            
            client_socket.send(str(result).encode())
        
        except Exception as e:
            print(f"에러 발생: {e}")
            break

    client_socket.close()

# 서버 실행
def start_server(host="127.0.0.1", port=9999):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"[서버 시작] {host}:{port}에서 대기 중...")

    # 대기 스레드 시작
    waiting_thread = threading.Thread(target=waiting, daemon=True)
    waiting_thread.start()

    while len(clients) < MAX_CLIENTS:
        client_socket, addr = server.accept()
        clients.append((client_socket, addr))  # 연결을 리스트에 추가
        print(f"클라이언트 연결 완료: {addr}")

        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()

if __name__ == "__main__":
    start_server()