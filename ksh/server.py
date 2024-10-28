import socket
import threading
import re
import queue
import os
import time

MAX_CLIENTS = 4  # 클라이언트 최대 접속 수
clients = []  # 클라이언트 연결을 저장할 리스트
waiting_queue = queue.Queue()  # 대기 리스트 (무제한 크기)
calc_queue = queue.Queue()  # 계산 요청 큐
result_queue = queue.Queue()  # 계산 결과 큐
exit_count = 0  # 종료 요청 수

system_clock_time = 0  # 가상의 System Clock (msec 단위)
clock_lock = threading.Lock()  # System Clock을 보호하는 lock

clients_lock = threading.Lock()
exit_count_lock = threading.Lock()

# System Clock을 증가시키는 함수
def update_system_clock(increment):
    global system_clock_time
    with clock_lock:
        system_clock_time += increment

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

        i = 0
        while i < len(tokens):
            token = tokens[i]
            if re.match(r'\d+', token):  # 숫자인 경우
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
                while operators and operators[-1].value != '(':
                    operator = operators.pop()
                    operator.right = operands.pop()
                    operator.left = operands.pop()
                    operands.append(operator)
                operators.pop()  # '(' 제거
            i += 1

        while operators:
            operator = operators.pop()
            operator.right = operands.pop()
            operator.left = operands.pop()
            operands.append(operator)

        return operands[0]  # 루트 노드 반환
    
    def count_leaf_nodes(node):
        if not node:
            return 0
        if not node.left and not node.right:
            return 1
        return count_leaf_nodes(node.left) + count_leaf_nodes(node.right)

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
            if right_val == 0:
                raise ZeroDivisionError("division by zero")
            return left_val / right_val

    try:
        # 음수 숫자 및 소수 처리
        tokens = re.findall(r'\d+\.\d+|\d+|[+*/()-]', expression)
        root = build_tree(tokens)
        leaf_count = count_leaf_nodes(root)  # leaf node의 개수
        update_system_clock(leaf_count)  # 가상의 계산 시간 반영 (노드당 1 msec)
        time.sleep(leaf_count * 0.001)  # 실제 지연 시간 적용

        return evaluate(root)
    except Exception as e:
        return f"Error: {str(e)}"

# 클라이언트로부터 데이터를 수신하는 함수
def waiting(client_socket, address, log_file):
    global exit_count

    received_cnt = 0
    received_counts = set()  # 수신된 순번을 추적하는 집합

    while True:
        try:
            data = client_socket.recv(1024).decode()
            if data:
                # 요청마다 System Clock 1 msec 증가
                update_system_clock(1)
                # 현재 System Clock으로 타임스탬프 생성
                timestamp = f"[{system_clock_time:.3f} msec] "

                data = data.strip()
                # 종료 요청 처리
                if data == "EXIT":
                    log_file.write(f"{timestamp}[종료 요청] {address}에서 연결 종료 요청 수신\n")
                    print(f"{timestamp}[종료 요청] {address}에서 연결 종료 요청 수신")
                    client_socket.close()
                    with exit_count_lock:
                        exit_count += 1
                    log_file.write(f"{timestamp}[연결 종료] {address}와의 연결이 종료됨. 종료 수신 수: {exit_count}\n")
                    print(f"{timestamp}[연결 종료] {address}와의 연결이 종료됨. 종료 수신 수: {exit_count}")

                    # 모든 클라이언트가 종료 요청을 보낸 경우 서버 종료
                    if exit_count >= MAX_CLIENTS:
                        log_file.write("{timestamp}[서버 종료] 모든 클라이언트로부터 종료 요청을 수신하여 서버를 종료합니다.\n")
                        print("{timestamp}[서버 종료] 모든 클라이언트로부터 종료 요청을 수신하여 서버를 종료합니다.")
                        os._exit(0)  # 서버 종료
                    break

                # 데이터가 'SEND:순번:수식' 형식인지 확인하고 파싱
                if data.startswith("SEND:"):
                    parts = data.split(":", 2)
                    if len(parts) == 3:
                        _, count_str, expression = parts
                        count = int(count_str)

                        # 수신된 순번을 기록
                        received_counts.add(count)

                        log_file.write(f"{timestamp}[{address}] 수신된 수식: {expression} (순번: {count})\n")
                        print(f"{timestamp}[{address}] 수신된 수식: {expression} (순번: {count})")

                        # 누락된 순번 확인 및 클라이언트에 알림
                        expected_count = len(received_counts)
                        if count != expected_count:
                            missing_message = f"FAILED:{expected_count}:{expression}\n"
                            client_socket.send(missing_message.encode())
                            log_file.write(f"{timestamp}[경고] {address}에서 순번 {expected_count} 누락됨, 재전송 요청\n")
                            print(f"{timestamp}[경고] {address}에서 순번 {expected_count} 누락됨, 재전송 요청")

                        received_cnt += 1
                        log_file.write(f"현재 {received_cnt}개 수신\n")
                        print(f"현재 {received_cnt}개 수신")

                        # 대기 리스트에 수식 추가
                        waiting_queue.put((client_socket, address, expression))
                        log_file.write(f"[{address}] 수식 대기 리스트에 추가됨: {expression}\n")
                        print(f"[{address}] 수식 대기 리스트에 추가됨: {expression}")

        except Exception as e:
            log_file.write(f"{timestamp}[에러] {address}에서 수식을 수신하는 중 오류 발생: {e}\n")
            print(f"{timestamp}[에러] {address}에서 수식을 수신하는 중 오류 발생: {e}")
            client_socket.close()
            break

