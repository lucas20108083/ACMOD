
import os
import sys
import glob
import re
from pathlib import Path
from collections import defaultdict

def check_ini_file(file_path):
    errors = []
    current_section = None
    section_keys = defaultdict(set)
    line_numbers = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                lines = f.readlines()
        except:
            return [f"无法读取文件: {file_path} (编码问题)"]
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        # 跳过空行和注释
        if not line or line.startswith(';') or line.startswith('#'):
            continue
            
        # 检查是否是节头
        section_match = re.match(r'^\[([^\]]+)\]$', line)
        if section_match:
            current_section = section_match.group(1)
            continue
            
        # 检查键值对
        if ':' in line and current_section:
            key_value = line.split(':', 1)
            key = key_value[0].strip()
            
            if key in section_keys[current_section]:
                # 找到重复键
                if current_section not in errors:
                    errors.append(f"节 [{current_section}] 中的重复键:")
                
                first_line = line_numbers.get((current_section, key), '未知')
                errors.append(f"  键 '{key}' 重复 - 第一次出现在行 {first_line}, 当前行 {line_num}")
            else:
                section_keys[current_section].add(key)
                line_numbers[(current_section, key)] = line_num
    
    return errors

def check_directory(directory):
    extensions = ['*.ini', '*.ei', '*.template']
    all_errors = []
    
    for ext in extensions:
        pattern = os.path.join(directory, '**', ext)
        files = glob.glob(pattern, recursive=True)
        
        for file_path in files:
            print(f"检查文件: {os.path.relpath(file_path, directory)}")
            errors = check_ini_file(file_path)
            
            if errors:
                all_errors.append(f"\n文件: {os.path.relpath(file_path, directory)}")
                all_errors.extend(errors)
    
    return all_errors

def main():
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = "ACMod-Sunset_and_shimmer"
    
    if not os.path.exists(target_dir):
        print(f"错误: 目录 '{target_dir}' 不存在")
        sys.exit(1)
    
    print(f"开始检查目录: {target_dir}")
    print("=" * 60)
    
    errors = check_directory(target_dir)
    
    if errors:
        print("\n" + "=" * 60)
        print("发现以下问题:")
        print("=" * 60)
        for error in errors:
            print(error)
        print("=" * 60)
        print(f"总共发现 {len([e for e in errors if e.startswith('  键')])} 个重复键")
    else:
        print("\n" + "=" * 60)
        print("✓ 检查完成，未发现重复键")
        print("=" * 60)

if __name__ == "__main__":
    main()