import logging
import sys

def setup_logging():
    """设置基础的日志配置"""
    # 创建logger
    logger = logging.getLogger('music_search')
    logger.setLevel(logging.INFO)
    
    # 避免重复添加handler
    if not logger.handlers:
        # 创建formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # 添加handler到logger
        logger.addHandler(console_handler)
    
    return logger

# 创建默认的logger实例
logger = setup_logging()