# 대기 리스트에서 수식을 처리하고 결과를 반환하는 management 스레드 함수
def management(log_file):
    print("[관리 스레드 시작] 대기 리스트에서 수식을 처리 중...")

    while True:
        timestamp = f"[{system_clock_time:.3f} msec] "
        # 결과 큐 처리
        if not result_queue.empty():
            client_socket, address, result = result_queue.get()
            try:
                client_socket.send((str(result) + "\n").encode())
                log_file.write(f"[{timestamp}{address}] 계산 결과 전송: {result}\n")
                print(f"[{timestamp}{address}] 계산 결과 전송: {result}")
            except Exception as e:
                log_file.write(f"[에러] {address}로 결과 전송 중 오류 발생: {e}\n")
                print(f"[에러] {address}로 결과 전송 중 오류 발생: {e}")
            result_queue.task_done()
            continue  # 다음 루프로 넘어감

        # 대기 큐 처리
        if not waiting_queue.empty():
            client_socket, address, expression = waiting_queue.get()
            log_file.write(f"[{address}] 계산할 수식: {expression}\n")
            print(f"[{address}] 계산할 수식: {expression}")
            calc_queue.put((client_socket, address, expression))
            waiting_queue.task_done()
        else:
            # 둘 다 비어있으면 잠시 대기
            time.sleep(0.1)

# 계산 작업을 수행하는 calc 스레드 함수
def calc(calc_cnt, log_file):
    print(f"[계산 스레드 시작] {calc_cnt}번 calc 생성 중...")
    global system_clock_time

    while True:
        client_socket, address, expression = calc_queue.get()  # 계산할 데이터 수신
        result = calculate_expression(expression)  # 계산 수행

        timestamp = f"[{system_clock_time:.3f} msec] "
        log_file.write(f"{timestamp}[{address}] 계산 수행 완료: {expression} = {result}\n")
        print(f"[{timestamp}{address}] 계산 수행 완료: {expression} = {result}")
        result_queue.put((client_socket, address, result))  # 결과를 result_queue에 넣음
        calc_queue.task_done()

# 서버 실행
def start_server(host="0.0.0.0", port=9999):
    global system_clock_time
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"[서버 시작] {host}:{port}에서 대기 중...")

    # 서버 로그 파일 생성
    log_file_path = f"Server.txt"
    log_file = open(log_file_path, 'w', encoding='utf-8')  # 로그 파일 직접 열기
    log_file.write(f"[로그 시작] Server.txt\n")

    client_id = 1
    while len(clients) < MAX_CLIENTS:
        client_socket, addr = server.accept()
        with clients_lock:
            clients.append((client_socket, addr))  # 연결을 리스트에 추가
        log_file.write(f"클라이언트 연결 완료: {addr}\n")
        print(f"클라이언트 연결 완료: {addr}")
        
        start_time = time.time() if system_clock_time == 0 else start_time
        # 각 클라이언트에 대한 핸들러 스레드 시작
        client_thread = threading.Thread(target=waiting, args=(client_socket, addr, log_file))
        client_thread.start()
    
    for client in clients:
        # 접속 순서에 따라 FLAG 전송
        client[0].send(f"FLAG:{client_id}\n".encode())
        client_id += 1  # 다음 클라이언트에 대한 ID 증가

    # 관리 스레드 시작
    management_thread = threading.Thread(target=management, args=(log_file,))
    management_thread.start()

    # 적절한 수의 calc 스레드 생성
    calc_threads = []
    calc_cnt = 0
    for _ in range(10):  # 필요한 만큼의 스레드 수로 조정
        calc_cnt += 1
        thread = threading.Thread(target=calc, args=(calc_cnt, log_file))
        thread.start()
        calc_threads.append(thread)

    # 메인 스레드 대기
    management_thread.join()
    for thread in calc_threads:
        thread.join()

if __name__ == "__main__":
    start_server()
