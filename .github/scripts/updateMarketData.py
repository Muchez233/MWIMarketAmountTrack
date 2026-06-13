import urllib.request
import json
import time
import os
import sys

#下载所有
def getMarketJson():
    try:
        # 1. 创建请求对象（可以在此处添加请求头以应对反爬）
        req = urllib.request.Request(JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})        
        # 2. 发送请求并获取响应
        with urllib.request.urlopen(req, timeout=10) as response:
            # 3. 检查状态码是否成功
            if response.status == 200:
                # 4. 读取响应体并解析 JSON
                json_data = json.loads(response.read().decode('utf-8'))
                return json_data
            else:
                print(f"请求失败，状态码：{response.status}")
                return None;
    except Exception as e:
        print(f"请求发生异常: {e}")
        return None;
#清除超过7天数据
def cleanTimeoutData():
    seven_days_ago = time.time()- (7 * 24 * 60 * 60)
    # 遍历目标目录
    for filename in os.listdir(DIR_PATH):
        # 仅处理 .json 文件
        if filename.endswith(".json"):
            try:
                # 提取文件名中的时间戳（去掉 .json 后缀）
                timestamp_str = filename.replace(".json", "")
                file_timestamp = float(timestamp_str)
                
                # 判断时间戳是否超过7天
                if file_timestamp < seven_days_ago:
                    file_path = os.path.join(DIR_PATH, filename)
                    os.remove(file_path)
                    print(f"已删除过期文件: {file_path}")
            except ValueError:
                # 如果文件名不是合法的时间戳格式，跳过该文件
                print(f"跳过非时间戳格式的文件: {filename}")
            except Exception as e:
                # 捕获其他可能的异常（如权限不足、文件被占用等）
                print(f"删除文件 {filename} 时发生错误: {e}")

#生成文件列表共vue调用
def generateIndexJson():
    files=[]
    for filename in os.listdir(DIR_PATH):
    # 仅处理 .json 文件
        if filename.endswith(".json"):
            try:
                # 提取文件名中的时间戳（去掉 .json 后缀）
                timestamp_str = filename.replace(".json", "")
                _ = float(timestamp_str)     
                files.append(filename)        
            except ValueError:
                # 如果文件名不是合法的时间戳格式，跳过该文件
                print(f"跳过非时间戳格式的文件: {filename}")
    with open(os.path.join(DIR_PATH,INDEX_FILE),"w",encoding='utf-8') as f:
        json.dump(files,f, indent=4, ensure_ascii=False)
    return 


def main():
    cleanTimeoutData();

    newMarketJson=getMarketJson();
    if newMarketJson==None:
        return
    newTimestamp=newMarketJson["timestamp"];
    filename=str(newTimestamp)+".json" 
    if filename in os.listdir(DIR_PATH):
        return
    with open(os.path.join(DIR_PATH,filename),'w',encoding='utf-8') as f:
        json.dump(newMarketJson,f, indent=4, ensure_ascii=False)
        print(f"已添加文件:{filename}")
    
    generateIndexJson()

    return


if __name__=="__main__":
    if len(sys.argv)!=2:
        print("Usage: Marketdata Folder (dist/marketdata)")
    else:
        DIR_PATH=sys.argv[1];
        INDEX_FILE=r"index.json"        
        JSON_URL =r"https://www.milkywayidle.com/game_data/marketplace.json"
        main()
    





