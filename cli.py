#!/usr/bin/env python
import argparse
import os
import sys
from parser import convert_to_epub, parse_epub
from tts_fish import synthesize_text
from debug_log import log_message, log_error, log_file_status

def main():
    parser = argparse.ArgumentParser(description='VoiceLibra - 电子书转有声书工具')
    parser.add_argument('ebook', help='电子书文件路径')
    parser.add_argument('--voice', '-v', help='声音克隆参考音频文件路径')
    parser.add_argument('--start', '-s', type=int, default=1, help='起始章节 (默认: 1)')
    parser.add_argument('--end', '-e', type=int, help='结束章节 (默认: 最后一章)')
    parser.add_argument('--output', '-o', default='output', help='输出目录 (默认: output)')
    parser.add_argument('--format', '-f', default='mav', 
                       choices=['mp3', 'wav', 'pcm'],
                       help='输出格式 (默认: mav)')
    
    args = parser.parse_args()
    
    # 验证输入
    if not os.path.exists(args.ebook):
        print(f"错误: 找不到电子书文件: {args.ebook}")
        return 1
        
    if args.voice and not os.path.exists(args.voice):
        print(f"错误: 找不到参考音频文件: {args.voice}")
        return 1
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    
    try:
        # 转换为EPUB格式
        print(f"正在将 {args.ebook} 转换为EPUB格式...")
        epub_path = convert_to_epub(args.ebook)
        
        # 解析电子书内容
        print("正在解析电子书内容...")
        book_title, chapters = parse_epub(epub_path)
        
        # 确定章节范围
        total_chapters = len(chapters)
        start_chapter = max(1, args.start)
        end_chapter = args.end if args.end else total_chapters
        
        if start_chapter > total_chapters or end_chapter < 1 or start_chapter > end_chapter:
            print(f"错误: 无效的章节范围。本书共有 {total_chapters} 章。")
            return 1
        
        end_chapter = min(end_chapter, total_chapters)
        selected_chapters = chapters[start_chapter-1:end_chapter]
        
        print(f"\n开始处理《{book_title}》")
        print(f"章节范围: {start_chapter} - {end_chapter} (共 {total_chapters} 章)")
        print(f"声音克隆: {'启用 - ' + args.voice if args.voice else '未启用'}")
        print(f"输出格式: {args.format}")
        print(f"输出目录: {os.path.abspath(args.output)}\n")
        
        # 处理每一章
        for i, chapter in enumerate(selected_chapters, start=start_chapter):
            chapter_title = chapter['title'] or f"第{i}章"
            print(f"正在处理 {i}/{end_chapter}: {chapter_title}")
            
            # 生成安全的文件名
            safe_title = "".join([c if c.isalnum() else "_" for c in chapter_title])
            output_file = os.path.join(args.output, f"chapter_{i:03d}_{safe_title[:30]}.{args.format}")
            
            try:
                # 合成语音
                audio_data = synthesize_text(
                    text=chapter['text'],
                    reference_audio_path=args.voice,
                    output_format=args.format
                )
                
                # 保存音频
                with open(output_file, 'wb') as f:
                    f.write(audio_data)
                
                print(f"✓ 已保存: {os.path.basename(output_file)}")
                
            except Exception as e:
                log_error(f"处理章节 {i} 时出错: {str(e)}")
                print(f"错误: 处理章节失败 - {str(e)}")
                continue
        
        print(f"\n处理完成! 音频文件已保存到: {os.path.abspath(args.output)}")
        return 0
        
    except Exception as e:
        log_error(f"程序执行出错: {str(e)}")
        print(f"错误: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())