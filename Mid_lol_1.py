## 필요한 라이브러리 호출
import pandas as pd
import plotly.express as px
import requests
import time
from tqdm import tqdm

## 길어서 안보이는 컬럼 표시
pd.options.display.max_columns = None

## 밀리 세컨드(ms) -> 분(m) 초(s)
def msTOm(ms):
    m = ms // 60000 
    s = (ms - m * 60000) // 1000
    return(f'{m}분 {s}초')
   
## 챌린저 5000게임 불러오고 결측치 제거 
df = pd.read_parquet("data/df.match.gzip")
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


dragon_count = 0        ## 첫 용 처치 판수 총합
blue_dragon_count = 0   ## 블루 진영 첫 용 처치 판수
red_dragon_count = 0    ## 레드 진영 첫 용 처치 판수
herald_count = 0        ## 첫 전령 처치 판수 총합
blue_herald_count = 0   ## 블루 진영 첫 전령 처치 판수
red_herald_count = 0    ## 레드 진영 첫 전령 처치 판수
dragon_gold_diff = 0
herald_gold_diff = 0
except_count = 0


for i in range(0,len(df_2)-1,2):
    if ((df_2.loc[i]["dragon_first"] == True) & (df_2.loc[i+1]["riftHerald_first"] == True)) :
        dragon_count += 1
        if(df_2.loc[i]["win"] & df_2.loc[i]["dragon_first"]):
            blue_dragon_count +=1
            dragon_gold_diff += df_2.loc[i+1]["gold_spent"]  / df_2.loc[i]["gold_spent"] * 100
            if(dragon_gold_diff<0):
                except_count += 1
                
        elif(df_2.loc[i+1]["win"] & df_2.loc[i+1]["riftHerald_first"]):
            red_herald_count += 1
            dragon_gold_diff += df_2.loc[i]["gold_spent"] / df_2.loc[i+1]["gold_spent"]  * 100
            if(dragon_gold_diff<0):
                except_count += 1
            
    if ((df_2.loc[i]["riftHerald_first"] == True) & (df_2.loc[i+1]["dragon_first"] == True)):
        herald_count += 1
        if(df_2.loc[i]["win"] & df_2.loc[i]["riftHerald_first"]):
            blue_herald_count += 1
            herald_gold_diff += df_2.loc[i+1]["gold_spent"]  / df_2.loc[i]["gold_spent"] * 100
            if(herald_gold_diff<0):
                except_count += 1
        elif(df_2.loc[i+1]["win"] & df_2.loc[i+1]["dragon_first"]):
            red_dragon_count += 1
            herald_gold_diff += df_2.loc[i]["gold_spent"] / df_2.loc[i+1]["gold_spent"]  * 100
            if(herald_gold_diff<0):
                except_count += 1
          
dragon_blue = round(blue_dragon_count / dragon_count * 100,2)
herald_red = round(red_herald_count / dragon_count * 100,2)
gold_diff_1 = round(100-dragon_gold_diff/dragon_count,2)
dragon_red = round(red_dragon_count / herald_count * 100,2)
herald_blue = round(blue_herald_count / herald_count * 100,2)
gold_diff_2 = round(100-herald_gold_diff/herald_count,2)

data = pd.DataFrame(columns=["Team Color","first_dragon","first_herald"])
data.loc[0] = ["Blue Win Rate",dragon_blue,herald_blue]
data.loc[1] = ["Red Win Rate",herald_red,dragon_red]
data.loc[2] = ["Gold Spent Diff",gold_diff_1,gold_diff_2]


y = [str(data["first_dragon"][0])+"%",str(data["first_dragon"][1])+"%",str(data["first_dragon"][2])+"%"]
fig = px.bar(data, x="Team Color", y="first_dragon",color="Team Color",text=y,title="Blue - First Dragon, Red - First Herald")
fig.show()

y = [str(data["first_herald"][0])+"%",str(data["first_herald"][1])+"%",str(data["first_herald"][2])+"%"]
fig = px.bar(data, x="Team Color", y="first_herald",color="Team Color", text=y,title="Blue - First Herald, Red - First Dragon")
fig.show()
