import socket
import threading
import re
import queue
import os

MAX_CLIENTS = 4  # 클라이언트 4개 대기
clients = []  # 클라이언트 연결을 저장할 리스트
waiting_queue = queue.Queue(30)  # 힙/공유 메모리를 기반으로 한 대기 리스트
calc_queue = queue.Queue()  # 계산 요청 큐
result_queue = queue.Queue()  # 계산 결과 큐
exit_count = 0

# 파싱 트리를 위한 노드 클래스
class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

# 파싱 트리로 수식을 계산하는 함수
def calculate_expression(expression):
    def build_tree(tokens):
        precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
        operators = []
        operands = []

        for token in tokens:
            if token.isdigit():  # 숫자인 경우
                operands.append(Node(int(token)))
            elif token in precedence:  # 연산자인 경우
                while (operators and operators[-1].value in precedence and
                       precedence[operators[-1].value] >= precedence[token]):
                    operator = operators.pop()
                    operator.right = operands.pop()
                    operator.left = operands.pop()
                    operands.append(operator)
                operators.append(Node(token))
            elif token == '(':
                operators.append(Node(token))
            elif token == ')':
                while operators[-1].value != '(':
                    operator = operators.pop()
                    operator.right = operands.pop()
                    operator.left = operands.pop()
                    operands.append(operator)
                operators.pop()

        while operators:
            operator = operators.pop()
            operator.right = operands.pop()
            operator.left = operands.pop()
            operands.append(operator)

        return operands[0]  # 루트 노드 반환

    def evaluate(node):
        if isinstance(node.value, int):
            return node.value
        left_val = evaluate(node.left)
        right_val = evaluate(node.right)
        if node.value == '+':
            return left_val + right_val
        elif node.value == '-':
            return left_val - right_val
        elif node.value == '*':
            return left_val * right_val
        elif node.value == '/':
            return left_val / right_val

    tokens = re.findall(r'\d+|[+*/()-]', expression)
    root = build_tree(tokens)
    return evaluate(root)

# 하나의 스레드에서 대기 리스트 관리 및 계산 수행
def waiting():
    global exit_count

    print("[대기 스레드 시작] 클라이언트로부터 수식을 대기 중...")
    while True:
        for client_socket, address in clients:
            try:
                # 클라이언트로부터 수식 수신
                data = client_socket.recv(1024).decode()
                if data:
                    if data == "EXIT":
                        print(f"[종료 요청] {address}에서 연결 종료 요청 수신")
                        clients.remove((client_socket, address))
                        client_socket.close()
                        exit_count += 1
                        print(f"[연결 종료] {address}와의 연결이 종료됨. 종료 수신 수: {exit_count}")

                        # 모든 클라이언트가 종료 요청을 보낸 경우 서버 종료
                        if exit_count >= MAX_CLIENTS:
                            print("[서버 종료] 모든 클라이언트로부터 종료 요청을 수신하여 서버를 종료합니다.")
                            os._exit(0)  # 서버 종료
                        continue

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
