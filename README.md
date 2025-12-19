# CLI-ShareFile

**CLI-ShareFile** 是一款专为 终端设计的轻量级、零配置、高性能文件共享服务。它将物理目录结构透明地映射为 HTTP 路径，旨在让开发者仅通过 `curl` 即可查看目录，通过 `wget` 即可完成断点续传下载。

------

## ✨ 核心特性

- **终端优先 (CLI-First)**：自动检测并为 `curl` 返回美观的 `tabulate` ASCII 表格。
- **实时映射**：无需重启或建立索引，物理目录变动实时同步。
- **智能排序**：默认按文件修改时间 (**mtime**) 降序排列，第一时间看到最新文件。
- **断点续传**：支持 HTTP `Range` 请求，完美适配 `wget -c` 协议。
- **极简部署**：基于 Docker 容器化，深度优化中国区网络构建速度。
- **安全健壮**：内置路径穿越攻击防御，自动过滤隐藏文件，支持只读挂载。

------

## 🚀 快速开始

### 1. 准备环境

确保您的服务器已安装 **Docker**。

### 2. 构建镜像 (针对中国源优化)

在包含 `Dockerfile` 的目录下执行：

Bash

```
docker build -t cli-sharefile .
```

### 3. 运行服务

将您想要共享的目录（例如 `/home/user/data`）挂载到容器的 `/data` 路径：

Bash

```
docker run -d \
  --name cli-sharefile \
  -p 8000:8000 \
  -v /home/user/data:/data:ro \
  -e TZ=Asia/Shanghai \
  --restart always \
  cli-sharefile
```

> **注**：建议添加 `:ro` 以后端只读模式运行，确保宿主机数据安全。

------

## 🛠 使用示例

### A. 查看目录列表

Bash

```
curl http://<server_ip>:8000/
```

### B. 查看子目录内容

Bash

```
curl http://<server_ip>:8000/AA/BB/
```

### C. 下载文件

Bash

```
wget http://<server_ip>:8000/AA/test_file.zip
```

### D. 断点续传 (大文件推荐)

如果下载中断，使用 `-c` 参数继续下载：

Bash

```
wget -c http://<server_ip>:8000/AA/large_image.iso
```

------

## 📊 终端输出预览

执行 `curl` 后，您将看到如下格式化表格：

Plaintext

```
Index of /AA/
============

Type    Name         Size        Last Modified
------  -----------  ----------  -------------------
FILE    patch.tar.gz 1.50 GB     2025-11-07 18:00:01
FILE    setup.sh     12.00 KB    2025-11-07 15:30:00
DIR     configs/     -           2025-11-06 12:00:00
FILE    README.txt   4.00 KB     2025-11-01 09:30:00

---
Total: 4 items | Server Time: 2025-11-07 18:05:22
```

------

## ⚙️ 技术栈

- **核心框架**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11-slim)
- **表格渲染**: [Tabulate](https://github.com/astanin/python-tabulate)
- **服务器**: Uvicorn (ASGI)
- **基础镜像**: Debian Bookworm (优化的中国镜像源)

------

## 📂 项目结构说明

- `main.py`: 核心逻辑。包含目录扫描算法、表格渲染引擎以及 HTTP Range 断点续传处理。
- `Dockerfile`: 容器构建配置。预置了时区处理、APT/Pip 中国镜像源加速。
- `requirements.txt`: 依赖定义。

------

## 🔒 安全性说明

1. **路径审计**：程序会自动检查所有请求路径，防止通过 `../` 访问共享目录以外的系统文件。
2. **隐藏文件防护**：默认隐藏以 `.` 开头的所有文件（如 `.git`, `.env`），防止敏感配置泄露。
3. **权限容错**：自动跳过权限不足的文件或目录，避免因单个文件权限问题导致整个列表服务崩溃。

------

## 📜 许可证

本项目采用 MIT 许可证。
