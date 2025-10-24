from typing import Optional, Dict, Any, Union, Tuple
from bs4 import BeautifulSoup
import requests
from urllib.parse import quote
import re
import json
import random
import logging

# 导入logger
from .logging_config import logger
# 导入缓存管理器
from .request_cache import RequestCache

# 初始化全局缓存管理器
_cache_manager = RequestCache()

def parse_music_data(html_content: str) -> list:
    """
    解析给定的 HTML 内容，提取歌曲信息。

    此函数会遵循以下步骤：
    1. 找到 class 为 "card-text" 的 <div> 元素。
    2. 在该元素内，查找所有包含歌曲信息的 <div class="row">。
    3. 从每个歌曲行中，提取 <a> 标签的链接 (href) 和文本内容。
    4. 将提取的歌曲名和歌手名组合成一个列表。
    5. 最终返回一个包含所有歌曲信息的列表。

    Args:
        html_content: 包含 HTML 代码的字符串。

    Returns:
        一个列表，每个元素是一个字典，包含 "link" 和 "text" 键。
        例如: [{"link": "/music/39466", "text": ["园游会", "周杰伦"]}]
    """
    soup = BeautifulSoup(html_content, "html.parser")
    data_list = []
    # 1. 首先找到 <div class="card-text">
    card_text_div = soup.find("div", class_="card-text")
    if not card_text_div:
        return data_list
    # 2. 然后找到所有的子元素 <div class="row">
    #    为了更精确地定位到含歌曲的行，我们直接查找包含歌曲链接的<a>标签
    song_rows = card_text_div.find_all("a", class_="music-link")
    for row_tag in song_rows:
        # 3. 提取<a href=包含的链接
        link = row_tag.get("href")
        # 4. 提取文本 "园游会" 和 "周杰伦"
        song_title = row_tag.find("span", class_="music-title").get_text(strip=True)
        artist_name = row_tag.find("small").get_text(strip=True)
        if link and song_title and artist_name:
            data_list.append({"link": link, "text": [song_title, artist_name]})
    # 5. 返回最终的列表
    return data_list


def parse_play_data(html_content: str) -> list:
    soup = BeautifulSoup(html_content, "html.parser")
    data_list = []
    # 1. 首先找到 <div class="card-text">
    card_text_div = soup.find("div", class_="card-text")
    if not card_text_div:
        return data_list
    # 2. 然后找到所有的子元素 <div class="row">
    #    为了更精确地定位到含歌曲的行，我们直接查找包含歌曲链接的<a>标签
    song_rows = card_text_div.find_all("a", class_="music-link")
    for row_tag in song_rows:
        # 3. 提取<a href=包含的链接
        link = row_tag.get("href")
        # 4. 提取文本 "园游会" 和 "周杰伦"
        song_title = row_tag.find("span", class_="music-title").get_text(strip=True)
        artist_name = row_tag.find("small").get_text(strip=True)
        if link and song_title and artist_name:
            data_list.append({"link": link, "text": [song_title, artist_name]})
    # 5. 返回最终的列表
    return data_list


def extract_app_data(html_content: str) -> tuple:
    """
    从 <script> 标签内容中提取 window.appData 的 JSON 对象。

    Args:
        script_content: 包含 "window.appData = {...};" 的完整脚本字符串。

    Returns:
        一个包含解析后数据的 Python 字典。如果未找到，则返回 None。
    """
    soup = BeautifulSoup(html_content, "html.parser")
    lrc_div = soup.find('div', id='content-lrc')
    lrc_content = ''
    # 检查是否找到了元素
    if lrc_div:
        # 提取并打印内容
        # 使用 .get_text() 并指定 separator='\n' 可以将 <br /> 转换成换行符
        lrc_content = lrc_div.get_text(separator='\n')
    # 找到 script 标签
    script_tags = soup.find_all('script', type="text/javascript")
    # 检查是否找到了标签
    if script_tags and len(script_tags) > 0:
        for script_tag in  script_tags:
            # 提取脚本内容
            script_content = script_tag.string
            # 使用正则表达式查找 window.appData = 和 ; 之间的内容
            # re.DOTALL 标志让 . 可以匹配包括换行符在内的任意字符
            match = re.search(r"window\.appData\s*=\s*({.*?});", script_content, re.DOTALL)
            if match:
                # group(1) 提取第一个括号内的匹配项，即 JSON 字符串
                json_str = match.group(1)
                try:
                    # 解析 JSON 字符串为 Python 字典
                    # json.loads 会自动处理 \uXXXX 这样的 Unicode 转义字符
                    data = json.loads(json_str)
                    data["lrc"] = lrc_content
                    return data
                except json.JSONDecodeError as e:
                    logger.error(f"解析JSON时出错: {e}")
                    return None
    return None


