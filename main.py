import os
import re
import time
import json
import random
import requests
from bs4 import BeautifulSoup
import html2text
from datetime import datetime

class WeChatArticleCrawler:
    def __init__(self, output_dir='police_country_articles'):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # 初始化html2text
        self.h = html2text.HTML2Text()
        self.h.ignore_links = False
        self.h.bypass_tables = False
        self.h.ignore_images = True

        # 基础请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Origin': 'https://mp.weixin.qq.com',
            'Referer': 'https://mp.weixin.qq.com/'
        }
        
        # --- 核心配置区 (JS逆向接口必须参数) ---
        self.cookie = "rewardsn=; wxtokenkey=777"  # 填入抓包的 Cookie
        self.appmsg_token = "" # 填入抓包的 appmsg_token
        # ------------------------------------

    def get_url_params(self, url):
        """基于JS逆向逻辑，从URL中提取 API 必须的参数"""
        params = {}
        # 提取 __biz, mid, idx, sn
        for key in ['__biz', 'mid', 'idx', 'sn']:
            match = re.search(f'{key}=([^&]+)', url)
            if match:
                params[key] = match.group(1)
        return params

    def get_article_stats(self, url_params):
        """获取阅读量、点赞、在看"""
        if not self.cookie or not self.appmsg_token:
            # print("⚠️ 警告: 未配置 Cookie 或 appmsg_token...") 
            return None

        api_url = "https://mp.weixin.qq.com/mp/getappmsgext"
        params = {
            "f": "json", "mock": "", "r": random.random(),
            "uin": "777", "key": "777", "pass_ticket": "", 
            "wxtoken": "777", "devicetype": "Windows-10", 
            "clientversion": "62090529", "__biz": url_params.get('__biz'), 
            "appmsg_token": self.appmsg_token, "x5": "0"
        }
        data = {"is_only_read": "1", "is_temp_url": "0", "appmsg_type": "9", 'reward_uin_count': '0'}
        
        stats_headers = self.headers.copy()
        stats_headers.update({
            "Cookie": self.cookie,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "*/*"
        })

        try:
            resp = requests.post(api_url, params=params, data=data, headers=stats_headers, timeout=5)
            res_json = resp.json()
            if res_json.get("appmsgstat"):
                stat = res_json["appmsgstat"]
                return {
                    "read_num": stat.get("read_num"), 
                    "like_num": stat.get("like_num"), 
                    "old_like_num": stat.get("old_like_num")
                }
            return None
        except Exception as e:
            print(f"请求统计接口出错: {e}")
            return None

    def get_safe_title(self, title):
        safe_title = re.sub(r'[\\/*?:"<>|]', '', title)[:50]
        return safe_title.strip()

    def process_article(self, url):
        try:
            print(f"\n🚀 开始处理文章: {url}")

            # 1. 获取正文 HTML
            response = requests.get(url, headers=self.headers, timeout=15) # 增加超时设置
            if response.status_code != 200:
                raise Exception(f"HTTP状态码错误: {response.status_code}")
                
            response.encoding = 'utf-8'
            html_text = response.text
            soup = BeautifulSoup(html_text, 'html.parser')

            # 2. 提取基础信息
            title_node = soup.find('h1', {'id': 'activity-name'})
            title = title_node.get_text().strip() if title_node else '无标题'
            safe_title = self.get_safe_title(title)
            
            ct_match = re.search(r'var ct = "(\d+)";', html_text)
            if ct_match:
                ts = int(ct_match.group(1))
                date = datetime.fromtimestamp(ts).strftime('%Y年%m月%d日')
            else:
                date = datetime.now().strftime('%Y年%m月%d日')

            print(f"📄 文章标题: {title}")
            print(f"📅 发布时间: {date}")

            # 3. 尝试获取 阅读量
            url_params = self.get_url_params(url)
            stats = self.get_article_stats(url_params)
            
            stats_text = ""
            if stats:
                print(f"📊 阅读: {stats['read_num']} | 点赞: {stats['like_num']}")
                stats_text = f"阅读量: {stats['read_num']}  点赞数: {stats['like_num']}  在看数: {stats['old_like_num']}\n\n"

            # 4. 正文处理
            content_div = soup.find('div', {'id': 'js_content'})
            if not content_div:
                if "验证" in soup.get_text():
                    raise Exception("触发验证码/风控")
                print(f"❌ 未找到文章内容")
                return None

            # 移除干扰项
            for img in content_div.find_all('img'): img.decompose()
            for qr in content_div.find_all('p', style=re.compile(r'text-align:\s*center')):
                if qr.find('img'): qr.decompose()

            # 转 Markdown
            html_content = str(content_div)
            markdown_content = self.h.handle(html_content)

            final_content = f"# {title}\n\n发布时间: {date}\n\n{stats_text}---\n\n{markdown_content}"

            # 保存
            article_filename = f"{safe_title}.md"
            article_path = os.path.join(self.output_dir, article_filename)

            with open(article_path, 'w', encoding='utf-8') as f:
                f.write(final_content)

            print(f"✅ 保存成功: {article_path}")
            return article_path # 返回成功路径

        except Exception as e:
            print(f"❌ 处理出错: {e}")
            return None # 失败返回 None

    def read_urls_from_file(self, file_path='urls.txt'):
        if not os.path.exists(file_path):
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

# --- 辅助函数：追加写入错误文件 ---
def save_wrong_url(url):
    with open('url_wrong.txt', 'a', encoding='utf-8') as f:
        f.write(url + '\n')
    print(f"   └── 📝 已自动记录到 url_wrong.txt")

if __name__ == "__main__":
    crawler = WeChatArticleCrawler()

    # 1. 这里修改为你主要的任务文件 (例如 url_test.txt)
    input_file = 'url_test.txt' 
    
    # 如果文件不存在，提示一下
    if not os.path.exists(input_file):
        print(f"⚠️ 未找到 {input_file}，将尝试读取 urls.txt")
        input_file = 'urls.txt'

    urls = crawler.read_urls_from_file(input_file)
    
    if not urls:
        print(f"没有读取到任务，请检查 {input_file}")
    else:
        print(f"🎯 读取到 {len(urls)} 个任务，开始执行...")
        
        for url in urls:
            # === 核心修改：接收返回值 ===
            result = crawler.process_article(url)
            
            # 如果返回 None，说明处理过程出错，写入错误文件
            if result is None:
                save_wrong_url(url)
            
            # 随机延时
            time.sleep(random.uniform(2, 5))
            
        print("\n🏁 所有任务执行完毕。失败链接已保存在 url_wrong.txt")