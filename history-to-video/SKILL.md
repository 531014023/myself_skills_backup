---
name: history-to-video
description: 将企业史鉴(corp-history-insight)生成的HTML历史洞察报告自动转化为"每天了解一家公司"短视频。当用户提到"做视频""转短视频""生成视频""HTML转视频""做成讲解视频"或类似意图时触发。依赖 HyperFrames（HTML→视频开源框架）、edge-tts（免费中文TTS）、ffmpeg。产出两个版本：无字幕版 + 逐句字幕版。
agent_created: true
---

# History To Video — HTML历史洞察报告转短视频

## 概述

将 corp-history-insight 生成的 HTML 报告转化为 1080p 短视频。全流程：

```
HTML报告 → ①阅读报告提取叙事脚本(n≥3段)
         → ②设计幻灯片HTML(GSAP动画)
         → ③分段生成配音(edge-tts) + 写入.duration文件
         → ④gen_srt.py一键生成字幕SRT
         → ⑤HyperFrames渲染无声视频
         → ⑥ffmpeg合并配音+字幕→双版本输出
```

产出两个版本：无字幕版（`_final.mp4`）+ 字幕版（`_subtitle.mp4`）。

---

## 前置条件

- Node.js >= 22
- ffmpeg（系统路径可用）
- edge-tts（`pip install edge-tts`）
- funasr（`pip install funasr torchaudio`，用于字幕生成的时间戳）
- HyperFrames 项目已初始化（`npx hyperframes init <project-name>`）

---

## 通用工作流

### 第一步：阅读HTML报告 → 提炼叙事脚本

**核心原则：内容决定结构，不预设框架。**

通读 HTML 报告，找出报告自身的叙事节奏。通常包含：
- 开篇（公司简介/文化精髓）→ 必然有
- 正文（起源→发展→转折→现状）→ 按报告实际段落数
- 结语（核心结论）→ 必然有

**步骤：**
1. 通读 HTML 报告全文，理解叙事结构
2. 识别出 3~8 个自然叙事段落（报告有几个章节就分几段）
3. 为每段写口播文案（连贯通顺，用过渡词串联）
4. 每段保存为单个 .txt 文件，按顺序命名

**文件命名规范：**
```
segments/
├── seg_01.txt    # 开篇（公司名+一句话精髓）
├── seg_02.txt    # 历史起源
├── seg_03.txt    # 发展/转折    ← 数量由报告决定
├── ...           
└── seg_N.txt     # 结语/核心结论
```

**文案写作规范：**
- ✅ 按时间线叙事，用"到了…""但…""然而…"等过渡词自然串联
- ✅ 每段在 10~35 秒口播量（太长的拆成两段）
- ✅ 只做历史介绍和关键事件洞察
- ✅ 不评分、不打分、不排雷，结尾一句整体评价即可
- ✅ 片尾用"关注我，每天了解一家公司。企业史鉴，深度洞察。"
- ❌ 不要出现"主人"等称呼
- ❌ 不要用"我们"等模糊主语

---

### 第二步：设计幻灯片 HTML

按叙事段落的数量（N 段）设计 N+1 张幻灯片（外加片头片尾）。

**通用 HTML 结构（以 N=5 段为例）：**

```html
<div id="root" data-composition-id="main" data-start="0" data-duration="TOTAL"
     data-width="1920" data-height="1080">
  <!-- S1 片头 -->
  <div class="clip" data-start="0" data-duration="X" data-track-index="0">...</div>
  <!-- S2~S(N) 正文章节 -->
  <div class="clip" data-start="X" data-duration="Y" data-track-index="0">...</div>
  ...
  <!-- S(N+1) 片尾 -->
  <div class="clip" data-start="XX" data-duration="Z" data-track-index="0">...</div>
</div>
```

**幻灯片数量 = 叙事段落数 + 2（片头+片尾）。**
- 最少 3 张（片头+1段正文+片尾）
- 最多不限，但每段不少于 8 秒口播量

**设计规范：** 深色背景（`#0f0c29`），白色/金色文字，GSAP 渐入动画。

---

### 第三步：分段生成配音 + 写入 .duration 文件

为每个 .txt 文件生成配音，测量精确时长：

```bash
# 生成配音（语速 +30% ≈ 抖音1.3倍速，可调整）
edge-tts --voice zh-CN-YunxiNeural --rate +30% \
  --text "$(cat segments/seg_01.txt)" \
  --write-media segments/seg_01.mp3

# 测量精确时长并写入.duration文件
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 segments/seg_01.mp3 \
  > segments/seg_01.duration
```

推荐音色：`zh-CN-YunxiNeural`（自然男声，温和清晰），语速 `+30%`（约抖音1.3倍速）

**重要：** 每段必须写 .duration 文件（gen_srt.py 依赖它确定字幕时间轴）。

合并所有段为单音频文件（用于最终合成）：
```bash
# 生成合并列表
(for f in segments/seg_*.mp3; do echo "file '${f}'"; done) > concat_list.txt
# 合并
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy narration_master.mp3
```

---

### 第四步：更新 HTML 翻页时间

**关键规则：翻页时间直接等于配音时长，不加提前量，不加缓冲，不区分段落。**

每张幻灯片的 `data-duration` = 该段配音时长（从 .duration 文件读出）**向上取整到整数秒**。

