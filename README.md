# pyevsimEscSim

1. 10 * 10 크기의 맵을 만든다
2. 랜덤으로 이동하게 함
3. 가장 빠른 시간 내에 탈출하는게 목표

Game Model
init : 맵을 만들고 탈출구를 설정함
NPC Gen : NPC들을 만듬

NPC Model
init : 초기 위치, 이동 큐를 만듬

게임 규칙
1. 처음에 500점으로 시작함
2. 한 턴이 지날때마다 1씩 빠짐
3. 다른 유닛이랑 부딛치면 50씩 빠짐
4. 가장 많은 점수가 남아야됨
5. 그리드세계 밖으로 나가면 50씩 빠짐
6. 제대로 문으로 탈출하면 +100점
