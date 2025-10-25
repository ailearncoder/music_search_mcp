from typing import Any, Annotated
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from .api_music_gequbao import (
    api_music_gequbao_search
)
from .alist_storage import save_music

# Create a basic server instance
mcp = FastMCP(name="music_search")

# You can also add instructions for how to interact with the server
mcp_with_instructions = FastMCP(
    name="music_search",
    instructions="""
        search music online, you can search by artist or song name
    """,
)

@mcp.tool
def search_music(keyword: Annotated[str, "search keyword"]) -> dict:
    '''search music online, you can search by artist or song name'''
    result = api_music_gequbao_search(keyword)
    if result is None:
        raise ToolError("search failed, current search engine may have problems")
    try:
        search_result = []
        music_info = {}
        if isinstance(result, tuple):
            if len(result) != 2:
                raise ToolError(f"search failed, length of result is not 2, result: {result}")
            if 'data' not in result[1]:
                raise ToolError(f"search failed, 'data' not in result[1], result: {result}")
            if 'url' not in result[1]['data']:
                raise ToolError(f"search failed, 'url' not in result[1]['data'], result: {result}")
            url = result[1]['data']['url']
            title = result[0].get('mp3_title', '未知歌曲')
            artist = result[0].get('mp3_author', '未知歌手')
            artwork_url = result[0].get('mp3_cover', '')
            lrc = result[0].get('lrc', '')
            lrc_url = result[0].get('lrc_url', '')
            music_info = {
                "url": url,
                "title": title,
                "artist": artist,
                "artworkUrl": artwork_url,
                "lrcText": lrc,
                "lrcUrl": lrc_url
            }
            save_music(music_info)
        if isinstance(result, dict):
            music_info = result
        search_result.append(music_info)
        return {
            "success": True,
            "result": search_result,
            "nextTools": ["self.music.play"]
        }
    except Exception as e:
        raise ToolError(f"search failed, {e}")
