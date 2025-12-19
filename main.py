import os
import time
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, Response
from tabulate import tabulate

app = FastAPI()

# 从环境变量获取共享目录，默认挂载点为 /data
SHARE_DIR = os.getenv("SHARE_DIR", "/data")

def format_size(size):
    """将字节大小转换为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def get_directory_listing(path, url_path):
    """生成结构化的 ASCII 表格视图"""
    items = []
    # 规范化显示路径
    display_path = url_path if url_path.endswith('/') else url_path + '/'
    
    try:
        with os.scandir(path) as it:
            for entry in it:
                # 1. 过滤逻辑：隐藏文件（以.开头）不展示
                if entry.name.startswith('.'):
                    continue
                
                try:
                    stats = entry.stat()
                    mtime = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    is_dir = entry.is_dir()
                    
                    items.append({
                        "Type": "DIR" if is_dir else "FILE",
                        "Name": entry.name + ("/" if is_dir else ""),
                        "Size": "-" if is_dir else format_size(stats.st_size),
                        "mtime_raw": stats.st_mtime,
                        "Last Modified": mtime
                    })
                except OSError:
                    # 跳过由于权限或其他原因无法 stat 的文件
                    continue
    except PermissionError:
        return f"Error: Permission denied accessing '{display_path}'\n"
    except Exception as e:
        return f"Error: {str(e)}\n"

    # 2. 排序逻辑：按修改时间降序（最新的在前）
    items.sort(key=lambda x: x['mtime_raw'], reverse=True)

    # 3. 表格渲染：使用 tabulate 格式化
    table_data = [[i['Type'], i['Name'], i['Size'], i['Last Modified']] for i in items]
    headers = ["Type", "Name", "Size", "Last Modified"]
    
    # 渲染 ASCII 表格
    table = tabulate(table_data, headers=headers, tablefmt="simple")
    
    # 组装输出文本
    header_text = f"Index of {display_path}\n" + "="*len(f"Index of {display_path}") + "\n\n"
    footer_text = f"\n---\nTotal: {len(items)} items | Server Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return header_text + table + footer_text

@app.get("/{full_path:path}")
async def handle_request(full_path: str, request: Request):
    # 安全性：防止路径穿越攻击 (../)
    raw_path = os.path.join(SHARE_DIR, full_path)
    safe_path = os.path.abspath(raw_path)
    if not safe_path.startswith(os.path.abspath(SHARE_DIR)):
        raise HTTPException(status_code=403, detail="Forbidden: Path out of bounds")

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File or Directory Not Found")

    # 场景 A：请求的是目录 -> 返回表格
    if os.path.isdir(safe_path):
        content = get_directory_listing(safe_path, "/" + full_path)
        return Response(content=content, media_type="text/plain; charset=utf-8")

    # 场景 B：请求的是文件 -> 处理下载及断点续传
    file_size = os.path.getsize(safe_path)
    range_header = request.headers.get("range")

    # 4. 断点续传逻辑 (HTTP 206 Partial Content)
    if range_header:
        try:
            # 解析格式: bytes=start-end
            range_val = range_header.replace("bytes=", "").split("-")
            start = int(range_val[0])
            end = int(range_val[1]) if range_val[1] else file_size - 1
        except (ValueError, IndexError):
            raise HTTPException(status_code=416, detail="Invalid Range Header")

        if start >= file_size or end >= file_size:
            raise HTTPException(status_code=416, detail="Range Not Satisfiable")

        def file_iterator(file_path, offset, length):
            with open(file_path, "rb") as f:
                f.seek(offset)
                chunk_size = 1024 * 1024 # 每次读取 1MB
                remaining = length
                while remaining > 0:
                    read_size = min(chunk_size, remaining)
                    data = f.read(read_size)
                    if not data:
                        break
                    yield data
                    remaining -= len(data)

        content_length = end - start + 1
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Disposition": f'attachment; filename="{os.path.basename(safe_path)}"'
        }
        return StreamingResponse(file_iterator(safe_path, start, content_length), status_code=206, headers=headers)

    # 普通下载逻辑 (HTTP 200 OK)
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Disposition": f'attachment; filename="{os.path.basename(safe_path)}"'
    }
    return StreamingResponse(open(safe_path, "rb"), headers=headers)
