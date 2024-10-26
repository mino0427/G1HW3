import socket
import threading
import re
import queue

MAX_CLIENTS = 4  # 클라이언트 4개 대기
clients = []  # 클라이언트 연결을 저장할 리스트
waiting_queue = queue.Queue(30)  # 힙/공유 메모리를 기반으로 한 대기 리스트
calc_queue = queue.Queue()  # 계산 요청 큐
result_queue = queue.Queue()  # 계산 결과 큐

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
                        error_message = f"FAILED: {data}"
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
            calc_queue.put((client_socket, address, expression))  # 계산 요청을 calc_queue에 넣음
            waiting_queue.task_done()
            
             # result_queue에서 계산 결과 수신
            if not result_queue.empty():
                client_socket, address, result = result_queue.get()
                try:
                    client_socket.send(str(result).encode())  # 클라이언트에 결과 전송
                    print(f"[{address}] 계산 결과 전송: {result}")
                except Exception as e:
                    print(f"[에러] {address}로 결과 전송 중 오류 발생: {e}")
                result_queue.task_done()

# 계산 작업을 수행하는 calc 스레드 함수
def calc():
    while True:
        client_socket, address, expression = calc_queue.get()  # 계산할 데이터 수신
        result = calculate_expression(expression)  # 계산 수행
        result_queue.put((client_socket, address, result))  # 결과를 result_queue에 넣음
        calc_queue.task_done()

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
        print(f"클라이언트 연결 완료: {addr}")

    # 대기 스레드 시작
    waiting_thread = threading.Thread(target=waiting, daemon=True)
    waiting_thread.start()

    # 관리 스레드 시작
    management_thread = threading.Thread(target=management, daemon=True)
    management_thread.start() 

    # 200개의 calc 스레드를 생성하고, 스레드 리스트에 추가하여 join 가능하도록 설정
    calc_threads = []
    for _ in range(200):
        thread = threading.Thread(target=calc, daemon=True)
        thread.start()
        calc_threads.append(thread)

    # 200개의 calc 스레드 생성
    for _ in range(200):
        threading.Thread(target=calc, daemon=True).start()      

    for client in clients:# 접속 순서에 따라 FLAG 전송
        client[0].send(f"FLAG:{client_id}\n".encode())
        client_id += 1  # 다음 클라이언트에 대한 ID 증가
    
    waiting_thread.join()
    management_thread.join()
    for thread in calc_threads:
        thread.join()

if __name__ == "__main__":
    start_server()
