import os
import json
import signal
import subprocess
import platform
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console, Group
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TaskProgressColumn,
)
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.rule import Rule

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm")

console = Console()

# ================= Ctrl+C 优雅中断 =================
stop_requested = False
def handle_sigint(sig, frame):
    global stop_requested
    stop_requested = True
    console.print(
        "\n[bold yellow]⚠ 已请求中断[/bold yellow] "
        "[yellow]正在安全停止当前视频，后续任务将不会启动…[/yellow]"
    )

signal.signal(signal.SIGINT, handle_sigint)


# ================= 播放提示音 =================
def play_notification():
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        else:
            print("\a")
    except Exception:
        pass


# ================= NVENC 检测 =================
def has_nvenc():
    try:
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
        )
        return "hevc_nvenc" in r.stdout
    except Exception:
        return False


# ================= 分辨率 =================
def get_resolution(path):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json", path
    ]
    info = json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)
    s = info["streams"][0]
    return s["width"], s["height"]


# ================= CRF 策略 =================
def auto_crf(w, h, nvenc):
    if w >= 3840 or h >= 2160:
        return 19 if nvenc else 24
    if w >= 1920 or h >= 1080:
        return 21 if nvenc else 26
    return 23 if nvenc else 28


# ================= 视频时长 =================
def get_duration(path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", path
    ]
    info = json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)
    return float(info["format"]["duration"])


# ================= 单文件处理 =================
def compress_one(
    path, out_dir, existing_outputs,
    nvenc, crf_override,
    progress, recent_logs
):
    global stop_requested
    if stop_requested:
        return None

    name = os.path.basename(path)
    base = os.path.splitext(name)[0]
    out_name = base + "_h265.mp4"
    out_path = os.path.join(out_dir, out_name)

    if out_name in existing_outputs:
        recent_logs.append(f"[grey58]⏭ 跳过已存在文件：{name}[/grey58]")
        return "skipped", 0, 0

    src_size = os.path.getsize(path)
    w, h = get_resolution(path)
    crf = crf_override if crf_override is not None else auto_crf(w, h, nvenc)
    duration = get_duration(path)

    task_id = progress.add_task(f"🎞 [cyan]正在压缩:[/cyan] {name}", total=100)

    if nvenc:
        vcodec = ["-c:v", "hevc_nvenc", "-cq", str(crf), "-preset", "p6"]
    else:
        vcodec = ["-c:v", "libx265", "-crf", str(crf), "-preset", "slow"]

    cmd = [
        "ffmpeg", "-y",
        "-i", path,
        *vcodec,
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-progress", "pipe:1",
        "-nostats",
        out_path
    ]

    try:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        for line in p.stdout:
            if stop_requested:
                p.terminate()
                return None
            if line.startswith("out_time_ms="):
                t = int(line.split("=")[1]) / 1_000_000
                progress.update(task_id, completed=min(t / duration * 100, 100))

        p.wait()
        recent_logs.append(f"[green]✅ 已完成：{name}[/green]")
        dst_size = os.path.getsize(out_path)
        return "done", src_size, dst_size
    except Exception as e:
        recent_logs.append(f"[red]❌ 失败：{name} ({str(e)})[/red]")
        return None
    finally:
        progress.remove_task(task_id)


# ================= 扫描视频 =================
def scan_videos(root):
    vids = []
    for base, dirs, files in os.walk(root):
        if "output_wm" in dirs:
            dirs.remove("output_wm")
        for f in files:
            if f.lower().endswith(VIDEO_EXTS):
                vids.append(os.path.join(base, f))
    return vids


