#!/usr/bin/env python3
"""
gen_srt.py — SRT 字幕生成器（自然短语 + FunASR 时间锚点）

原理:
  1. 用 FunASR 逐段识别音频 → 得到每段文字和它在音频中的真实起止时间
  2. 将识别结果拼接成"完整识别文本"，同时记录每个字的时间
  3. 把已知原文按标点拆成自然短句（每条≤15字，不断句）
  4. 用"字级时间表"给每句自然短句分配精确时间
  5. 识别有错的字用原文替换

用法:
  python gen_srt.py --input-dir ./segments/ --output subtitles.srt
"""
import re, os, sys, argparse, subprocess, tempfile, shutil

MAX_CHARS = 15

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", required=True)
    p.add_argument("--output", default="subtitles.srt")
    p.add_argument("--audio", default="narration_master.mp3")
    return p.parse_args()

def load_text(input_dir):
    files = sorted([f for f in os.listdir(input_dir) if re.match(r'seg_\d+\.txt$', f)],
                   key=lambda x: int(re.search(r'\d+', x).group()))
    return ''.join(open(os.path.join(input_dir, f), 'r', encoding='utf-8').read().strip() for f in files)

def time_to_srt(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    ms = int((s - int(s)) * 1000)
    return f"{h:02d}:{m:02d}:{int(s):02d},{ms:03d}"

def get_chunks(audio_path):
    """检测停顿，返回切分段"""
    cmd = ['ffmpeg', '-i', audio_path, '-af', 'silencedetect=n=-30dB:d=0.2', '-f', 'null', '-']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    silences = []
    for line in result.stderr.split('\n'):
        m = re.search(r'silence_end:\s*([\d.]+)', line)
        if m: silences.append(float(m.group(1)))
    
    info = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', audio_path], capture_output=True, text=True)
    total = float(info.stdout.strip())
    
    points = [0.0]
    for s in silences:
        if s - points[-1] > 2.0 and s < total - 0.5:
            points.append(s)
    points[-1] = total
    return [(points[i], points[i+1]) for i in range(len(points) - 1)]

def clean(text):
    return re.sub(r'<\|[^|]+\|>', '', text).strip()

def split_into_phrases(text, max_chars=MAX_CHARS):
    """按标点拆成自然短句，不断句"""
    sentences = re.split(r'(?<=[。？！])', text)
    phrases = []
    for s in sentences:
        s = s.strip()
        if not s: continue
        if len(s) <= max_chars:
            phrases.append(s)
        else:
            parts = re.split(r'(?<=[，、；：])', s)
            for p in parts:
                p = p.strip()
                if not p: continue
                if len(p) <= max_chars:
                    phrases.append(p)
                else:
                    mid = len(p) // 2
                    for sep in '，、':
                        idx = p.find(sep)
                        if 2 < idx < len(p) - 2: mid = idx + 1; break
                    p1, p2 = p[:mid].strip(), p[mid:].strip()
                    if p1 and len(p1) > 2: phrases.append(p1)
                    if p2 and len(p2) > 2: phrases.append(p2)
    return [p for p in phrases if p]

def generate(args):
    if not os.path.exists(args.audio):
        print(f"❌ 找不到音频: {args.audio}")
        return
    
    original = load_text(args.input_dir)
    orig_clean = re.sub(r'[\s，。？！、；：""''——\-\(\)（）\n]', '', original)
    print(f"📖 原文 {len(orig_clean)} 字")
    
    # 1. 拆成自然短句
    phrases = split_into_phrases(original)
    print(f"📝 拆成 {len(phrases)} 条自然短句")
    
    # 2. FunASR 逐段识别
    chunks = get_chunks(args.audio)
    print(f"🎬 音频切成 {len(chunks)} 段，开始识别...")
    
    from funasr import AutoModel
    model = AutoModel(model='iic/SenseVoiceSmall', disable_update=True)
    
    tmp = tempfile.mkdtemp()
    
    try:
        # 收集每段的识别结果和对应原文字数
        rec_results = []  # [(start, end, rec_text, orig_char_count)]
        char_pos = 0
        
        for ci, (start, end) in enumerate(chunks):
            wav = os.path.join(tmp, f'{ci:04d}.wav')
            subprocess.run(['ffmpeg', '-y', '-i', args.audio, '-ss', str(start),
                '-to', str(end), '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', wav],
                capture_output=True)
            
            r = model.generate(input=wav, language='zh', ban_emoji=True)
            if isinstance(r, list) and r:
                rtext = clean(r[0].get('text', ''))
            elif isinstance(r, dict):
                rtext = clean(r.get('text', ''))
            else:
                rtext = ''
            
            if rtext:
                # 计算这段音频对应多少原文字（取原文对应片段）
                rec_clean = re.sub(r'[\s，。？！、；：""''——\-\(\)（）]', '', rtext)
                # 从原文当前位置取相同长度的文本
                orig_seg = orig_clean[char_pos:char_pos + len(rec_clean)]
                if len(orig_seg) < len(rec_clean):
                    rec_clean = rec_clean[:len(orig_seg)]
                
                actual_chars = min(len(rec_clean), len(orig_seg))
                if actual_chars > 0:
                    rec_results.append((start, end, rtext, actual_chars))
                    char_pos += actual_chars
            
            if (ci + 1) % 20 == 0:
                print(f"   进度: {ci+1}/{len(chunks)}")
        
        print(f"   ✅ 识别完成，{len(rec_results)} 段")
        
        # 3. 构建字级时间表
        # 每段音频的时间均匀分配给该段的原文文字
        char_times = []  # [(orig_char_index, start_time, end_time)]
        text_cursor = 0  # 在 orig_clean 中的位置
        
        for start, end, rec_text, num_chars in rec_results:
            dur_per_char = (end - start) / num_chars if num_chars > 0 else 0
            for i in range(num_chars):
                if text_cursor + i < len(orig_clean):
                    t_start = start + i * dur_per_char
                    t_end = start + (i + 1) * dur_per_char
                    char_times.append((text_cursor + i, t_start, t_end))
            text_cursor += num_chars
        
        print(f"   📊 构建了 {len(char_times)} 个字的时间映射")
        
        # 4. 把自然短句映射到字的时间上
        entries = []
        phrase_cursor = 0  # 在 orig_clean 中的位置
        
        for phrase in phrases:
            phrase_clean = re.sub(r'[\s，。？！、；：""''——\-\(\)（）]', '', phrase)
            if not phrase_clean:
                continue
            
            ph_len = len(phrase_clean)
            end_pos = phrase_cursor + ph_len - 1
            
            # 从char_times中找到这个短语的起止时间
            start_time = None
            end_time = None
            
            for pos, ts, te in char_times:
                if pos == phrase_cursor:
                    start_time = ts
                if pos == end_pos:
                    end_time = te
                if start_time is not None and end_time is not None:
                    break
            
            # 如果没找到精确匹配，用上一个/下一个时间点
            if start_time is None:
                for pos, ts, te in char_times:
                    if pos >= phrase_cursor:
                        start_time = ts
                        break
            if end_time is None:
                for pos, ts, te in reversed(char_times):
                    if pos <= end_pos:
                        end_time = te
                        break
            
            # 仍然没找到就跳过
            if start_time is None or end_time is None:
                phrase_cursor += ph_len
                continue
            
            if end_time - start_time >= 0.5:
                entries.append((phrase, start_time, end_time))
            
            phrase_cursor += ph_len
        
        # 5. 写SRT
        with open(args.output, 'w', encoding='utf-8') as f:
            for idx, (text, start, end) in enumerate(entries, 1):
                ct = text.strip().rstrip('，。？！；：、')
                if ct and end - start >= 0.5:
                    f.write(f"{idx}\n")
                    f.write(f"{time_to_srt(start)} --> {time_to_srt(end)}\n")
                    f.write(f"{ct}\n\n")
        
        print(f"✅ 生成 {len(entries)} 条字幕 → {args.output}")
        
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == '__main__':
    args = parse_args()
    generate(args)
