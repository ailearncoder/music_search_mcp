from urllib.parse import quote
from openlist_api import OpenListClient
from datetime import datetime
import requests
import logging
import tempfile
import json
import jwt
import os

def validate_and_get_jwt_info(token, secret_key=None):
    """
    完整验证JWT token并获取信息
    """
    try:
        if secret_key:
            # 使用密钥验证签名
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        else:
            # 不验证签名，只解析
            payload = jwt.decode(token, options={"verify_signature": False})
        
        result = {
            'valid': True,
            'payload': payload
        }
        
        # 检查过期时间
        if 'exp' in payload:
            exp_timestamp = payload['exp']
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            result['exp_timestamp'] = exp_timestamp
            result['exp_datetime'] = exp_datetime
            result['is_expired'] = datetime.now().timestamp() > exp_timestamp
        
        # 检查生效时间（nbf）
        if 'nbf' in payload:
            result['nbf'] = payload['nbf']
        
        # 检查签发时间（iat）
        if 'iat' in payload:
            result['iat'] = payload['iat']
            
        return result
        
    except jwt.ExpiredSignatureError:
        return {'valid': False, 'error': 'Token已过期'}
    except jwt.InvalidTokenError as e:
        return {'valid': False, 'error': f'无效的Token: {e}'}

def load_token() -> str | None:
    if not os.path.exists("/tmp/alist.token"):
        return
    with open("/tmp/alist.token", "r") as f:
        token = f.read().strip()
    validate_result = validate_and_get_jwt_info(token)
    logging.info(f"token 验证结果: {validate_result}")
    if validate_result['valid']:
        return token

def download_file(url: str, path: str) -> bool:
    response = requests.get(url, timeout=10, allow_redirects=True)
    if response.status_code != 200:
        logging.info(f"下载失败: {response.status_code}")
        return False
    with open(path, "wb") as f:
        f.write(response.content)
        return True

def _upload_file(client, local_path: str, remote_path: str) -> bool:
    """
    上传文件到AList
    
    Args:
        client: OpenListClient实例
        local_path: 本地文件路径
        remote_path: 远程文件路径
    
    Returns:
        bool: 上传是否成功
    """
    try:
        with open(local_path, "rb") as f:
            response = client.fs.stream_upload(remote_path, f, as_task=False)
            if response.code != 200:
                logging.error(f"上传文件失败: {local_path} -> {remote_path}, 状态码: {response.code}")
                return False
            logging.info(f"上传文件成功: {remote_path}")
            return True
    except Exception as e:
        logging.error(f"上传文件异常: {local_path} -> {remote_path}, 错误: {e}")
        return False

def get_openlist_base_url() -> str:
    """
    获取 AList 的 OpenList Base URL
    
    Returns:
        str: AList 的 OpenList Base URL
    """
    url = os.getenv("OPENLIST_BASE_URL", "OPENLIST_BASE_URL")
    if url == "OPENLIST_BASE_URL":
        logging.error("未设置 OPENLIST_BASE_URL 环境变量")
        raise Exception("未设置 OPENLIST_BASE_URL 环境变量")
    return url

