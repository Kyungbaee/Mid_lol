import pandas as pd
import plotly.express as px
import requests
import time
from tqdm import tqdm

pd.options.display.max_columns = None

df = pd.read_parquet("data/df.match.gzip")
dragon_4 = df[df["dragon_kill"] >= 4].sort_values("dragon_kill",ascending=False)["game_id"]
df = df.reset_index(drop=True).drop(index=[128,129,3490,4855])
df = df.reset_index(drop=True)
out = []
for i in range(0,len(df)-1,2):
    if df.loc[i]["win"] == df.loc[i+1]["win"]:
        out.append(i)
        out.append(i+1)
df = df.drop(index=out).reset_index(drop=True)

df_2 = df[["game_id","team","win","dragon_first","dragon_kill"
    ,"riftHerald_first","riftHerald_kill","baron_first","baron_kill","gold_spent"]]

df_dragon_4 = df_2.loc[df_2["game_id"].isin(dragon_4)].reset_index(drop=True)

df_dragon4 = pd.DataFrame(columns=["game_id","soul","baron"])
dragon_4_baron_list = []

for match_id in tqdm(dragon_4[:]):
    base_url = f"https://asia.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": "RGAPI-a7a53e7b-e537-4dca-b167-f1a6eb2a8efc"
    }
    response = requests.get(base_url,headers=headers).json()
    try:
        object_list = [response["info"]["frames"][index]["events"] for index in range(len(response["info"]["frames"]))]
        object_soul = [(soul['name'],msTOm(soul["timestamp"]),soul["teamId"]) for object_index in object_list for soul in object_index if soul['type'] == 'DRAGON_SOUL_GIVEN']
        object_baron = [(baron["monsterType"],msTOm(baron["timestamp"]),baron["killerTeamId"]) for object_index in object_list for baron in object_index if 'monsterType' in baron if baron["monsterType"]== "BARON_NASHOR"]
        if (len(object_soul)>0) & (len(object_baron)==1):
            if(object_soul[0][2] != object_baron[0][2]):
                dragon_4_baron_list.append([match_id,object_soul[0],object_baron])
        time.sleep(2)
    except:
        print(match_id)

for index in range(len(dragon_4_baron_list)):
    df_dragon4.loc[index] = [dragon_4_baron_list[index][0],dragon_4_baron_list[index][1],dragon_4_baron_list[index][2]]

test_df = pd.merge(df_dragon4,df_dragon_4,on="game_id",how="left")
test_df = test_df[["game_id","soul","baron","team","win"]]

for number in range(len(test_df)):
    if (test_df.loc[number]["soul"][2] == 200)& (test_df.loc[number]["team"] == "red"):
        test_df.loc[number,"soul"] = test_df.loc[number]["soul"][0]
        test_df.loc[number,"baron"] = "No Kill"
    elif (test_df.loc[number]["soul"][2] == 100)& (test_df.loc[number]["team"] == "blue"):
        test_df.loc[number,"soul"] = test_df.loc[number]["soul"][0]
        test_df.loc[number,"baron"] = "No Kill"
    elif (test_df.loc[number]["soul"][2] == 200)& (test_df.loc[number]["team"] == "blue"):
        test_df.loc[number,"soul"] = "No Soul"
        test_df.loc[number,"baron"] = "Kill"
    elif (test_df.loc[number]["soul"][2] == 100)& (test_df.loc[number]["team"] == "red"):
        test_df.loc[number,"soul"] = "No Soul"
        test_df.loc[number,"baron"] = "Kill"
        
    if (test_df.loc[number,"win"] ):
        test_df.loc[number,"win"] = 1
    elif ~(test_df.loc[number,"win"]):
        test_df.loc[number,"win"] = 0

fig = px.bar(test_df, x="soul", y="win",color="team")
fig.show()

fig = px.bar(test_df, x="baron", y="win",color="team")
fig.show()
