# 🎬 VideoCompressor - H.265 视频批量压缩工具

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)  
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

📌 项目主页：[https://github.com/XuanMouren2004/VideoCompressor](https://github.com/XuanMouren2004/VideoCompressor)

---

## 🚀 工具简介

**VideoCompressor** 是一款基于 **FFmpeg** 的 H.265 / HEVC 视频批量压缩工具，核心特点包括：

- 📂 递归扫描指定目录下的视频文件  
- 📁 自动创建输出文件夹 `output_wm`  
- ⏭ 自动跳过已压缩的视频，避免重复处理  
- 🚀 NVIDIA NVENC GPU 加速支持  
- 🧠 智能 CRF 策略适配不同分辨率  
- ⚡ 支持同步与异步（多线程）处理  
- 🛑 支持 **Ctrl + C 安全中断**

> ⚠ 提示：本项目 **不包含 FFmpeg**，你需要自行下载并配置 FFmpeg。FFmpeg 官方 GitHub 仓库在这里：  
> https://github.com/FFmpeg/FFmpeg :contentReference[oaicite:0]{index=0}

---

## 🏷️ 发行版下载（开箱即用）

如果你不想自己配置 Python 环境，可以直接下载已打包的 Windows 发行版：

👉 **下载地址（Releases）：**  
https://github.com/XuanMouren2004/VideoCompressor/releases

发行版通常包含：

- 🗂 VideoCompressor.exe（可直接运行）  
- 📌 app.ico 图标文件  
- ❗ 不包含 FFmpeg，需要自行下载放置

只需：  
1. 解压缩  
2. 将 `ffmpeg.exe` 和 `ffprobe.exe` 放到同一目录或系统 PATH  
3. 运行 `VideoCompressor.exe`

---

## 🛠 使用前准备

### 1️⃣ 安装 Python（如果用源码版）

请安装 Python 3.10 或更高版本：  
https://www.python.org/downloads

安装依赖：
```bash
pip install rich
````

### 2️⃣ 下载 FFmpeg

FFmpeg 是这个工具压缩视频所依赖的核心程序。
📍 官方 GitHub 项目地址（源代码 & 下载）：
[https://github.com/FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) ([GitHub][1])

下载后，将 `ffmpeg.exe` 和 `ffprobe.exe`：

* 放入系统环境变量 PATH 可访问的路径 **或**
* 放在 `main.py` / `VideoCompressor.exe` 同一目录

⚠ **必备依赖，否则无法压缩！**

---

## 📝 使用方法（源码版）

1. 克隆仓库：

```bash
git clone https://github.com/XuanMouren2004/VideoCompressor
cd VideoCompressor
```

2. 运行主程序：

```bash
python main.py
```

3. 按提示输入：

* 📂 视频根目录
* ⚡ 是否启用异步处理
* 🧵 线程数
* 🎯 自定义 CRF（可选）

输出结果保存在：`output_wm` 文件夹。

---

## 🖥 打包方法（生成独立可执行文件）

如果你想 **自行打包成 EXE 文件**，推荐使用 **PyInstaller**：

1. 安装 PyInstaller：

```bash
pip install pyinstaller
```

2. 运行打包：

```bash
pyinstaller --noconsole --onefile --icon=app.ico main.py
```

参数说明：

* `--noconsole`（可选）隐藏控制台窗口
* `--onefile` 生成单个可执行文件
* `--icon=app.ico` 使用图标资源

成功后，你会在 `dist` 文件夹中看到 `main.exe`，改名为你喜欢的名字即可。

> 🎯 提示：使用打包好的 exe 前，一样需要 FFmpeg 放在同目录或 PATH。

---

## 📊 CRF & 输出规则

| 项       | 说明                          |
| ------- | --------------------------- |
| CRF 值范围 | 18 ~ 28（数值越小 = 画质更高 / 文件更大） |
| 输出规则    | 原文件不被覆盖，生成 `_h265.mp4`      |

示例：

```
example.mp4 → example_h265.mp4
```

---

## 💡 示例输出

```
📂 请输入视频根目录: D:\Videos
⚡ 是否启用异步处理 (y/N, 默认 N): y
🧵 线程数 (默认 2): 4
🎯 自定义 CRF (回车=自动 18~28): 22
```

压缩完毕后显示统计表：

```
📊 压缩统计
原始体积   压缩后   节省率
10.52 GB   4.37 GB   58.5%
🔔 全部任务已完成！
```

---

## 📚 参考链接

* FFmpeg 官方 GitHub：[https://github.com/FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) ([GitHub][1])

---

## 📝 许可证

本项目采用 **MIT License**。欢迎自由使用与修改。