def gequbao_request(
    path: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    # 核心改动：允许 data 是一个字典或一个原始字符串
    data: Optional[Union[Dict[str, Any], str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    use_cache: bool = True,
    cache_expiry: int | None = None,
) -> Optional[requests.Response]:
    """
    在 "歌曲宝" 网站上发送指定方法的 HTTP 请求，并返回响应对象。
    
    支持智能缓存:
    1. GET 请求: URL 匹配即命中缓存
    2. POST 请求: URL + Body 匹配才命中缓存
    3. 缓存有效期 24 小时
    4. 过期后网络失败时返回过时缓存

    Args:
        path (str): 请求的路径 (例如 "/s/" 或 "/api/play-url")。
        method (str): HTTP 请求方法 ('GET' 或 'POST')。默认为 'GET'。
        headers (dict, optional): HTTP 请求头。默认为 None。
        cookies (dict, optional): 请求中要携带的 cookie。默认为 None。
        params (dict, optional): GET 请求的查询参数。默认为 None。
        data (dict or str, optional): POST 请求的表单数据或原始字符串。默认为 None。
        json_data (dict, optional): POST 请求的 JSON 数据。默认为 None。
        use_cache (bool): 是否使用缓存。默认为 True。

    Returns:
        requests.Response or None: 如果请求成功，返回 Response 对象；
                                   如果发生网络或HTTP错误，则返回 None。
    """
    base_url = "https://www.gequbao.com"
    full_url = f"{base_url}{path}"
    
    # 尝试从缓存获取
    cached_response = None
    if use_cache:
        cached_data = _cache_manager.get(
            url=full_url,
            method=method,
            data=data,
            json_data=json_data,
            cache_expiry=cache_expiry
        )
        
        if cached_data:
            is_expired = cached_data.get('is_expired', False)
            
            # 如果缓存未过期，直接返回缓存的响应
            if not is_expired:
                logger.info(f"使用有效缓存: {full_url}")
                return _create_response_from_cache(cached_data)
            else:
                # 缓存已过期，保存以备网络失败时使用
                logger.info(f"缓存已过期，将尝试网络请求: {full_url}")
                cached_response = cached_data
    
    logger.info(f"正在向 URL: {full_url} 发送 {method.upper()} 请求...")
    
    try:
        # requests.request() 是一个更通用的方法，可以简化if/else
        response = requests.request(
            method=method.upper(),
            url=full_url,
            headers=headers,
            cookies=cookies,
            params=params,
            data=data,
            json=json_data,
            timeout=10,
        )
        # 检查请求是否成功 (例如，状态码不是 4xx 或 5xx)
        response.raise_for_status()
        logger.info(f"请求成功，状态码: {response.status_code}")
        
        # 保存到缓存
        if use_cache:
            _save_response_to_cache(
                url=full_url,
                response=response,
                method=method,
                data=data,
                json_data=json_data,
            )
        
        # 成功时返回响应对象
        return response
        
    except requests.exceptions.RequestException as e:
        # 捕获所有 requests 相关的异常
        logger.error(f"网络请求失败: {e}")
        
        # 如果有过期的缓存，返回过期缓存
        if cached_response:
            logger.warning(f"网络请求失败，使用过期缓存: {full_url}")
            return _create_response_from_cache(cached_response)

        raise Exception(f"网络请求失败: {e}")


def _create_response_from_cache(cached_data: Dict[str, Any]) -> requests.Response:
    """
    从缓存数据创建 requests.Response 对象
    
    Args:
        cached_data: 缓存的响应数据
    
    Returns:
        模拟的 Response 对象
    """
    # 创建一个模拟的 Response 对象
    response = requests.Response()
    response.status_code = cached_data.get('status_code', 200)
    response._content = cached_data.get('content', '').encode('utf-8')
    response.headers.update(cached_data.get('headers', {}))
    response.encoding = cached_data.get('encoding', 'utf-8')
    
    return response


def _save_response_to_cache(
    url: str,
    response: requests.Response,
    method: str = "GET",
    data: Optional[Union[Dict[str, Any], str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    将响应保存到缓存
    
    Args:
        url: 请求 URL
        response: requests.Response 对象
        method: 请求方法
        data: POST 请求的表单数据
        json_data: POST 请求的 JSON 数据
    """
    try:
        response_data = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text,
            'encoding': response.encoding,
        }
        
        _cache_manager.set(
            url=url,
            response_data=response_data,
            method=method,
            data=data,
            json_data=json_data,
        )
    except Exception as e:
        logger.error(f"保存响应到缓存失败: {e}")


# 定义通用的请求头和 Cookie
request_headers = {
    "accept": "*",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "referer": "https://www.gequbao.com/",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
}

def search_sound(keyword: str):
    # 2. 将搜索词进行 URL 编码，以处理中文字符或特殊符号
    encoded_term = quote(keyword)
    response = gequbao_request(
        headers=request_headers, path=f"/s/{encoded_term}"
    )
    if response and response.status_code == 200:
        return parse_music_data(response.text)


def play_sound(link: str):
    response = gequbao_request(
        headers=request_headers, path=link, use_cache=False
    )
    if response and response.status_code == 200:
        return extract_app_data(response.text)


def get_play_url(play_id: str) -> Dict:
    response = gequbao_request(
        method="POST",
        headers=request_headers,
        path=f"/api/play-url",
        data={"id": play_id},
        use_cache=False
    )
    if response and response.status_code == 200:
        return response.json()


def api_music_gequbao_search(keyword: str) -> Tuple[Dict, Dict] | None:
    """
    优化的歌曲搜索函数。

    该函数能智能识别关键词是歌手名还是歌曲名，并据此提供更优的播放策略：
    - 如果是歌手名：从该歌手的歌曲中随机选择一首播放。
    - 如果是歌曲名（或无法判断）：直接播放最匹配的歌曲。
    """
    # 1. 搜索歌曲
    sounds = search_sound(keyword)
    if not sounds:
        raise ValueError(f"没有搜索到关于 '{keyword}' 的歌曲, 请更换关键词")

    # 2. 意图识别：判断关键词是歌手还是歌曲
    top_result = sounds[0]
    top_song_title = top_result["text"][0]
    top_artist_name = top_result["text"][1]
    
    # 默认为歌曲搜索
    search_type = 'song'
    
    # 使用 .lower() 进行不区分大小写的比较，更加健壮
    if keyword.lower() == top_artist_name.lower():
        search_type = 'artist'
        logger.info(f"识别到搜索意图: 歌手 ({top_artist_name})")
    # 如果关键词与歌曲名完全匹配，也认为是歌曲搜索
    elif keyword.lower() == top_song_title.lower():
        search_type = 'song'
        logger.info(f"识别到搜索意图: 歌曲 ({top_song_title})")
    else:
        # 对于 "歌手 歌名" 的格式或其他模糊搜索，默认为歌曲搜索
        logger.info(f"识别到搜索意图: 默认为歌曲搜索 (关键词: '{keyword}')")

    # 3. 根据识别的意图选择歌曲
    selected_sound = None
    if search_type == 'artist':
        # 筛选出所有属于该歌手的歌曲
        artist_songs = [s for s in sounds if s["text"][1].lower() == top_artist_name.lower()]
        
        # 如果筛选出结果，则随机选择一首；否则，为保险起见，返回第一首
        if artist_songs:
            selected_sound = random.choice(artist_songs)
            logger.info(f"为歌手 '{top_artist_name}' 随机选择了歌曲: '{selected_sound['text'][0]}'")
        else:
            selected_sound = top_result
            logger.warning(f"未能在结果中筛选出歌手 '{top_artist_name}' 的其他歌曲，返回首个结果。")
            
    else: # search_type == 'song'
        # 直接选择最匹配的结果
        selected_sound = top_result
        logger.info(f"为歌曲 '{top_song_title}' 选择了最匹配的结果。")

    # 4. 获取播放信息和URL
    sound_info = play_sound(selected_sound["link"])
    if sound_info is None:
        return None
    play_url = get_play_url(sound_info["play_id"])
    
    return sound_info, play_url


def search_save():
    import rich
    sounds = search_sound("林俊杰")
    sound_infos = []
    url_infos = []
    for sound in sounds:
        rich.print(sound)
        sound_infos.append(play_sound(sound["link"]))
    for info in sound_infos:
        rich.print(info)
        url_infos.append(get_play_url(info["play_id"]))
    for url_info in url_infos:
        rich.print(url_info)
    with open("林俊杰.json", "w") as f:
        json.dump(
            {
                "sounds": sounds,
                "sound_infos": sound_infos,
                "url_infos": url_infos,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

# --- 主程序入口，演示如何使用上面的函数 ---
if __name__ == "__main__":
    url = get_search_sound_url("林俊杰")
    logger.info(f"搜索结果URL: {url}")

