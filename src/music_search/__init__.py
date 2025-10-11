from .api_music_gequbao import (
    api_music_gequbao_search
)

def main() -> None:
    result = api_music_gequbao_search("周杰伦")
    print("Hello from music-search!")
    print(result)
