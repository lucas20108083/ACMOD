import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import tkinter.font as tkfont
import os
import shutil
import zipfile
import psutil
import time
import re
import threading
import platform
import subprocess
try:
    from win10toast import ToastNotifier
    _win_notifier = ToastNotifier()
except Exception:
    _win_notifier = None

class PackageToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("铁锈战争Mod打包工具")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # 设置样式
        self.setup_styles()
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        
        # 初始化变量
        self.base_name = "ACMod-Sunset_and_shimmer"
        # 使用脚本文件所在目录作为基准路径，避免从其他工作目录运行时报找不到源文件
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_path = os.path.join(self.script_dir, self.base_name)
        self.mod_info_path = os.path.join(self.base_path, "mod-info.txt")
        self.build_output_dir = os.path.join(self.script_dir, "Build")
        self.version_var = tk.StringVar()
        self.build_type_var = tk.StringVar(value="release")
        self.move_to_mods_var = tk.BooleanVar(value=True)
        self.rw_mods_path_var = tk.StringVar()
        self.progress_var = tk.StringVar(value="准备就绪")
        # 关闭并重启选项：勾选则在构建前关闭游戏并记录 exe 路径，构建完成后尝试重启
        self.close_and_restart_var = tk.BooleanVar(value=False)
        self.killed_rw_exe = None
        # 跳过Build目录选项
        self.skip_build_var = tk.BooleanVar(value=True)
        
        self.create_widgets()
        self.auto_detect_version()
        self.auto_detect_mods_path()
        
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        # 优先使用 JetBrains Mono 字体，如果未安装则使用默认字体
        try:
            available = tkfont.families()
            preferred_font = 'JetBrains Mono' if 'JetBrains Mono' in available else 'Arial'
        except Exception:
            preferred_font = 'Arial'

        style.configure("Title.TLabel", font=(preferred_font, 16, "bold"))
        style.configure("Subtitle.TLabel", font=(preferred_font, 12, "bold"))
        style.configure("Success.TLabel", foreground="green")
        style.configure("Error.TLabel", foreground="red")
        
    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = ttk.Label(self.main_frame, text="铁锈战争Mod打包工具", 
                               style="Title.TLabel")
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 版本信息框架
        version_frame = ttk.LabelFrame(self.main_frame, text="版本信息", padding="10")
        version_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        version_frame.columnconfigure(1, weight=1)
        
        ttk.Label(version_frame, text="版本号:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.version_entry = ttk.Entry(version_frame, textvariable=self.version_var, width=20)
        self.version_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.detect_version_btn = ttk.Button(version_frame, text="自动检测", 
                                           command=self.auto_detect_version)
        self.detect_version_btn.grid(row=0, column=2)
        
        # 构建选项框架
        build_frame = ttk.LabelFrame(self.main_frame, text="构建选项", padding="10")
        build_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(build_frame, text="构建类型:").grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        self.release_radio = ttk.Radiobutton(build_frame, text="发行版 (Release)", 
                                           variable=self.build_type_var, value="release")
        self.release_radio.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        self.debug_radio = ttk.Radiobutton(build_frame, text="测试版 (Debug)", 
                                         variable=self.build_type_var, value="debug")
        self.debug_radio.grid(row=0, column=2, sticky=tk.W)
        
        # 快速移动框架
        move_frame = ttk.LabelFrame(self.main_frame, text="快速部署", padding="10")
        move_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        move_frame.columnconfigure(1, weight=1)
        
        self.move_check = ttk.Checkbutton(move_frame, text="快速移动到铁锈战争Mod文件夹", 
                                        variable=self.move_to_mods_var,
                                        command=self.toggle_move_options)
        self.move_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(move_frame, text="Mod文件夹路径:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.path_entry = ttk.Entry(move_frame, textvariable=self.rw_mods_path_var, state="readonly")
        self.path_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.detect_path_btn = ttk.Button(move_frame, text="检测路径", 
                                        command=self.auto_detect_mods_path)
        self.detect_path_btn.grid(row=1, column=2)
        
        # 日志输出框架
        log_frame = ttk.LabelFrame(self.main_frame, text="构建日志", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(4, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # 如果 JetBrains Mono 可用则设置为日志字体，保证等宽显示
        try:
            available = tkfont.families()
            if 'JetBrains Mono' in available:
                self.log_text.configure(font=('JetBrains Mono', 10))
        except Exception:
            pass
        
        # 进度和按钮框架
        bottom_frame = ttk.Frame(self.main_frame)
        bottom_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        bottom_frame.columnconfigure(0, weight=1)
        
        self.progress_label = ttk.Label(bottom_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.build_btn = ttk.Button(bottom_frame, text="开始构建", 
                                  command=self.start_build_thread)
        self.build_btn.grid(row=0, column=1, padx=(10, 0))
        # 跳过Build目录选项
        self.skip_build_chk = ttk.Checkbutton(bottom_frame, text="跳过Build目录", 
                                             variable=self.skip_build_var)
        self.skip_build_chk.grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        # 在开始构建按钮下增加关闭进程的 CheckBox（用户勾选后在构建前关闭游戏并在构建后重启）
        self.close_chk = ttk.Checkbutton(bottom_frame, text="关闭进程",
                                         variable=self.close_and_restart_var)
        self.close_chk.grid(row=1, column=1, sticky=tk.W, pady=(6, 0))
        
    def toggle_move_options(self):
        """切换快速移动选项的状态"""
        if self.move_to_mods_var.get():
            self.path_entry.configure(state="normal")
            self.auto_detect_mods_path()
        else:
            self.path_entry.configure(state="readonly")
            
    def log_message(self, message):
        """在日志框中添加消息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def send_notification(self, title, message, duration=5):
        """尝试使用系统通知发送消息，缺失时回退到 messagebox"""
        try:
            if _win_notifier and platform.system() == 'Windows':
                # win10toast 在后台线程显示通知
                _win_notifier.show_toast(title, message, duration=duration, threaded=True)
                self.log_message(f"🔔 已发送系统通知: {title} - {message}")
                return
        except Exception as e:
            # 记录但回退到 messagebox
            self.log_message(f"⚠️ 系统通知发送失败: {e}")

        # 回退：使用普通弹窗
        try:
            messagebox.showinfo(title, message)
        except Exception:
            # 最后回退：记录日志
            self.log_message(f"ℹ️ {title}: {message}")
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        
    def auto_detect_version(self):
        """自动检测版本号"""
        version = self.get_version_from_mod_info()
        if version:
            self.version_var.set(version)
            self.log_message(f"✅ 自动检测到版本号: {version}")
        else:
            self.log_message("❌ 无法自动检测版本号，请手动输入")
            
    def get_version_from_mod_info(self):
        """从mod-info.txt文件中提取版本号"""
        if not os.path.exists(self.mod_info_path):
            return None
            
        try:
            with open(self.mod_info_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            version_pattern = r'Version\s*([\d.]+)'
            match = re.search(version_pattern, content)
            
            if match:
                return match.group(1)
            else:
                return None
                
        except Exception:
            return None
            
    def auto_detect_mods_path(self):
        """自动检测铁锈战争Mod路径"""
        default_paths = [
            r"D:\Program Files (x86)\Steam\steamapps\common\Rusted Warfare\mods\units",
            r"C:\Program Files (x86)\Steam\steamapps\common\Rusted Warfare\mods\units",
            r".\mods\units"
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                self.rw_mods_path_var.set(path)
                self.log_message(f"✅ 检测到Mod路径: {path}")
                return
                
        self.log_message("❌ 未检测到Mod路径，请手动选择")
        
    def kill_rw_process(self):
        """结束铁锈战争进程"""
        # 保留兼容方法：只结束进程并返回是否找到并结束过
        found = False
        target_names = ['Rusted Warfare - 64.exe', 'Rusted Warfare.exe', 'RustedWarfare.exe']
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info.get('name')
                if name in target_names:
                    self.log_message("🛑 检测到铁锈战争正在运行，正在结束进程...")
                    proc.kill()
                    time.sleep(1)
                    self.log_message("✅ 铁锈战争进程已结束")
                    found = True
            except Exception:
                continue
        return found

    def find_and_kill_rw_process(self):
        """查找并结束 Rusted Warfare 进程，返回可执行文件路径（若找到）"""
        target_names = ['Rusted Warfare - 64.exe', 'Rusted Warfare.exe', 'RustedWarfare.exe']
        exe_path = None
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                name = proc.info.get('name')
                if name in target_names:
                    # 尝试获取 exe 路径
                    try:
                        exe_path = proc.exe()
                    except Exception:
                        exe_path = proc.info.get('exe')
                    self.log_message("🛑 检测到铁锈战争正在运行，正在结束进程...")
                    try:
                        proc.kill()
                    except Exception as e:
                        self.log_message(f"⚠️ 无法结束进程: {e}")
                    time.sleep(1)
                    self.log_message("✅ 铁锈战争进程已结束")
                    # 如果有多个实例，仍记录第一个可用 exe 路径
                    if exe_path:
                        return exe_path
            except Exception:
                # 忽略无法访问的进程信息
                continue
        return exe_path
        
    def save_version(self, version):
        """保存版本号到ver.txt"""
        # 将 ver.txt 保存在脚本目录，保证从任意工作目录运行时位置一致
        try:
            ver_path = os.path.join(self.script_dir, "ver.txt")
            with open(ver_path, "w", encoding='utf-8') as f:
                f.write(version)
            self.log_message(f"📝 版本号 {version} 已保存到 {ver_path}")
        except Exception as e:
            self.log_message(f"⚠️ 无法保存 ver.txt: {e}")
        
    def retry_action(self, action, retries=5, delay=0.5, action_name="操作"):
        """重试操作，避免文件被占用导致偶发失败"""
        for attempt in range(retries):
            try:
                return action()
            except Exception as e:
                if attempt == retries - 1:
                    raise
                self.log_message(f"⚠️ {action_name} 失败，重试 {attempt+1}/{retries}：{e}")
                time.sleep(delay)

    def safe_remove(self, path):
        if not os.path.exists(path):
            return
        def action():
            os.remove(path)
        self.retry_action(action, action_name=f"删除文件 {path}")

    def safe_rename(self, src, dst):
        def action():
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(src, dst)
        self.retry_action(action, action_name=f"重命名 {src} -> {dst}")

    def start_build_thread(self):
        """在新线程中开始构建"""
        self.build_btn.configure(state="disabled")
        self.clear_log()
        thread = threading.Thread(target=self.build_mod)
        thread.daemon = True
        thread.start()
        
    def build_mod(self):
        """构建Mod包"""
        try:
            self.progress_var.set("正在构建...")
            
            # 获取输入值
            version = self.version_var.get().strip()
            if not version:
                messagebox.showerror("错误", "请输入版本号")
                self.progress_var.set("准备就绪")
                self.build_btn.configure(state="normal")
                return
                
            build_type = self.build_type_var.get()
            move_to_mods = self.move_to_mods_var.get()
            rw_mods_path = self.rw_mods_path_var.get()
            skip_build = self.skip_build_var.get()
            
            # 显示构建配置
            self.log_message("=" * 50)
            self.log_message("🏗️  开始构建Mod")
            self.log_message("=" * 50)
            self.log_message(f"📋 构建配置:")
            self.log_message(f"   版本号: {version}")
            self.log_message(f"   构建类型: {build_type}")
            self.log_message(f"   快速移动: {'是' if move_to_mods else '否'}")
            if move_to_mods:
                self.log_message(f"   目标路径: {rw_mods_path}")
            
            # 保存版本号
            self.save_version(version)

            # 如果用户勾选了关闭进程选项，先尝试关闭游戏并记录 exe 路径以便构建后重启
            if self.close_and_restart_var.get():
                try:
                    self.killed_rw_exe = self.find_and_kill_rw_process()
                    if self.killed_rw_exe:
                        self.log_message(f"ℹ️ 记录到被关闭的游戏可执行文件: {self.killed_rw_exe}")
                except Exception as e:
                    self.log_message(f"⚠️ 尝试关闭游戏时出错: {e}")
            
            # 检查源文件夹是否存在（使用脚本目录下的 base_path）
            if not os.path.exists(self.base_path):
                self.log_message(f"❌ 错误: 源文件夹 未找到: {self.base_path}")
                messagebox.showerror("错误", f"源文件夹 未找到: {self.base_path}")
                self.progress_var.set("准备就绪")
                self.build_btn.configure(state="normal")
                return

            # 创建构建目录
            if not os.path.exists(self.build_output_dir):
                os.makedirs(self.build_output_dir)
                self.log_message(f"📁 创建构建目录: {self.build_output_dir}")
                
            # 准备文件名
            if build_type == "debug":
                file_name = f"{self.base_name}_{version}_Debug"
            else:
                file_name = f"{self.base_name}_{version}"
                
            # 创建zip文件
            zip_path = os.path.join(self.build_output_dir, f"{file_name}.zip")
            zip_temp_path = zip_path + ".tmp"
            try:
                self.log_message(f"\n📦 正在打包 {self.base_name}...")
                file_count = 0
                if os.path.exists(zip_temp_path):
                    self.safe_remove(zip_temp_path)
                
                with zipfile.ZipFile(zip_temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # 使用基于脚本目录的源文件夹路径，避免相对路径问题
                    source_dir = os.path.abspath(self.base_path)
                    for root, _, files in os.walk(source_dir):
                        if skip_build:
                            rel_root = os.path.relpath(root, source_dir)
                            if rel_root == 'Build' or rel_root.startswith('Build' + os.path.sep):
                                continue  # 只跳过源目录下的 Build 文件夹
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join(
                                os.path.relpath(root, source_dir),
                                file
                            ).replace(os.path.sep, '/')
                            if arcname.startswith('./'):
                                arcname = arcname[2:]
                            try:
                                self.log_message(f"正在添加文件: {arcname}")
                                zipf.write(file_path, arcname)
                                file_count += 1
                                if file_count % 10 == 0:  # 每10个文件更新一次日志
                                    self.log_message(f"   已添加 {file_count} 个文件...")
                            except Exception as e:
                                self.log_message(f"❌ 添加文件失败: {arcname} - {str(e)}")
                                raise  # 重新抛出异常以停止构建
                            
                self.log_message(f"✅ 总共添加了 {file_count} 个文件")
                self.safe_rename(zip_temp_path, zip_path)
                
                # 重命名为.rwmod
                rwmod_path = os.path.join(self.build_output_dir, f"{file_name}.rwmod")
                if os.path.exists(rwmod_path):
                    self.safe_remove(rwmod_path)
                self.safe_rename(zip_path, rwmod_path)
                self.log_message(f"🎯 Mod包已创建: {rwmod_path}")
                
                # 如果选择快速移动
                if move_to_mods and rw_mods_path and os.path.exists(rw_mods_path):
                    target_path = os.path.join(rw_mods_path, f"{file_name}.rwmod")
                    
                    if os.path.exists(target_path):
                        self.log_message("⚠️  检测到已存在同名Mod文件")
                        self.kill_rw_process()
                        try:
                            self.safe_remove(target_path)
                            self.log_message(f"🗑️  已删除旧版Mod: {target_path}")
                        except Exception as e:
                            self.log_message(f"❌ 无法删除旧版Mod（可能被占用）: {e}")
                            self.log_message("⚠️ 请确保目标文件未被其他程序占用后重试")
                            self.progress_var.set("构建失败")
                            self.build_btn.configure(state="normal")
                            return
                        
                    shutil.copy2(rwmod_path, rw_mods_path)
                    self.log_message(f"🚀 Mod已复制到铁锈战争Mod文件夹: {target_path}")
                    self.log_message("🎉 构建完成！Mod已自动部署")
                else:
                    self.log_message("🎉 构建完成！")
                    
                self.progress_var.set("构建完成")
                # 使用系统通知（优先）或回退到弹窗
                self.send_notification("成功", "Mod构建完成！")
                # 如果记录了被关闭的游戏可执行文件，尝试在构建后重启游戏
                if self.close_and_restart_var.get() and self.killed_rw_exe:
                    try:
                        exe = self.killed_rw_exe
                        cwd = os.path.dirname(exe) if exe and os.path.dirname(exe) else None
                        subprocess.Popen([exe], cwd=cwd)
                        self.log_message(f"🚀 已尝试重启游戏: {exe}")
                    except Exception as e:
                        self.log_message(f"❌ 无法重启游戏: {e}")
                
            except Exception as e:
                self.log_message(f"❌ 打包过程中出现错误：{str(e)}")
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                messagebox.showerror("错误", f"打包过程中出现错误：{str(e)}")
                
        except Exception as e:
            self.log_message(f"❌ 发生未知错误：{str(e)}")
            messagebox.showerror("错误", f"发生未知错误：{str(e)}")
        finally:
            self.build_btn.configure(state="normal")
            self.progress_var.set("准备就绪")

def main():
    root = tk.Tk()
    app = PackageToolGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()