def save_music(music_info: dict) -> bool:
    """
    保存音乐文件到AList
    
    Args:
        music_info: 音乐信息字典
            {
                "url": url,
                "title": title,
                "artist": artist,
                "artworkUrl": artwork_url,
                "lrcText": lrc,
                "lrcUrl": lrc_url
            }
    
    Returns:
        bool: 保存是否成功
    """
    tmp_dir = None
    try:
        # 创建临时目录
        tmp_dir = tempfile.mkdtemp(prefix="music_", dir="/tmp")
        logging.info(f"创建临时目录: {tmp_dir}")
        
        # 准备艺术家和标题
        artist = music_info.get("artist", "").strip() or "未知"
        title = music_info.get("title", "").strip() or "未知歌曲"
        logging.info(f"准备保存音乐: {artist} - {title}")
        
        # 下载音乐文件
        music_path = os.path.join(tmp_dir, "music.mp3")
        logging.info(f"开始下载音乐文件: {music_info['url']}")
        if not download_file(music_info["url"], music_path):
            logging.error("下载音乐文件失败")
            return False
        logging.info("下载音乐文件成功")
        
        # 保存歌词文件（如果有）
        lrc_path = None
        lrc_text = music_info.get("lrcText", "")
        if lrc_text:
            lrc_path = os.path.join(tmp_dir, "music.lrc")
            with open(lrc_path, "w", encoding="utf-8") as f:
                f.write(lrc_text)
            logging.info("保存歌词文件成功")

        # 保存音乐元信息
        del music_info["url"] # 删除url字段
        del music_info["lrcText"] # 删除lrcText字段
        del music_info["lrcUrl"] # 删除lrcUrl字段
        json_path = os.path.join(tmp_dir, "music.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(music_info, f, ensure_ascii=False, indent=2)
        logging.info("保存音乐元信息成功")
        
        # 初始化AList客户端
        client = OpenListClient(get_openlist_base_url())
        
        # 获取或登录token
        token = load_token()
        if token is None:
            logging.info("Token不存在或已过期，重新登录")
            login_resp = client.auth.login_hash(
                "upload", 
                "03473b106db25a53dcf79fd7234b7d5617abab1dbd716f7499fb90b485001035"
            )
            if login_resp.code != 200:
                logging.error("登录失败")
                return False
            token = login_resp.data.token
            # 保存新token
            with open("/tmp/alist.token", "w") as f:
                f.write(token)
            logging.info("登录成功并保存新token")
        
        client.set_token(token)
        
        # 上传文件
        base_path = f"/music/{artist}/{title}"
        
        # 上传元信息
        if not _upload_file(client, json_path, f"{base_path}.json"):
            return False
        
        # 上传音乐文件
        if not _upload_file(client, music_path, f"{base_path}.mp3"):
            return False
        
        # 上传歌词文件（如果有）
        if lrc_path and os.path.exists(lrc_path):
            if not _upload_file(client, lrc_path, f"{base_path}.lrc"):
                return False
        
        logging.info(f"音乐保存成功: {artist} - {title}")
        return True
        
    except Exception as e:
        logging.error(f"保存音乐失败: {e}", exc_info=True)
        return False
    finally:
        # 清理临时目录
        if tmp_dir and os.path.exists(tmp_dir):
            try:
                import shutil
                shutil.rmtree(tmp_dir)
                logging.info(f"清理临时目录: {tmp_dir}")
            except Exception as e:
                logging.warning(f"清理临时目录失败: {e}")

def load_music(title: str, artist: str) -> dict | None:
    logging.info(f"开始加载音乐: {title} - {artist}")
    url = f"{get_openlist_base_url()}/d/upload/music/{quote(artist)}/{quote(title)}.json"
    response = requests.get(url)
    if response.status_code != 200:
        logging.error(f"加载音乐失败: {response.status_code}")
        return
    music_info = response.json()
    if 'code' in music_info:
        logging.error(f"加载音乐失败: {music_info['code']}")
        return
    music_info["url"] = f"{get_openlist_base_url()}/d/upload/music/{quote(artist)}/{quote(title)}.mp3"
    music_info["lrcUrl"] = f"{get_openlist_base_url()}/d/upload/music/{quote(artist)}/{quote(string=title)}.lrc"
    logging.info(f"已加载音乐 '{title}' '{artist}'")
    return music_info

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    music_info = {
        "url": "https://vip.123pan.cn/1812665715/13416461",
        "title": "爱在西元前",
        "artist": "周杰伦",
        "artworkUrl": "http://img4.kuwo.cn/star/albumcover/500/39/0/1272200948.jpg",
        "lrcText": "爱在西元前 歌词",
        "lrcUrl": ""
    }
    res = save_music(music_info)
    print(res)
    music_info = load_music("爱在西元前", "周杰伦")
    print(music_info)
