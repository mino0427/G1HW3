1조 조원 구성 및 역할

20203043 권수현 - server.py 스레드 알고리즘 작성, log 작성, 재전송 알고리즘 작성, 디버깅

20203058 남태인 - 오류 해결, Read me 작성, 코드 작성

20203072 안민호 – 절대 경로로 텍스트 파일읽어내기, 파싱트리 코딩, 오류 해결,
Readme 작성


1. 프로그램 구성요소 : server.py, client.py

◆ server.py 구성요소
① 클라이언트 관리
- MAX_CLIENTS: 서버에 연결 가능한 최대 클라이언트 수(4)
- clients, clients_lock: 클라이언트 연결을 관리하는 리스트와 잠금 장치로, 다중 스레드 환경에서 클라이언트 목록을 안전하게 조작할 수 있도록 하는 장치

② 큐
- waiting_queue: 클라이언트로부터 수신한 수식을 처리하기 전에 대기, 30개 제한
- calc_queue: 계산할 수식을 담는 큐로, 대기 큐에서 수식을 꺼내 이곳에 저장한 후 계산 스레드가 처리
- result_queue: 계산 결과를 담는 큐로, 계산이 끝난 결과를 여기에 넣고 관리 스레드가 클라이언트로 결과를 전송
- failed_queue: 클라이언트로부터 누락된 순번의 수식에 대해 재전송을 요청받은 경우 이 큐에 순번을 추가하여 재전송 대기 상태로 만듦 (클라이언트에 존재)

③ 수식 처리 및 계산
- Node 클래스: 수식을 파싱 트리로 변환하기 위해 사용하는 클래스, 연산자와 피연산자를 저장하고, 트리 구조로 연산
- calculate_expression(): 수식을 파싱 트리로 변환하고 계산하는 함수, 수식에 포함된 연산자의 우선순위를 고려하여 트리를 구성하고, 재귀적으로 트리를 탐색하여 결과를 산출

④ 클라이언트와 통신
waiting():
-클라이언트로 부터 "EXIT" 메시지를 받으면 exit_count++, exit_count==4이면 Server 종료한다
-"SEND" 메시지를 받으면 클라이언트 별로 수식의 순번을 기록
	-누락된 순번 확인 및 클라이언트에게 알림
	-누락된 순번이 없으면 정상적으로 waiting_queue에 추가

⑤ 스레드 간 통신
- management(): 대기 큐에서 수식을 꺼내 계산 큐로 전달하고, 결과 큐에서 계산 결과를 클라이언트로 전송
- calc(): 계산 큐에 담긴 수식을 처리하고, 계산 결과를 결과 큐에 저장

⑥ 서버 실행 및 종료 관리
- start_server(): 서버를 시작하고 클라이언트 연결을 관리하는 함수. 모든 클라이언트가 종료 요청을 보낸 경우 서버를 종료
- exit_count: 서버가 종료될 수 있는 기준으로, 모든 클라이언트가 종료 요청을 보내면 서버를 자동으로 종료

◆ client.py 구성요소
① 큐
- failed_queue: 서버에서 특정 순번의 데이터 누락으로 인해 재전송 요청을 받은 경우 해당 순번을 여기에 저장하여 우선적으로 재전송을 준비(누락 메시지를 직접 받아서 처리하기 보다 스레드 관리를 위해 큐를 사용)

② 서버에 수식 전송
- send_expressions(): 로컬 파일에서 라인별로 수식을 읽어 순차적으로 서버로 전송. 단, failed_queue에 누락된 값의 정보가 있으면 그 수식을 우선적으로 재전송.

③ 서버로부터 결과 수신
- receive_results(): 서버로부터 수식 계산 결과를 수신하고, 서버로부터 "FAILED" 메시지를 받으면 이 누락된 순번을 재전송 큐에 추가.(스레드 관리를 위해 바로 재전송하기 보다 큐를 이용) 설정된 최대 수신 횟수에 도달하면 서버에 EXIT 메시지를 보내 연결 종료를 요청

④ 클라이언트 연결 관리
- start_client(): 서버에 연결을 설정하고, 서버로부터 받은 클라이언트 ID에 따라 해당 ID의 수식 파일을 선택. 이후 수식 전송 스레드와 결과 수신 스레드를 생성해 비동기적으로 작업을 수행



2. 소스코드 컴파일 방법 (GCP 사용)

① 구글 클라우드에 접속하여 VM instance를 생성한다.
	지역 : us-central1로 설정
	머신 유형 : e2-micro
	부팅 디스크 : Debian

② 방화벽 규칙을 추가한다
	대상 : 모든 인스턴스 선택
	소스 IP 범위 : 0.0.0.0/0  (모든 IP 주소 허용)
	프로토콜 및 포트 : TCP와 해당 포트를 지정 (port : 9999)

③ 생성된 인스턴스의 SSH를 실행한다.

④ Python과 개발 도구의 패키지들을 설치한다 (Debian 기준)
	sudo apt update
	sudo apt install python3
	sudo apt install python3-pip
	pip install numpy
	pip install numpy scipy
	pip install loguru //Python에서 로그(logging)기능을 제공하는 라이브러리

⑤ 가상환경을 생성하고 활성화한다.
	python3 -m venv myenv(가상환경 이름)
	source myenv/bin/activate //가상환경 활성화

⑥ UPLOAD FILE을 클릭하여 server.py를 업로드한다.
	server.py가 업로드된 디렉터리에서 python3 server.py로 server를 실행한다.

