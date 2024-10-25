1조 조원 구성 및 역할

20203043 권수현 - 

20203058 남태인 - 

20203072 안민호 – 



1. 프로그램 구성요소 : data.py, client.py

◆ data.py 구성요소
①
②
③
④
⑤

◆ client.py 구성요소
① 
② 
③
④

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
	server.py가 업로드된 디렉터리에서 python3 data.py로 Data server를 실행한다.

⑦ 로컬에서 powershell 터미널 6개를 열어 터미널 2개는 python3 cache.py로 캐시 서버를 실행시키고, 나머지 터미널 4개는 python3 client.py로 client를 실행한다. (vscode에서 실행해도 됨)
	
⑧ 2개의 Cache server와 4개의 client가 모두 연결되면 프로그램이 실행된다.

☆주의할 점 : 



3. 프로그램 실행환경 및 실행방법 설명


4. 서버의 thread 관리 및 작업 대기 리스트의 선정 알고리즘에 대한 설명 작성

⦁ 알고리즘 시나리오

5. Error or Additional Message Handling
▶ Additional Message Handling

⊙ Data Server
① 
⊙ Client
①

▶ Error Handling (Exception 처리 포함)

⊙ Data Server
①

⊙ Client
①



6. Additional Comments (팀플 날짜 기록)
2024/10/24
과제 시작
