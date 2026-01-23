import requests
import time
import random
import csv

# ================= 配置区 =================
TOKEN = "1243847146" 
COOKIE = "rewardsn=; wxtokenkey=777; ua_id=jywNMpyXm61nZM36AAAAAOXPLDDRiYWF4RdclSg_4zg=; _clck=19d7px|1|g2y|0; wxuin=69146071915197; poc_sid=HGELc2mjP5hyLWDRKYb55_r0-O6Uv-gXrRSNsrlV; mm_lang=zh_CN; cert=TFX8bgsQOjkOm6DzKgLVuWRUFRPIEvB8; _clsk=108l54g|1769178612423|1|1|mp.weixin.qq.com/weheat-agent/payload/record; __wx_phantom_mark__=5NCVqX2UG7; uuid=73f3e97e41f6ee789fdd1460fc478378; rand_info=CAESIIeno2XOvhyyZdjpZmV8c0HoGyVXu0/V5NNThDr3Fu55; slave_bizuin=3693070202; data_bizuin=3693070202; bizuin=3693070202; data_ticket=vsMSZVGMO1MJu8DTs/AaP8TQsTnEp76/iTMTYF5J3irZcizqdex3wBRf7xxFPdip; slave_sid=VlB2TWo1dVdCSkVaSHpsdGs3d0hTRktEREoxTnFnREJhWUExQ0lmWXNsMnlFaUM3YXB2VHBsUjVBVUx0OFNKS1RjRHBvVWNWejFVcEh4YnF2d1JZZjdqU0NsV1hUYnpkc08xN0xnZVlCQXdWM3N1bzFxZWs1YWhQNzZ4QTA5N2xGeHlMUVBvaDhsOFhjTUNR; slave_user=gh_9b1d983b809c; xid=bd75f3c11893506497eef9dee9468b0d"
TARGET_NAME = "公安部刑侦局"
# =========================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Cookie": COOKIE
}

def get_target_fakeid(name):
    url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"
    params = {
        "action": "search_biz",
        "begin": "0",
        "count": "5",
        "query": name,
        "token": TOKEN,
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1"
    }
    
    print(f"🔍 正在搜索公众号: {name} ...")
    try:
        resp = requests.get(url, params=params, headers=HEADERS)
        data = resp.json()
        
        if "base_resp" in data and data["base_resp"]["ret"] == 200003:
            print("❌ Token 或 Cookie 已失效！请重新去浏览器F12复制。")
            return None

        for item in data.get("list", []):
            if item["nickname"] == name:
                print(f"✅ 找到目标! FakeID: {item['fakeid']}")
                return item["fakeid"]
        
        print("❌ 未找到该公众号，请检查名称是否正确。")
        return None
    except Exception as e:
        print(f"❌ 搜索请求出错: {e}")
        return None

def get_article_links(fakeid):
    appmsg_url = "https://mp.weixin.qq.com/cgi-bin/appmsg"
    file_name = "url_(204-300).txt"
    
    # === 修改点 1: 设置起始页和结束页 ===
    START_PAGE = 204  # 从第 XX 页开始抓（对应 begin=250）
    END_PAGE = 300   # 抓到第 XX 页自动停止（你可以改大）
    
    print(f"\n🚀 开始采集文章链接 (从第 {START_PAGE} 页开始)")
    print(f"📂 模式：追加模式 (新数据将添加到 {file_name} 末尾)")
    
    # === 修改点 2: 使用 'a' (append) 模式打开文件，防止覆盖之前的数据 ===
    with open(file_name, "a", encoding="utf-8") as f:
        
        for i in range(START_PAGE, END_PAGE):
            print(f"\n📄 [进度] 正在抓取第 {i} 页 (begin={i*5})...")
            
            params = {
                "token": TOKEN,
                "lang": "zh_CN",
                "f": "json",
                "ajax": "1",
                "action": "list_ex",
                "begin": str(i * 5),
                "count": "5",
                "query": "",
                "fakeid": fakeid,
                "type": "9",
            }
            
            try:
                resp = requests.get(appmsg_url, params=params, headers=HEADERS)
                data = resp.json()
                
                # 检查频率限制 (Ret 200013 是封禁警告)
                ret_code = data.get("base_resp", {}).get("ret")
                if ret_code == 200013:
                    print("\n🛑 严重警告：触发微信频率限制 (Ret 200013)！")
                    print("🛑 请立即停止脚本，并等待 1-4 小时后再试，否则账号会被关小黑屋。")
                    break
                
                # 检查是否 Token 失效
                if ret_code == 200003:
                    print("\n❌ Cookie/Token 已过期，请重新获取。")
                    break

                msg_list = data.get("app_msg_list")
                if not msg_list:
                    print("✅ 已无更多文章，采集结束。")
                    break

                count = 0
                for item in msg_list:
                    link = item["link"]
                    title = item["title"]
                    f.write(link + "\n")
                    count += 1
                    print(f"   - {title}")
                
                # === 修改点 3: 升级版防封延时策略 ===
                
                # 策略 A: 每抓完 5 页，来一次“大休息” (30-60秒)
                if i > START_PAGE and i % 5 == 0:
                    long_sleep = random.randint(30, 60)
                    print(f"☕ 抓取了 5 页，休息 {long_sleep} 秒防风控...")
                    time.sleep(long_sleep)
                else:
                    # 策略 B: 普通翻页，间隔 10-15 秒 (比之前的 3-6 秒更安全)
                    short_sleep = random.randint(10, 15)
                    print(f"⏳ 等待 {short_sleep} 秒...")
                    time.sleep(short_sleep)
                
            except Exception as e:
                print(f"❌ 请求页码 {i} 失败: {e}")
                # 出错后多休息一会儿再试
                time.sleep(20) 
                continue

    print(f"\n🎉 采集结束！数据已追加至 {file_name}")

if __name__ == "__main__":
    fakeid = get_target_fakeid(TARGET_NAME)
    if fakeid:
        get_article_links(fakeid)