```html
<!-- ✅ seg_01.mp3 时长 25.66s → data-duration=26 -->
<div class="clip" data-start="0" data-duration="26">
<!-- ✅ seg_02.mp3 时长 27.46s → data-duration=28 -->
<div class="clip" data-start="26" data-duration="28">
<!-- ✅ seg_N.mp3 时长 35.14s → data-duration=36 -->
<div class="clip" data-start="186" data-duration="36">
```

**为什么不能提前翻页：**
- 每段提前 0.2~0.8 秒，N 段累积起来就是几秒的"亏空"——视频总长 < 配音总长，最后一段配音尾巴必然被切断
- 解决只有一个办法：**干脆不提前，全部取整。** 多出的零点几秒黑屏对观看体验毫无影响

**总视频时长：** root 的 `data-duration` = 各段 data-duration 之和（自然等于配音总长向上取整）。

---

### 第五步：一键生成字幕（基于 FunASR + 已知文案对齐）

```bash
# FunASR 逐段识别音频 → 获取每段的真实起止时间
# 将已知文案拆成自然短句 → 按"字→时间"映射表分配精确时间
# FunASR识别有错字的以已知文案为准（自动修正）
python references/gen_srt.py --input-dir ./segments/ --output subtitles.srt
```

**原理：**
1. ffmpeg 检测停顿 → 音频切成 2~6 秒短段
2. **FunASR**（SenseVoiceSmall）逐段识别 → 每段有真实起止时间 + 识别文案
3. 将已知文案（segments/seg_XX.txt）拆成按标点分界的**自然短句**（不断句、不超过15字）
4. 识别文案与已知原文逐字对齐 → 构建**字→时间**映射表
5. 每条自然短句按其在原文中的位置，从映射表获取精确起止时间
6. 识别错字自动替换为原文

**效果：**
- 每条字幕都是完整自然短语，不从中间切断
- 时间来自真实音频波形，精度毫秒级
- 文案100%准确（识别错字被原文覆盖）

然后转换为 ASS 格式（可精确定位）：

```bash
ffmpeg -i subtitles.srt subtitles.ass
```

编辑 ASS 文件第一行的 Style 行，设置底部居中、小字号：

```
Style: Default,Arial,10,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,8,1
```

- 字号 10（1080p 下约 37px）
- 白色字 + 黑色描边 + 半透明背景
- Alignment=2（底部居中）
- MarginV=8（距底边约 30px）

---

### 第六步：渲染 + 最终合成

```bash
# 校验并渲染
npm run check
npm run render     # 约 3~5 分钟/160s 1080p

# 有字幕版
ffmpeg -i renders/output.mp4 -i narration_master.mp3 \
  -vf "ass=subtitles.ass" \
  -c:v libx264 -crf 20 -preset fast -c:a aac \
  -map 0:v:0 -map 1:a:0 -shortest \
  "公司名_每天了解一家公司_subtitle.mp4"

# 无字幕版
ffmpeg -i renders/output.mp4 -i narration_master.mp3 \
  -c:v copy -c:a aac \
  -map 0:v:0 -map 1:a:0 -shortest \
  "公司名_每天了解一家公司_final.mp4"
```

**说明：** 用 `-shortest` 剪掉末尾多余的黑屏（向上取整导致视频比音频略长）。由于没有提前翻页，视频时长一定 ≥ 音频时长，不会出现切断配音尾巴的问题。

---

### 第七步：清理

删除临时文件（seg_*.mp3、concat_list.txt、中间版本MP4），保留最终两个 MP4、narration_master.mp3（供字幕生成复用）、subtitles.srt、subtitles.ass、index.html 以及 **segments/ 目录下的所有 .txt 和 .duration 文件**（下次重做时可用）。

---

## 踩坑经验（必须遵守）

### 音画同步
- ❌ **禁止**在 HyperFrames HTML 中嵌入 `<audio>` 元素 → 浏览器渲染帧率≠音频播放，必不同步
- ✅ 只渲染无声视频，用 ffmpeg 容器级混流（`-c:v copy` + `-c:a aac` + `-map` 分别指定）

### 翻页时间
- ✅ 每段配音必须用 ffprobe 精确测量，写入 .duration 文件
- ✅ 所有段落 data-duration = 配音时长向上取整到整数秒（不提前、不滞后、不加缓冲）
- ✅ root 的 data-duration = 各段 data-duration 之和（自然等于总时长）
- ❌ 不要按字数估算时长
- ❌ 不要提前翻页（累积误差会导致视频短于配音）

### 字幕
- ✅ 用 ASS 格式（非 SRT 直接烧录），像素级控制位置
- ✅ 字号 10（1080p 下约 37px）
- ✅ 每条字幕 ≤ 15 字，不换行、高度固定
- ✅ 最短停留 2.0 秒，防闪跳
- ✅ 底部居中，MarginV=8（距底部约 30px）

### 文案
- ✅ 内容决定分段数，不预设框架
- ✅ 按时间线叙事，用过渡词串联
- ✅ 只做历史介绍和关键事件洞察，不评分
- ❌ 不出现"主人"称呼，用"关注我"

## 参考文件

- `references/gen_srt.py` — SRT 字幕生成器（基于 FunASR）
  - 用法：`python references/gen_srt.py --input-dir ./segments/ --output subtitles.srt`
  - 输入：segments/*.txt + narration_master.mp3
  - 流程：检测停顿切分音频 → FunASR逐段识别 → 自然短句拆解 → 字级时间映射 → SRT输出
  - 每句≤15字，自动去重/合并短条目
