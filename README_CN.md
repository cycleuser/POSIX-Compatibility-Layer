# POSIX 兼容层 (POSIX Compatibility Layer)

一个**实验性质的探索工具**，旨在尝试通过 POSIX 兼容层，在操作系统与本地大语言模型（LLM）之间建立初步的互动连接。

## 项目背景

随着本地大模型技术的快速发展，我们开始思考如何让 AI 更自然地理解和操作计算机系统。然而，不同操作系统（Windows、Linux、macOS）之间的指令差异为 AI 的统一理解带来了障碍。

本项目并非为了替代现有的成熟 Shell 或提供生产级的跨平台解决方案，而是一次**技术验证（Proof of Concept）**。我们尝试构建一个轻量级的 Python 中间层，将 POSIX 标准命令作为 AI 与操作系统交互的“通用语言”。通过这个中间层，我们希望探索让本地模型（如 Ollama）通过标准化的指令集来辅助用户完成简单的文件操作和系统查询的可能性。

## 实验场景

作为一个探索性原型，本项目的适用场景主要集中在研究和个人尝试：

*   **AI 辅助交互探索**：测试本地大模型是否能通过 POSIX 指令集更准确地理解用户意图，并转换为实际的系统操作（例如，“帮我整理桌面”转换为一系列 `mv` 命令）。
*   **指令集标准化研究**：验证在异构系统上，使用统一的 POSIX 接口是否有助于降低 AI 学习系统操作的复杂度。
*   **简单的跨环境脚本测试**：为个人开发者提供一个简易环境，用于验证一些基础文件操作脚本在不同系统上的行为差异，但不建议用于复杂的生产环境。
*   **教学与演示**：作为教学案例，展示如何用 Python 封装系统调用，以及如何设计一个基础的“人-AI-系统”交互界面。

## 兼容性说明（实验中）

本项目基于 Python 标准库构建，理论上具备一定的跨平台能力，但仍处于**早期开发阶段**：

*   **硬件支持**：在标准的 x86/x64 PC 以及部分 ARM 设备（如 Mac M系列）上进行过基础运行测试。由于资源占用较少，它也可以在一些性能有限的设备上启动，用于简单的功能验证。
*   **操作系统**：目前主要在 Windows 10/11 环境下进行调试，同时也尝试在 macOS 和 Linux 上运行。我们通过 Python 库对部分系统差异进行了屏蔽，但可能会遇到未知的兼容性问题。
*   **本地模型支持**：集成了对 Ollama 本地接口的初步调用支持，允许用户在 GUI 中选择本地模型进行简单的对话和命令生成测试。

## 依赖环境

为了保持工具的轻量化，我们尽量减少了外部依赖：

*   **基础环境**：Python 3.7+。
*   **核心功能**：主要依赖 Python 原生库（`os`, `sys` 等）。
*   **图形界面**：使用了 Python 内置的 **Tkinter**，界面较为朴素，主要用于功能演示。
*   **系统信息（可选）**：推荐安装 `psutil` 以获取更准确的系统状态信息，若未安装，程序会尝试使用简易的系统命令进行回退，数据精度可能有限。
*   **AI 功能**：需要本地运行 **Ollama** 服务以支持模型交互功能。

## 安装与试用

本项目仅供学习和研究使用，建议通过以下方式试用：

**方式 1：PyPI 安装**
如果您想快速体验，可以尝试从 PyPI 下载：
```bash
pip install posix-compat

# 启动命令行模式
posix-cli

# 启动图形界面
posix-gui
```

**方式 2：源码运行（推荐）**
为了方便调试和修改代码，建议直接下载源码：
```bash
git clone https://github.com/cycleuser/POSIX-Compatibility-Layer
cd POSIX-Compatibility-Layer
# 直接运行启动脚本
python start_gui.py
```
这种方式无需安装到系统库，方便您随时调整代码进行实验。

## 运行截图

以下截图展示了该工具目前的雏形，界面和功能都比较基础。

### 帮助命令
列出了目前支持的少量基础命令。
![Help Command](https://raw.githubusercontent.com/cycleuser/POSIX-Compatibility-Layer/refs/heads/main/images/0-help.png)

### 目录列表 (ls)
尝试模拟了 ls 命令的输出格式。
![List Directory](https://raw.githubusercontent.com/cycleuser/POSIX-Compatibility-Layer/refs/heads/main/images/1-ls.png)

### 路径显示 (pwd)
显示当前的工作目录。
![PWD](https://raw.githubusercontent.com/cycleuser/POSIX-Compatibility-Layer/refs/heads/main/images/2-pwd.png)

### 目录切换 (cd)
基础的目录跳转功能。
![Change Directory](https://raw.githubusercontent.com/cycleuser/POSIX-Compatibility-Layer/refs/heads/main/images/3-cd.png)

### 系统概览 (lscpu)
获取 CPU 的基本信息。
![LSCPU](https://raw.githubusercontent.com/cycleuser/POSIX-Compatibility-Layer/refs/heads/main/images/4-lscpu.png)

### 硬件列表 (lspci)
在 Windows 上尝试通过命令模拟 lspci 的输出。
![LSPCI](https://raw.githubusercontent.com/cycleuser/POSIX-Compatibility-Layer/refs/heads/main/images/5-lspci.png)

## 授权协议

本项目采用 **GPLv3** 协议开源。

作为一个实验性项目，我们希望通过开源促进交流。如果您对“操作系统与 AI 交互”这个方向感兴趣，欢迎研究代码、提出建议或进行修改。请注意，本软件不提供任何形式的担保，使用时请注意数据安全。详细协议内容请参阅 `LICENSE` 文件。
