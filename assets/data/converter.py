import re
import yaml
import os
import argparse
from urllib.parse import urlparse, urljoin
import requests
from requests.exceptions import Timeout, ConnectionError
from bs4 import BeautifulSoup
import socket
import concurrent.futures
from PIL import Image
from io import BytesIO

def get_domain(url):
    try:
        return urlparse(url).netloc
    except:
        return None

def extract_icon(url):
    """
    智能提取网站图标，按以下优先级尝试：
    1. HTML中定义的较大尺寸图标
    2. 标准favicon.ico
    3. Google图标服务
    4. 域名映射的默认图标
    """
    domain = get_domain(url)
    if not domain:
        return "link"
    
    # 1. 尝试从HTML中提取高质量图标
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有可能的图标标签
            icon_candidates = []
            
            # 查找<link>标签中的图标
            for link in soup.find_all('link'):
                rel = link.get('rel', [])
                if isinstance(rel, str):
                    rel = [rel]
                rel = [r.lower() for r in rel]
                
                if 'icon' in rel or 'shortcut icon' in rel:
                    href = link.get('href')
                    if href:
                        # 处理相对路径
                        if href.startswith('//'):
                            href = f"https:{href}"
                        elif not href.startswith('http'):
                            href = urljoin(url, href)
                        
                        # 尝试获取图标大小
                        size = link.get('sizes')
                        width = 0
                        if size and 'x' in size:
                            try:
                                width = int(size.split('x')[0])
                            except:
                                pass
                        
                        icon_candidates.append((href, width))
            
            # 按尺寸排序，优先选择较大的图标
            if icon_candidates:
                icon_candidates.sort(key=lambda x: x[1], reverse=True)
                best_icon = icon_candidates[0][0]
                
                # 验证图标有效性
                try:
                    icon_resp = requests.head(best_icon, timeout=2)
                    if icon_resp.status_code == 200:
                        return best_icon
                except:
                    pass
    
    except (Timeout, ConnectionError, socket.gaierror, Exception) as e:
        pass
    
    # 2. 尝试标准favicon.ico
    icon_url = f"https://{domain}/favicon.ico"
    try:
        response = requests.head(icon_url, timeout=2)
        if response.status_code == 200:
            # 检查文件大小，过小的可能是低质量图标
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > 1024:  # 大于1KB
                return icon_url
    except:
        pass
    
    # 3. 使用Google图标服务作为后备
    try:
        google_icon = f"https://www.google.com/s2/favicons?sz=64&domain={domain}"
        response = requests.head(google_icon, timeout=2)
        if response.status_code == 200:
            return google_icon
    except:
        pass
    
    # 4. 域名映射的默认图标
    domain_parts = domain.split('.')
    if len(domain_parts) > 1:
        name_part = domain_parts[-2].lower()
        if name_part == 'github':
            return 'github'
        elif name_part == 'gitlab':
            return 'gitlab'
        elif name_part == 'bitbucket':
            return 'bitbucket'
        elif name_part == 'react':
            return 'react'
        elif name_part == 'vuejs':
            return 'vuejs'
        elif name_part == 'angular':
            return 'angular'
        elif name_part == 'figma':
            return 'figma'
        elif name_part == 'youtube':
            return 'youtube'
        elif name_part == 'stackoverflow':
            return 'stack-overflow'
        elif name_part == 'twitter':
            return 'twitter'
        elif name_part == 'facebook':
            return 'facebook'
        elif name_part == 'linkedin':
            return 'linkedin'
    
    # 5. 默认回退图标
    return "link"

