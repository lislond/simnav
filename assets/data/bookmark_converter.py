import re
import sys
import yaml
import os
import argparse
from urllib.parse import urlparse, urljoin
import requests
from requests.exceptions import Timeout, ConnectionError
from bs4 import BeautifulSoup
import socket
import concurrent.futures
import time

def check_dependencies():
    """检查并安装必要的依赖库"""
    missing_deps = []
    
    try:
        import yaml
    except ImportError:
        missing_deps.append("pyyaml")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        missing_deps.append("beautifulsoup4")
    
    if missing_deps:
        print(f"错误：缺少必要的依赖库：{', '.join(missing_deps)}")
        print("请使用以下命令安装：")
        print(f"pip install {' '.join(missing_deps)}")
        sys.exit(1)

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
        print(f"警告：获取 {url} 的HTML图标时出错: {e}")
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
    except Exception as e:
        print(f"警告：获取 {url} 的favicon.ico时出错: {e}")
        pass
    
    # 3. 使用Google图标服务作为后备
    try:
        google_icon = f"https://www.google.com/s2/favicons?sz=64&domain={domain}"
        response = requests.head(google_icon, timeout=2)
        if response.status_code == 200:
            return google_icon
    except Exception as e:
        print(f"警告：使用Google服务获取 {url} 的图标时出错: {e}")
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
    
    print("正在解析HTML内容...")
    start_time = time.time()
    
    for i, line in enumerate(lines):
        # 每处理1000行显示进度
        if i % 1000 == 0 and i > 0:
            print(f"已处理 {i}/{len(lines)} 行")
        
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
                'description': name  # 不再包含域名
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
    
    end_time = time.time()
    print(f"HTML解析完成，耗时 {end_time - start_time:.2f} 秒")
    
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
    
    total = len(websites)
    print(f"准备获取 {total} 个网站的图标...")
    
    if not websites:
        return
    
    # 使用线程池并发获取图标
    start_time = time.time()
    processed = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_website = {executor.submit(extract_icon, website['url']): website for website in websites}
        
        for future in concurrent.futures.as_completed(future_to_website):
            website = future_to_website[future]
            try:
                icon = future.result()
                website['icon'] = icon
                processed += 1
                
                # 显示进度条
                progress = processed / total
                bar_length = 50
                filled_length = int(bar_length * progress)
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                elapsed = time.time() - start_time
                eta = (elapsed / processed * (total - processed)) if processed > 0 else 0
                
                print(f"\r进度: [{bar}] {progress:.1%} | 已处理: {processed}/{total} | 用时: {elapsed:.1f}s | 预计剩余: {eta:.1f}s", end='')
                
            except Exception as e:
                print(f"\n错误：获取 {website['url']} 的图标时出错: {e}")
                website['icon'] = "link"  # 默认图标
    
    print(f"\n图标获取完成，总耗时 {time.time() - start_time:.2f} 秒")

def convert_bookmark_to_yaml(input_file, output_file):
    print(f"开始处理: {input_file}")
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：输入文件 '{input_file}' 不存在")
        sys.exit(1)
    
    # 检查文件是否可读
    if not os.access(input_file, os.R_OK):
        print(f"错误：没有读取文件 '{input_file}' 的权限")
        sys.exit(1)
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"创建目录: {output_dir}")
        except Exception as e:
            print(f"错误：无法创建目录 '{output_dir}': {e}")
            sys.exit(1)
    
    # 检查输出目录是否可写
    if output_dir and not os.access(output_dir, os.W_OK):
        print(f"错误：没有写入目录 '{output_dir}' 的权限")
        sys.exit(1)
    
    # 读取HTML文件
    print(f"读取HTML文件: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        print(f"文件大小: {len(html_content) / 1024:.2f} KB")
    except Exception as e:
        print(f"错误：读取文件时出错: {e}")
        sys.exit(1)
    
    # 解析书签
    yaml_data = parse_chrome_bookmarks(html_content)
    
    if not yaml_data:
        print("警告：解析结果为空，可能是书签文件格式不正确")
        sys.exit(1)
    
    # 计算总网站数
    total_websites = sum(len(s.get('websites', [])) for c in yaml_data for s in c.get('sections', []))
    print(f"解析完成，发现 {len(yaml_data)} 个分类，共 {total_websites} 个网站")
    
    # 获取图标
    if total_websites > 0:
        fetch_icons_concurrently(yaml_data)
    else:
        print("没有找到网站，跳过图标获取")
    
    # 写入YAML文件
    print(f"写入YAML文件到 {output_file}...")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print(f"YAML文件已保存，大小: {os.path.getsize(output_file) / 1024:.2f} KB")
    except Exception as e:
        print(f"错误：写入YAML文件时出错: {e}")
        sys.exit(1)
    
    print(f"\n转换完成！🎉\n结果已保存到: {output_file}")
    print(f"处理统计:")
    print(f"  分类数: {len(yaml_data)}")
    print(f"  网站总数: {total_websites}")
    print(f"  成功获取图标: {sum(1 for c in yaml_data for s in c.get('sections', []) for w in s.get('websites', []) if w['icon'] != 'link')}")
    print(f"  使用默认图标: {sum(1 for c in yaml_data for s in c.get('sections', []) for w in s.get('websites', []) if w['icon'] == 'link')}")

if __name__ == "__main__":
    # 检查依赖
    check_dependencies()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='将Chrome/Edge书签转换为YAML格式')
    parser.add_argument('input_file', help='Chrome/Edge书签HTML文件路径')
    parser.add_argument('output_file', nargs='?', default='websites.yaml', help='输出YAML文件路径（可选，默认为websites.yaml）')
    parser.add_argument('--workers', '-w', type=int, default=10, help='并发获取图标的线程数')
    
    try:
        args = parser.parse_args()
    except argparse.ArgumentError as e:
        print(f"参数错误: {e}")
        parser.print_help()
        sys.exit(1)
    
    # 确保输出文件有扩展名
    if args.output_file and not os.path.splitext(args.output_file)[1]:
        args.output_file += '.yaml'
    
    # 显示欢迎信息
    print("=" * 50)
    print("Chrome/Edge书签转换工具")
    print("=" * 50)
    
    # 开始转换
    convert_bookmark_to_yaml(args.input_file, args.output_file)    