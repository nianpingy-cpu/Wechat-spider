import os

# ================= 配置区 =================

# 1. 你的原始文件名为 (请确保这个文件在当前目录下)
INPUT_FILE = "url_(100-150).txt"

# 2. 新生成的任务文件名为 (程序会把剩下的链接存到这里)
OUTPUT_FILE = "remaining_urls.txt"

# 3. 你上次终止时的那个链接 (粘贴在这里)
# 脚本会自动忽略 http 和 https 的区别，只要核心部分匹配即可
LAST_URL = "https://mp.weixin.qq.com/s?__biz=MzI5NzA1NTU0NA==&mid=2649777633&idx=1&sn=35a07c73793f96dac3b7f52136fd01ef&chksm=f4be21b6c3c9a8a0ef135dc8e391390986250b129de0ebafb9a06e0b81c1d70494fab381b8ef#rd"

# =========================================

def normalize_url(url):
    """
    清洗URL，去除 http:// 或 https:// 以及首尾空格，用于模糊匹配
    """
    if not url:
        return ""
    url = url.strip()
    return url.replace("http://", "").replace("https://", "")

def generate_remaining_list():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 错误：在当前目录下找不到 {INPUT_FILE}，请确认文件名。")
        return

    print(f"📂 正在读取 {INPUT_FILE} ...")
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        all_lines = [line.strip() for line in f if line.strip()]

    total_count = len(all_lines)
    target_clean = normalize_url(LAST_URL)
    
    start_index = -1

    # 遍历寻找断点
    for i, line in enumerate(all_lines):
        # 只要核心部分相同，就认为是找到了
        if target_clean in line:
            start_index = i
            break
    
    if start_index != -1:
        # 切片：取找到位置的【下一条】开始的所有内容
        remaining_lines = all_lines[start_index + 1:]
        remaining_count = len(remaining_lines)
        
        print(f"✅ 成功定位断点！")
        print(f"   - 断点行号: 第 {start_index + 1} 行")
        print(f"   - 总链接数: {total_count}")
        print(f"   - 剩余链接: {remaining_count}")
        
        # 写入新文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
            for link in remaining_lines:
                f_out.write(link + "\n")
                
        print(f"\n💾 已将剩余任务保存至: {OUTPUT_FILE}")
        print("💡 接下来，请让你的爬虫脚本读取这个新文件即可！")
        
    else:
        print("⚠️ 警告：在文件中未找到指定的链接！")
        print("   - 请检查 INPUT_FILE 是否正确")
        print("   - 或者该链接可能已经被你删除了")
        print("   - 建议手动检查文件内容")

if __name__ == "__main__":
    generate_remaining_list()