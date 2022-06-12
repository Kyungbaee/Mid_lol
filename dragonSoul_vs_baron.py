## 필요한 라이브러리 호출
import pandas as pd
import plotly.express as px
import requests
import time
from tqdm import tqdm
import cufflinks as cf

# 그래프가 주피터 노트북에서 표시되지 않는다면 아래 설정을 사용해 주세요.
cf.go_offline(connected = True)

# columns 갯수 상관없이 모두 출력
pd.options.display.max_columns = None

## 밀리 세컨드(ms) -> 분(m) 초(s)
def msTOm(ms):
    m = ms // 60000 
    s = (ms - m * 60000) // 1000
    return(f'{m}분 {s}초')

## 챌린저 5000게임 불러오고 결측치 제거  
df = pd.read_parquet("data/df.match.gzip")
dragon_4_game = df[df["dragon_kill"] >= 4].sort_values("dragon_kill",ascending=False)["game_id"]
df = df.reset_index(drop=True).drop(index=[128,129,3490,4855])
df = df.reset_index(drop=True)
out = []
for i in range(0,len(df)-1,2):
    if df.loc[i]["win"] == df.loc[i+1]["win"]:
        out.append(i)
        out.append(i+1)
df = df.drop(index=out).reset_index(drop=True)

## 필요한 컬럼 추출
df_2 = df[["game_id","team","win","dragon_first","dragon_kill"
    ,"riftHerald_first","riftHerald_kill","baron_first","baron_kill","gold_spent"]]

## 처치한 용이 4개 이상인(드래곤의 영혼 획득) 게임 추출
df_dragon_4 = df_2.loc[df_2["game_id"].isin(dragon_4)].reset_index(drop=True)

df_dragon4 = pd.DataFrame(columns=["game_id","soul","baron"])
dragon_4_baron_list = []

# match_id로 Riot Api를 통하여 해당 게임 timeline 받아오기 
for match_id in tqdm(dragon_4_game[:]):
    base_url = f"https://asia.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    headers={
        "User-Agent": "",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": ""
    }
    # 해당 게임 timeline Json으로 get 
    response = requests.get(base_url,headers=headers).json()
    try:
        # timeline json 중 soul과 baron 부분 추출(soul이 있는 경우 + baron 처치 횟수 1인 경우)
        object_list = [response["info"]["frames"][index]["events"] for index in range(len(response["info"]["frames"]))]
        object_soul = [(soul['name'],msTOm(soul["timestamp"]),soul["teamId"]) for object_index in object_list for soul in object_index if soul['type'] == 'DRAGON_SOUL_GIVEN']
        object_baron = [(baron["monsterType"],msTOm(baron["timestamp"]),baron["killerTeamId"]) for object_index in object_list for baron in object_index if 'monsterType' in baron if baron["monsterType"]== "BARON_NASHOR"]
        if (len(object_soul)>0) & (len(object_baron)==1):
            if(object_soul[0][2] != object_baron[0][2]):
                dragon_4_baron_list.append([match_id,object_soul[0],object_baron])
                
        ## Api 호출 2분 동안 120회 제한
        time.sleep(2)
    except:
        ## 예외 처리
        print(match_id)

# timelion에서 추출한 데이터를 데이터 프레임으로 
for index in range(len(dragon_4_baron_list)):
    df_dragon4.loc[index] = [dragon_4_baron_list[index][0],dragon_4_baron_list[index][1],dragon_4_baron_list[index][2]]

# 데이터 프레임 병합
test_df = pd.merge(df_dragon4,df_dragon_4,on="game_id",how="left")
test_df = test_df[["game_id","soul","baron","team","win"]]

# 데이터 전처리 (100 -> 블루 진영, 200 -> 레드 진영)
for number in range(len(test_df)):
    ## 레드 진영이 드래곤의 영혼을 가지고 있는 경우
    if (test_df.loc[number]["soul"][2] == 200) & (test_df.loc[number]["team"] == "red"):
        test_df.loc[number,"soul"] = test_df.loc[number]["soul"][0]
        test_df.loc[number,"baron"] = "No Kill"
        
    ## 블루 진영이 드래곤의 영혼을 가지고 있는 경우
    elif (test_df.loc[number]["soul"][2] == 100) & (test_df.loc[number]["team"] == "blue"):
        test_df.loc[number,"soul"] = test_df.loc[number]["soul"][0]
        test_df.loc[number,"baron"] = "No Kill"
        
    ## 블루 진영이 바론을 처치한 경우
    elif (test_df.loc[number]["soul"][2] == 200) & (test_df.loc[number]["team"] == "blue"):
        test_df.loc[number,"soul"] = "No Soul"
        test_df.loc[number,"baron"] = "Kill"
        
    ## 레드 진영이 바론을 처치한 경우
    elif (test_df.loc[number]["soul"][2] == 100) & (test_df.loc[number]["team"] == "red"):
        test_df.loc[number,"soul"] = "No Soul"
        test_df.loc[number,"baron"] = "Kill"
        
    ## True -> 1, False -> 0 치환
    if (test_df.loc[number,"win"] ):
        test_df.loc[number,"win"] = 1
    elif ~(test_df.loc[number,"win"]):
        test_df.loc[number,"win"] = 0

# 데이터 저장
test_df.to_csv("lol_object_data.csv",index=False)

# 시각화에 사용되는 데이터 프레임
pd.read_csv("lol_object_data.csv")

# 데이터 프레임 시각화 
## (바론 vs 드래곤의 영혼) 드래곤의 영혼 진영별 승률
data_1 = test_df[["soul","team","win"]].set_index(["soul","team"]).sort_values("team")
data_1.iplot(kind="bar",theme='ggplot' ,title="(바론 vs 드래곤의 영혼) 진영별 승률", xTitle="진영별 드래곤의 영혼", yTitle="승리")

## (바론 vs 드래곤의 영혼) 바론 획득 유무 진영별 승률
data_2 = test_df[["baron","team","win"]].set_index(["baron","team"]).sort_values("team")
data_2.iplot(kind="bar",theme='polar', title="(바론 vs 드래곤의 영혼) 진영별 승률", xTitle="진영별 바론 획득 유무", yTitle="승리")