def parse_chrome_bookmarks(html_content):
    """解析Chrome/Edge导出的HTML书签文件"""
    # 初始化类别栈（用于跟踪当前文件夹层级）
    category_stack = []
    categories = {}
    
    # 正则表达式模式
    folder_start_pattern = re.compile(r'<DT><H3[^>]*>(.*?)</H3>')
    folder_end_pattern = re.compile(r'</DL><p>')
    bookmark_pattern = re.compile(r'<DT><A HREF="(.*?)"[^>]*>(.*?)</A>')
    
    lines = html_content.split('\n')
    current_folder = None
    ignore_top_level = False
    
    for line in lines:
        # 检查是否开始一个新文件夹
        folder_match = folder_start_pattern.search(line)
        if folder_match:
            folder_name = folder_match.group(1)
            
            # 检测是否为Edge的"收藏夹栏"顶级文件夹
            if not category_stack and folder_name.lower() in ['收藏夹栏', 'favorites bar']:
                ignore_top_level = True
                continue
                
            folder_id = folder_name.lower().replace(' ', '-')
            
            # 创建新类别
            category = {
                'id': folder_id,
                'name': folder_name,
                'icon': 'folder',  # 默认文件夹图标
                'sections': []
            }
            
            # 处理嵌套层级
            if ignore_top_level:
                # Edge导出格式 - 忽略顶级文件夹
                if len(category_stack) == 0:
                    # 一级类别
                    categories[folder_id] = category
                    current_folder = category
                elif len(category_stack) == 1:
                    # 二级类别（转换为sections）
                    section = {
                        'name': folder_name,
                        'websites': []
                    }
                    category_stack[0]['sections'].append(section)
                    current_folder = section
                else:
                    # 三级类别 - 合并到父级sections
                    if 'websites' not in category_stack[-1]:
                        category_stack[-1]['websites'] = []
                    current_folder = category_stack[-1]
            else:
                # Chrome导出格式 - 正常层级处理
                if len(category_stack) == 0:
                    # 一级类别
                    categories[folder_id] = category
                    current_folder = category
                elif len(category_stack) == 1:
                    # 二级类别（sections）
                    section = {
                        'name': folder_name,
                        'websites': []
                    }
                    category_stack[0]['sections'].append(section)
                    current_folder = section
                else:
                    # 三级类别 - 合并到父级sections
                    if 'websites' not in category_stack[-1]:
                        category_stack[-1]['websites'] = []
                    current_folder = category_stack[-1]
            
            # 将此文件夹压入栈
            category_stack.append(current_folder)
        
        # 检查是否结束一个文件夹
        if folder_end_pattern.search(line):
            if category_stack:
                category_stack.pop()
                if category_stack:
                    current_folder = category_stack[-1]
                else:
                    current_folder = None
        
        # 检查是否为书签
        bookmark_match = bookmark_pattern.search(line)
        if bookmark_match and current_folder:
            url = bookmark_match.group(1)
            name = bookmark_match.group(2)
            
            # 添加到当前文件夹的网站列表
            website_entry = {
                'name': name,
                'url': url,
                'icon': 'loading',  # 初始状态
                'description': f"{name} - {get_domain(url) or '未知域名'}"
            }
            
            if 'websites' in current_folder:
                current_folder['websites'].append(website_entry)
            elif 'sections' in current_folder and current_folder['sections']:
                current_folder['sections'][0]['websites'].append(website_entry)
            else:
                if 'sections' not in current_folder:
                    current_folder['sections'] = []
                section = {
                    'name': '默认分类',
                    'websites': []
                }
                current_folder['sections'].append(section)
                section['websites'].append(website_entry)
    
    return list(categories.values())

def fetch_icons_concurrently(yaml_data, max_workers=10):
    """使用线程池并发获取网站图标"""
    websites = []
    
    # 收集所有网站条目
    for category in yaml_data:
        if 'sections' in category:
            for section in category['sections']:
                if 'websites' in section:
                    for website in section['websites']:
                        websites.append(website)
        elif 'websites' in category:
            for website in category['websites']:
                websites.append(website)
    
    # 使用线程池并发获取图标
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_website = {executor.submit(extract_icon, website['url']): website for website in websites}
        
        total = len(websites)
        completed = 0
        
        for future in concurrent.futures.as_completed(future_to_website):
            website = future_to_website[future]
            try:
                icon = future.result()
                website['icon'] = icon
            except Exception as e:
                print(f"获取 {website['url']} 的图标时出错: {e}")
                website['icon'] = "link"  # 默认图标
            
            completed += 1
            if completed % 10 == 0:
                print(f"已获取 {completed}/{total} 个图标")

def convert_bookmark_to_yaml(bookmark_file, output_file):
    with open(bookmark_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print("解析书签文件...")
    yaml_data = parse_chrome_bookmarks(html_content)
    
    print("正在获取网站图标... 这可能需要一些时间")
    fetch_icons_concurrently(yaml_data)
    
    # 写入YAML文件
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    
    print(f"转换完成，已保存到 {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='将Chrome/Edge书签转换为YAML格式')
    parser.add_argument('--input', '-i', required=True, help='Chrome/Edge书签HTML文件路径')
    parser.add_argument('--output', '-o', default='websites.yaml', help='输出YAML文件路径')
    parser.add_argument('--workers', '-w', type=int, default=10, help='并发获取图标的线程数')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误：输入文件 '{args.input}' 不存在")
        exit(1)
    
    # 检查并安装依赖
    try:
        import yaml
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("缺少必要的库，正在自动安装...")
        import subprocess
        subprocess.check_call(["pip", "install", "pyyaml requests beautifulsoup4"])
        import yaml
        import requests
        from bs4 import BeautifulSoup
    
    convert_bookmark_to_yaml(args.input, args.output)