⑦ 로컬에서 powershell 터미널 4개를 열어 python3 client.py로 client 4개를 실행한다. (vscode 터미널에서 실행해도 됨)
	
⑧ server에 4개의 client가 모두 연결되면 프로그램이 실행된다.

☆주의할 점 : client의 host 정의가 자신이 사용하는 외부주소로 되어있는지 확인한다



3. 프로그램 실행환경 및 실행방법 설명
(실행방법 - 2번 참고)
외부 서버 - 구글 클라우드 (파이썬 3.11.2버전, 0.25-2 vCPU (1 shared core)
		메모리 1GB, Boot disk size 20GB, interface type: SCSI
로컬 실행 환경 - 프로세서 12th Gen Intel(R) Core(TM) i5-12500H 2.50 GHz
		      RAM 16GB, 64bit 운영체제, x64기반 프로세서


4. 서버의 thread 관리 및 작업 대기 리스트의 선정 알고리즘에 대한 설명 작성

⦁ 알고리즘 시나리오
① waiting 스레드에서 클라이언트에게 받은 데이터를 waiting_queue에 저장한다.
② management 스레드에서 waiting_queue에 저장된 데이터를 들어온 순서대로 calc_queue에 저장한다.
③ 200개의 calc 스레드는 calc_queue의 수식을 가져와 연산 후 결과를 result_queue에 저장한다. 
④ management 스레드는 result_queue에 있는 결과값을 클라이언트에게 전송한다

※ 스레드 사이의 자원 관리는 파이썬의 큐에서 제공하는 락을 이용하였다.


5. Error or Additional Message Handling
▶ Additional Message Handling
⊙ Server
① 종료 요청 처리 (EXIT)
- 클라이언트가 EXIT 메시지를 보내면 해당 클라이언트의 연결을 종료, 서버의 전체 연결 수가 최대값에 도달하면 서버 전체 종료
- exit_count를 증가, 모든 클라이언트 종료 요청을 받은 경우 os._exit(0) 시행
(gracefully termination)

② 수식 전송 처리 (SEND:순번:수식)
- SEND: 로 시작하는 메시지는 특정 순번의 수식 데이터로 인식
메시지 순번과 수식으로 파싱 후, 수식 대기 큐에 추가
- 순번을 기록해서 누락된 순번 감지, 누락 시 클라이언트에 해당 순번에 대해 
"FAILED:{expected_count}:{expression}" 메시지를 보내 재전송 요청

③ 결과 큐 메시지 처리
- 계산 결과가 result_queue에 쌓이면 클라이언트에게 해당 결과를 전송
- 결과 전송 시 client_socket.send()를 사용해 결과를 클라이언트로 전송

⊙ Client
① 재전송 요청 처리 ("FAILED:{expected_count}:{expression}\n")
- 서버로부터 FAILED 메시지를 수신하면 누락된 순번에 대한 재전송 요청으로 인식, 해당 순번을 failed_queue에 추가하여 재전송 준비
- 메시지 파싱 후 누락된 순번을 추출하고, failed_queue.put(failed_count)로 재전송 큐에 해당 순번 추가

② 수신한 결과 처리
- 서버로부터 정상적인 수식 계산 결과 메시지 수신 시 received_cnt를 증가시키고 로그 파일에 기록
- received_cnt[0] += 1로 수신된 결과 횟수 증가, [순번 결과 수신]: 결과 형식으로 로그와 콘솔에 기록

③ 종료 요청 처리(EXIT)
- 설정된 최대 수신 개수에 도달(MAX_RESULTS=1000)하면, 클라이언트는 EXIT 메시지를 서버로 전송해 연결 종료 요청을 보냄 (gracefully termination을 위해)
- client.send("EXIT\n".encode())로 서버 종료 요청 전송



▶ Error Handling (Exception 처리 포함)

⊙ Server
① 데이터 수신 오류(waiting() - except Exception as e)
- 클라이언트로부터 데이터를 수신하는 중 오류가 발생할 경우 예외 포착
- 발생한 오류를 로그파일에 기록, 해당 클라이언트와 연결 종료

② 결과 전송 오류(management() - except Exception as e)
- 계산된 결과를 클라이언트로 전송하는 과정에서 오류 발생 시 예외 포착
- 해당 오류를 로그 파일에 기록, result_queue.tast_done()을 호출해 해당 작업이 완료 되었음을 큐에 알림

③ 수식 계산 오류
- 계산 함수 내에 발생하는 모든 예외를 포착 (division by zero)
- 오류 메시지 출력 후 오류내용을 클라이언트에 전송

⊙ Client
① 전송 오류(send_expressions() - except Exception as e)
- 수식을 서버로 전송하는 중에 발생하는 모든 예외 포착
- 오류 내용을 로그 파일과 콘솔에 출력

② 수신 오류
- 서버로부터 결과를 수신하는 중 발생하는 모든 예외 포착
- 오류 내용을 로그 파일과 콘솔에 출력


6. Additional Comments (팀플 날짜 기록)
2024/10/24
과제 시작
알고리즘 작성
소켓 연결

2024/10/25
수식텍스트 파일 읽기
계산 코드 작성

2024/10/26 ~ 10/28
파싱트리
서버 코드 작성(thread 3가지 구현)
재전송 알고리즘 추가
오류 검출 및 디버깅 -> 해결
