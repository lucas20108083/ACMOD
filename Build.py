import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil
import zipfile
import psutil
import time

class PackageTool:
    def __init__(self, root):
        self.root = root
        self.root.title("铁锈战争Mod打包工具")
        
        # 版本控制
        self.version_frame = ttk.LabelFrame(root, text="版本控制", padding=10)
        self.version_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(self.version_frame, text="版本号:").grid(row=0, column=0, padx=5)
        self.version_var = tk.StringVar()
        self.version_entry = ttk.Entry(self.version_frame, textvariable=self.version_var)
        self.version_entry.grid(row=0, column=1, padx=5)
        
        # 构建类型
        self.build_var = tk.StringVar(value="release")
        ttk.Radiobutton(self.version_frame, text="发行版", variable=self.build_var, 
                       value="release").grid(row=1, column=0)
        ttk.Radiobutton(self.version_frame, text="测试版", variable=self.build_var, 
                       value="debug").grid(row=1, column=1)
        
        # 快速移动选项
        self.move_var = tk.BooleanVar()
        ttk.Checkbutton(root, text="快速移动到铁锈战争Mod文件夹", 
                       variable=self.move_var).grid(row=1, column=0, pady=5)
        
        # 构建按钮
        ttk.Button(root, text="开始构建", command=self.build_mod).grid(row=2, column=0, pady=10)
        
        self.root.resizable(False, False)
        
    def save_version(self, version):
        with open("ver.txt", "w") as f:
            f.write(version)
            
    def kill_rw_process(self):
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'RustedWarfare.exe':
                proc.kill()
                time.sleep(1)
                break
                
    def build_mod(self):
        version = self.version_var.get().strip()
        if not version:
            messagebox.showerror("错误", "请输入版本号")
            return
            
        # 保存版本号
        self.save_version(version)
        
        # 检查源文件夹是否存在
        base_name = "ACMod-Sunset_and_shimmer"
        if not os.path.exists(base_name):
            messagebox.showerror("错误", f"源文件夹 {base_name} 不存在")
            return

        # 创建构建目录
        if not os.path.exists("Build"):
            os.makedirs("Build")
            
        # 准备文件名
        if self.build_var.get() == "debug":
            file_name = f"{base_name}_{version}_Debug"
        else:
            file_name = f"{base_name}_{version}"
            
        # 创建zip文件
        zip_path = os.path.join("Build", f"{file_name}.zip")
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                source_dir = os.path.abspath(base_name)
                for root, _, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 计算相对路径，确保压缩包内的目录结构正确
                        arcname = os.path.join(
                            os.path.relpath(root, source_dir),
                            file
                        ).replace(os.path.sep, '/')
                        if arcname.startswith('./'):
                            arcname = arcname[2:]
                        zipf.write(file_path, arcname)
                    
            # 重命名为.rwmod
            rwmod_path = os.path.join("Build", f"{file_name}.rwmod")
            if os.path.exists(rwmod_path):
                os.remove(rwmod_path)
            os.rename(zip_path, rwmod_path)
            
            # 如果选择快速移动
            if self.move_var.get():
                rw_mods_path = r"D:\Program Files (x86)\Steam\steamapps\common\Rusted Warfare\mods\units"
                if not os.path.exists(rw_mods_path):
                    messagebox.showerror("错误", "铁锈战争Mod文件夹不存在")
                    return
                    
                target_path = os.path.join(rw_mods_path, f"{file_name}.rwmod")
                
                if os.path.exists(target_path):
                    self.kill_rw_process()
                    os.remove(target_path)
                    
                shutil.copy2(rwmod_path, rw_mods_path)
                messagebox.showinfo("成功", "Mod已构建并移动到铁锈战争Mod文件夹")
            else:
                messagebox.showinfo("成功", "Mod构建完成")
                
        except Exception as e:
            messagebox.showerror("错误", f"打包过程中出现错误：{str(e)}")
            if os.path.exists(zip_path):
                os.remove(zip_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = PackageTool(root)
    root.mainloop()