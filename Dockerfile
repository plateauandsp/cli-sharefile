# 使用基于 Debian 的精简镜像
FROM python:3.11-slim

# 1. 替换 Debian APT 源为清华大学镜像源 (针对 Debian 12 Bookworm 优化)
# 兼容旧版的 sources.list 和新版的 debian.sources 格式
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || \
    sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || \
    sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 2. 安装 tzdata 并设置时区 (Debian 使用 apt-get)
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置环境变量，确保 Python 环境感知时区
ENV TZ=Asia/Shanghai

WORKDIR /app

# 3. 安装 Python 依赖，使用清华 Pip 源加速
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 4. 拷贝业务代码
COPY main.py .

# 设置挂载点
ENV SHARE_DIR=/data
VOLUME ["/data"]

EXPOSE 8000

# 5. 启动服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
