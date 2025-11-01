import os
import shutil
import zipfile
import psutil
import time
import re

class PackageToolCLI:
    def __init__(self):
        self.base_name = "ACMod-Sunset_and_shimmer"
        self.mod_info_path = os.path.join(self.base_name, "mod-info.txt")
        
    def get_version_from_mod_info(self):
        """从mod-info.txt文件中提取版本号"""
        if not os.path.exists(self.mod_info_path):
            print(f"错误: {self.mod_info_path} 文件不存在")
            return None
            
        try:
            with open(self.mod_info_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 使用正则表达式匹配 Version*.*.* 格式
            version_pattern = r'Version\s*([\d.]+)'
            match = re.search(version_pattern, content)
            
            if match:
                version = match.group(1)
                print(f"从 {self.mod_info_path} 中检测到版本号: {version}")
                return version
            else:
                print(f"错误: 在 {self.mod_info_path} 中未找到版本号 (格式应为 Version*.*.*)")
                return None
                
        except Exception as e:
            print(f"读取 {self.mod_info_path} 时出现错误: {str(e)}")
            return None
    
    def save_version(self, version):
        """保存版本号到ver.txt"""
        with open("ver.txt", "w") as f:
            f.write(version)
        print(f"版本号 {version} 已保存到 ver.txt")
            
    def kill_rw_process(self):
        """结束铁锈战争进程"""
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'RustedWarfare.exe':
                print("检测到铁锈战争正在运行，正在结束进程...")
                proc.kill()
                time.sleep(1)
                print("铁锈战争进程已结束")
                return True
        return False
                
    def ask_yes_no(self, question, default=True):
        """询问是/否问题"""
        while True:
            if default:
                choice = input(f"{question} [Y/n]: ").strip().lower()
                if choice == '':
                    return True
            else:
                choice = input(f"{question} [y/N]: ").strip().lower()
                if choice == '':
                    return False
            
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("请输入 y 或 n")
    
    def ask_build_type(self):
        """询问构建类型"""
        while True:
            print("\n请选择构建类型:")
            print("1. 发行版 (Release)")
            print("2. 测试版 (Debug)")
            choice = input("请输入选择 [1]: ").strip()
            
            if choice == '' or choice == '1':
                return "release"
            elif choice == '2':
                return "debug"
            else:
                print("无效选择，请输入 1 或 2")
    
    def ask_rw_mods_path(self):
        """询问铁锈战争Mod路径"""
        default_paths = [
            r"/storage/emulated/0/rustedWarfare/units/",
            r"C:\Program Files (x86)\Steam\steamapps\common\Rusted Warfare\mods\units",
            r".\mods\units"  # 相对路径
        ]
        
        print("\n检测常用铁锈战争Mod路径...")
        for path in default_paths:
            if os.path.exists(path):
                print(f"检测到路径: {path}")
                if self.ask_yes_no("是否使用此路径?", default=True):
                    return path
        
        print("\n未检测到铁锈战争Mod文件夹，请手动输入路径")
        while True:
            path = input("请输入铁锈战争Mod文件夹路径: ").strip()
            if os.path.exists(path):
                return path
            else:
                if self.ask_yes_no("路径不存在，是否重新输入?", default=True):
                    continue
                else:
                    return None
    
    def build_mod(self):
        """构建Mod包 - 交互式版本"""
        print("=" * 50)
        print("铁锈战争Mod打包工具 CLI版本")
        print("=" * 50)
        
        # 自动获取版本号
        auto_version = self.get_version_from_mod_info()
        
        # 询问版本号
        if auto_version:
            if self.ask_yes_no(f"是否使用自动检测的版本号 {auto_version}?", default=True):
                version = auto_version
            else:
                version = input("请输入版本号: ").strip()
                if not version:
                    print("版本号不能为空")
                    return False
        else:
            version = input("请输入版本号: ").strip()
            if not version:
                print("版本号不能为空")
                return False
        
        # 询问构建类型
        build_type = self.ask_build_type()
        
        # 询问是否快速移动
        move_to_mods = self.ask_yes_no("是否快速移动到铁锈战争Mod文件夹?", default=True)
        
        rw_mods_path = None
        if move_to_mods:
            rw_mods_path = self.ask_rw_mods_path()
            if not rw_mods_path:
                print("未提供有效的Mod路径，取消快速移动")
                move_to_mods = False
        
        # 显示构建配置
        print("\n" + "=" * 30)
        print("构建配置确认:")
        print(f"版本号: {version}")
        print(f"构建类型: {build_type}")
        print(f"快速移动: {'是' if move_to_mods else '否'}")
        if move_to_mods:
            print(f"目标路径: {rw_mods_path}")
        print("=" * 30)
        
        if not self.ask_yes_no("确认开始构建?", default=True):
            print("构建已取消")
            return True
        
        # 保存版本号
        self.save_version(version)
        
        # 检查源文件夹是否存在
        if not os.path.exists(self.base_name):
            print(f"错误: 源文件夹 {self.base_name} 不存在")
            return False

        # 创建构建目录
        if not os.path.exists("Build"):
            os.makedirs("Build")
            print("创建 Build 目录")
            
        # 准备文件名
        if build_type == "debug":
            file_name = f"{self.base_name}_{version}_Debug"
        else:
            file_name = f"{self.base_name}_{version}"
            
        # 创建zip文件
        zip_path = os.path.join("Build", f"{file_name}.zip")
        try:
            print(f"\n正在打包 {self.base_name}...")
            file_count = 0
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                source_dir = os.path.abspath(self.base_name)
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
                        file_count += 1
                        print(f"添加文件: {arcname}")
                    
            print(f"总共添加了 {file_count} 个文件")
            
            # 重命名为.rwmod
            rwmod_path = os.path.join("Build", f"{file_name}.rwmod")
            if os.path.exists(rwmod_path):
                os.remove(rwmod_path)
            os.rename(zip_path, rwmod_path)
            print(f"Mod包已创建: {rwmod_path}")
            
            # 如果选择快速移动
            if move_to_mods and rw_mods_path:
                target_path = os.path.join(rw_mods_path, f"{file_name}.rwmod")
                
                if os.path.exists(target_path):
                    print("检测到已存在同名Mod文件")
                    self.kill_rw_process()
                    os.remove(target_path)
                    print(f"已删除旧版Mod: {target_path}")
                    
                shutil.copy2(rwmod_path, rw_mods_path)
                print(f"Mod已复制到铁锈战争Mod文件夹: {target_path}")
                print("🎉 构建完成！Mod已自动部署")
            else:
                print("🎉 构建完成！")
                
            return True
                
        except Exception as e:
            print(f"❌ 打包过程中出现错误：{str(e)}")
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return False

def main():
    tool = PackageToolCLI()
    
    try:
        success = tool.build_mod()
        if success:
            print("\n✅ 操作成功完成！")
        else:
            print("\n❌ 操作失败！")
            input("按Enter键退出...")
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消操作")
    except Exception as e:
        print(f"\n❌ 发生未知错误: {str(e)}")
    
    input("按Enter键退出...")

if __name__ == "__main__":
    main()