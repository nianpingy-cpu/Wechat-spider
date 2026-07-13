"""封装原有 resume_helper.py 的断点续传逻辑"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)


def normalize_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    return url.replace("http://", "").replace("https://", "")


def generate_remaining(input_file: str, last_url: str, output_file: str = "remaining_urls.txt") -> int:
    """
    根据最后成功处理的 URL，生成剩余任务列表。
    返回剩余 URL 数量。
    """
    input_path = os.path.join(BASE_DIR, input_file)
    output_path = os.path.join(BASE_DIR, output_file)

    if not os.path.exists(input_path):
        return -1

    with open(input_path, "r", encoding="utf-8") as f:
        all_lines = [line.strip() for line in f if line.strip()]

    target_clean = normalize_url(last_url)
    start_index = -1

    for i, line in enumerate(all_lines):
        if target_clean in line:
            start_index = i
            break

    if start_index == -1:
        return -1

    remaining_lines = all_lines[start_index + 1:]

    with open(output_path, "w", encoding="utf-8") as f_out:
        for link in remaining_lines:
            f_out.write(link + "\n")

    return len(remaining_lines)
