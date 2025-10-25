from importlib.resources import files
from .mcp_server import mcp
import logging
import os

def load_cert():
    data_path = files('music_search_mcp').joinpath('assets')
    """初始化证书文件，将自定义 PEM 证书添加到 certifi CA 包中"""
    try:
        # 获取 PEM 文件路径
        pem_file_path = data_path.joinpath('ZeroSSL_ECC_Domain_Secure_Site_CA.pem')
        
        # 验证 PEM 文件是否存在
        if not pem_file_path.is_file():
            logging.warning(f"PEM 证书文件不存在: {pem_file_path}")
            return
        
        # 获取 certifi CA 文件路径（使用更健壮的方式）
        try:
            import certifi
            ca_file_path = certifi.where()
        except ImportError:
            logging.error("certifi 模块未安装，无法获取 CA 证书路径")
            return
        
        # 验证 CA 文件是否存在
        if not os.path.isfile(ca_file_path):
            logging.error(f"CA 证书文件不存在: {ca_file_path}")
            return
        
        # 读取 PEM 文件内容
        try:
            pem_content = pem_file_path.read_text(encoding='utf-8')
            if not pem_content.strip():
                logging.warning("PEM 证书文件为空")
                return
        except Exception as e:
            logging.error(f"读取 PEM 文件失败 {pem_file_path}: {e}")
            return
        
        # 检查证书是否已存在于 CA 文件中
        try:
            with open(ca_file_path, 'r', encoding='utf-8') as f:
                ca_content = f.read()
                if pem_content.strip() in ca_content:
                    logging.info(f"PEM 证书已存在于 CA 文件中，跳过添加: {ca_file_path}")
                    return
        except Exception as e:
            logging.error(f"读取 CA 文件失败 {ca_file_path}: {e}")
            return
        
        # 追加 PEM 证书到 CA 文件
        try:
            with open(ca_file_path, 'a', encoding='utf-8') as f:
                # 确保前面有换行符分隔
                if not ca_content.endswith('\n'):
                    f.write('\n')
                f.write(pem_content)
                if not pem_content.endswith('\n'):
                    f.write('\n')
            logging.info(f"成功添加 PEM 证书到 CA 文件: {ca_file_path}")
        except PermissionError:
            logging.error(f"没有权限写入 CA 文件: {ca_file_path}。可能需要管理员权限")
        except Exception as e:
            logging.error(f"写入 CA 文件失败 {ca_file_path}: {e}")
    
    except Exception as e:
        logging.error(f"初始化证书文件时发生未知错误: {e}")

def main() -> None:
    load_cert()
    logging.basicConfig(level=logging.INFO, force=True)
    mcp.run()