# ================= 主循环 =================
def main():
    while True:
        global stop_requested
        stop_requested = False
        recent_logs = deque(maxlen=5)

        console.print(Panel(
            "[bold cyan]🎬 H.265 视频批量压缩工具（专业版）[/bold cyan]\n\n"
            "[bold yellow]📌 工具简介[/bold yellow]\n"
            "• 本工具基于 [bold]FFmpeg[/bold]，将视频统一压缩为 [bold green]H.265 / HEVC[/bold green]\n"
            "• 在 [bold]几乎无肉眼画质损失[/bold] 的前提下，大幅降低视频体积\n"
            "• 适合素材归档、NAS、剪辑前压缩、长期存储\n\n"
            "[bold yellow]⚙️ 核心功能[/bold yellow]\n"
            "• 📂 递归扫描指定目录下的所有视频文件\n"
            "• 📁 在源目录内自动创建 [bold]output_wm[/bold] 输出文件夹\n"
            "• ⏭ 自动识别已压缩文件并跳过，绝不重复处理\n"
            "• 🚀 自动检测 [bold green]NVIDIA NVENC[/bold green]，优先使用显卡加速\n"
            "• 🧠 根据分辨率自动选择最优 CRF（4K / 1080P / 其他）\n"
            "• ⚡ 支持 [bold]同步 / 异步（多线程）[/bold] 处理模式\n"
            "• 🛑 支持 [bold yellow]Ctrl + C[/bold yellow] 安全中断，不损坏文件\n\n"
            "[bold yellow]🎯 CRF 说明[/bold yellow]\n"
            "• CRF 数值越小，画质越高，文件越大\n"
            "• 推荐肉眼无明显差别区间：[bold green]18 ~ 28[/bold green]\n"
            "• 直接回车 = 使用工具内置智能策略\n\n"
            "[bold yellow]📦 输出规则[/bold yellow]\n"
            "• 原文件 [bold red]不会被修改[/bold red]\n"
            "• 新文件名追加：[_h265.mp4]\n"
            "• 示例：example.mp4 → example_h265.mp4\n",
            title="[bold cyan]VideoCompressor[/bold cyan]",
            title_align="center",
            border_style="cyan",
            expand=True,
            padding=(1, 2)
        ))

        input_dir = console.input(
            "[bold cyan]📂 请输入视频根目录[/bold cyan]: "
        ).strip()
        if not os.path.isdir(input_dir):
            console.print("[bold red]❌ 路径无效！[/bold red]")
            continue

        async_mode = console.input(
            "[bold magenta]⚡ 是否启用异步处理[/bold magenta] (y/N): "
        ).strip().lower() == "y"

        workers = 1
        if async_mode:
            workers = int(console.input("[bold magenta]🧵 线程数[/bold magenta] (默认 2): ") or 2)

        crf_input = console.input(
            "[bold cyan]🎯 自定义 CRF[/bold cyan] (回车=自动): "
        ).strip()
        crf_override = int(crf_input) if crf_input else None

        out_dir = os.path.join(input_dir, "output_wm")
        os.makedirs(out_dir, exist_ok=True)

        existing_outputs = {
            f for f in os.listdir(out_dir)
            if f.lower().endswith("_h265.mp4")
        }

        nvenc = has_nvenc()
        videos = scan_videos(input_dir)
        if not videos:
            console.print("[bold red]❌ 未找到视频文件[/bold red]")
            continue

        progress = Progress(
            TextColumn("{task.description}", justify="left"),
            BarColumn(bar_width=28),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        )

        total_task = progress.add_task(
            f"[bold cyan]📦 总进度 (0/{len(videos)})",
            total=len(videos)
        )

        def make_layout():
            return Group(progress, Rule(style="grey15"), "\n".join(recent_logs))

        total_src = total_dst = 0

        with Live(make_layout(), console=console, refresh_per_second=10):
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [
                    pool.submit(
                        compress_one, v, out_dir, existing_outputs,
                        nvenc, crf_override, progress, recent_logs
                    )
                    for v in videos
                ]

                for f in as_completed(futures):
                    if stop_requested:
                        break

                    r = f.result()

                    progress.advance(total_task)

                    done = int(progress.tasks[total_task].completed)
                    progress.update(
                        total_task,
                        description=f"[bold cyan]📦 总进度 ({done}/{len(videos)})"
                    )

                    if r and r[0] == "done":
                        total_src += r[1]
                        total_dst += r[2]

        if total_src > 0:
            table = Table(title="📊 压缩统计")
            table.add_column("原始体积")
            table.add_column("压缩后")
            table.add_column("节省率")
            table.add_row(
                f"{total_src / 1024**3:.2f} GB",
                f"{total_dst / 1024**3:.2f} GB",
                f"{100 * (1 - total_dst / total_src):.1f}%"
            )
            console.print(table)

        play_notification()

        choice = console.input(
            "\n[bold cyan]是否继续处理其他文件？[/bold cyan] [green](Y)[/green]/[red](N)[/red]: "
        ).strip().lower()

        if choice != "y":
            console.print("[bold green]👋 程序已退出，再见！[/bold green]")
            break


if __name__ == "__main__":
    main()
