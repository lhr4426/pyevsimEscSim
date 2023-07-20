# pyevsimEscSim

일단 뭐라도 하자
1. 10 * 10 크기의 맵을 만든다
2. 일단 한 모델이라도 만들어서 랜덤으로 이동하게 한다
3. 가장 빠른 시간 내에 탈출하는게 목표임

Game Model
init : 맵을 만들고 탈출구를 설정함
NPC Gen : NPC들을 
만듬


NPC Model
init : 초기 위치, 이동 큐를 만듬

게임 규칙
1. 처음에 500점으로 시작함
2. 한 턴이 지날때마다 1씩 빠짐
3. 다른 유닛이랑 부딛치면 50씩 빠짐
4. 가장 많은 점수가 남아야됨
5. 그리드세계 밖으로 나가면 50씩 빠짐
6. 제대로 문으로 탈출하면 +100점

### 07.17 만든 내용
- 게임 모델이랑 NPC 모델 틀만 짜둠
- 게임 모델은 생성시 바로 맵 만들고 NPC 생성해서 엮음
- 이때 NPC들이 처음부터 부딛치지 않도록, 게임모델이 위치정보를 다 가지고있도록 함

#### 내일 해야할거
- 선택 큐 만들어서 어떻게 움직였는지 확인해야함
- 가장 높은 선택을 잇도록 해야함

### 07.19 만든 내용
- 이동 로그랑 점수 로그 만듬 (NPCModel.move_log랑 score_log)
- 에포크 기능 추가
- 이제 움직이는거까지는 어떻게 됨 
- 에포크 여러번일때 마지막 점수가 최고였던 결과를 따라가도록 함 (NPCModel.make_choice())
- 근데 무조건은 아니고 확률적으로 따라가도록
- 가장 점수가 높았던 이동 로그를 txt파일로 남기도록 했음 (GameModel에서)
- 의미없이 반대 방향으로 가는걸 막음 (NPCModel.remove_opposite_move())
- 위의 함수 만들어서 조금 성능이 괜찮아진거같음

### 해결된 문제점
- 맵을 매번 새로 그릴건데, 배경 맵이랑 그린 후의 맵이 주소가 똑같아서 초기화가 안됨
- 매번 새로그리는 대신 이전 위치부분을 'ㅁ'로 다시 바꾸는걸로 해결함

### 해결되지 않은 문제점
- 최종 점수가 가장 높은 이동 로그를 따라가다보니까 늘 최선의 선택은 아닐수 있음
- 매 회차에서 해당 이동순서 기준 가장 좋은 선택을 해야할지 고민중
- 같은 점수라면 더 짧은 이동횟수로 문까지 도달한게 더 좋은 결과임
- 생각보다 정확도가 많이 떨어짐;

#### 내일 해야할거
- 여러 유닛들을 생성해서 잘 되나 해봐야함

### 07.20 만든 내용
- 구조 좀 깔끔하게 다시 정리해야될듯;
- 1 에포크 시작할때 GameModel이 NPCModel한테 신호를 주는건 필요함
- 이동횟수 다하거나 방 탈출했을때 NPCModel이 GameModel한테 Epoch_end를 보내야할까?
- 뭔가 이상함 다시짜야될거같음 -> 0720_new에 다시짰음 내일 내로 문제 발견 안되면 예전버전 지울거임
- 돌아가기는 하는데 자꾸 동시에 도착할때 멈춰버림
