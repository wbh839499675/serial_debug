import os
import shutil
import numpy
import PyInstaller.__main__
from utils.path_manager import PathManager

# 项目根目录
project_root = PathManager._PROJECT_ROOT

# 资源目录
resources_dir = PathManager.RESOURCES_DIR
docs_dir = PathManager.DOCS_DIR

numpy_path = os.path.dirname(numpy.__file__)

# 清理旧的打包文件
def clean_build_dirs():
    """清理旧的打包目录"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        dir_path = os.path.join(project_root, dir_name)
        if os.path.exists(dir_path):
            try:
                # 先尝试删除目录内容
                for item in os.listdir(dir_path):
                    item_path = os.path.join(dir_path, item)
                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        else:
                            shutil.rmtree(item_path)
                    except Exception as e:
                        print(f"清理文件/目录失败 {item_path}: {str(e)}")

                # 再删除目录本身
                shutil.rmtree(dir_path)
                print(f"已清理目录: {dir_path}")
            except Exception as e:
                print(f"清理目录失败 {dir_path}: {str(e)}")
                return False
    return True

def create_installer():
    """使用Inno Setup创建安装程序"""
    import subprocess
    import urllib.request
    import tempfile

    # 安装程序输出路径
    installer_output = os.path.join(project_root, "dist", "CAT1_ProTest_Suite_Setup.exe")
    # 应用程序源目录
    app_source_dir = os.path.join(project_root, "dist")

    # 检查并安装Inno Setup
    def install_inno_setup():
        print("正在检查Inno Setup安装情况...")
        # 检查常见安装路径
        possible_paths = [
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Inno Setup 6", "ISCC.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Inno Setup 6", "ISCC.exe"),
            "ISCC.exe"  # 如果在PATH中
        ]

        for path in possible_paths:
            if os.path.exists(path):
                # 检查中文语言文件是否存在
                inno_dir = os.path.dirname(path)
                lang_file = os.path.join(inno_dir, "Languages", "ChineseSimp.isl")
                if not os.path.exists(lang_file):
                    print(f"警告: Inno Setup中文语言文件不存在: {lang_file}")
                    print("将使用默认语言创建安装程序")
                return path

        # 如果未找到，尝试下载安装
        print("未找到Inno Setup，正在尝试自动下载安装...")
        try:
            # Inno Setup下载地址
            url = "https://files.jrsoftware.org/is/6/innosetup-6.2.2.exe"
            installer_path = os.path.join(tempfile.gettempdir(), "innosetup_installer.exe")

            print(f"正在下载Inno Setup安装程序到: {installer_path}")
            urllib.request.urlretrieve(url, installer_path)

            print("正在安装Inno Setup，请稍候...")
            subprocess.run([installer_path, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/DIR=" + os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Inno Setup 6")], check=True)

            # 等待安装完成
            import time
            time.sleep(10)

            # 重新检查安装路径
            for path in possible_paths:
                if os.path.exists(path):
                    return path

            print("Inno Setup安装完成，但未找到ISCC.exe")
            return None
        except Exception as e:
            print(f"自动安装Inno Setup失败: {str(e)}")
            print("请手动下载并安装Inno Setup: https://jrsoftware.org/isdl.php")
            return None

    # 获取或安装Inno Setup
    iscc_path = install_inno_setup()
    if not iscc_path:
        return False

    # 创建应用程序目录
    app_dir = os.path.join(project_root, "dist", "CAT1 ProTest Suite")
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)

    # 复制可执行文件
    exe_source = os.path.join(project_root, "dist", "CAT1 ProTest Suite.exe")
    exe_dest = os.path.join(app_dir, "CAT1 ProTest Suite.exe")
    if os.path.exists(exe_source):
        if os.path.exists(exe_dest):
            os.remove(exe_dest)
        shutil.copy2(exe_source, exe_dest)
        print(f"已复制可执行文件到: {exe_dest}")

    # 复制script目录到应用程序根目录
    script_source = os.path.join(project_root, "script")
    script_dest = os.path.join(app_dir, "script")
    if os.path.exists(script_source):
        if os.path.exists(script_dest):
            shutil.rmtree(script_dest)
        shutil.copytree(script_source, script_dest)
        print(f"已复制script目录到: {script_dest}")

    # 检查中文语言文件是否存在
    inno_dir = os.path.dirname(iscc_path)
    lang_file = os.path.join(inno_dir, "Languages", "ChineseSimp.isl")
    use_chinese = os.path.exists(lang_file)

    # Inno Setup脚本内容
    if use_chinese:
        iss_content = f"""[Setup]
AppName=CAT1 ProTest Suite
AppVersion=1.0
DefaultDirName={{autopf}}\\CAT1 ProTest Suite
DefaultGroupName=CAT1 ProTest Suite
OutputDir={os.path.join(project_root, "dist")}
OutputBaseFilename=CAT1_ProTest_Suite_Setup
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={{app}}\\CAT1 ProTest Suite.exe
UninstallDisplayName=CAT1 ProTest Suite 卸载程序
UninstallFilesDir={{app}}\\Uninstall
CreateUninstallRegKey=yes
WizardStyle=modern
; 添加Unicode支持
WizardImageBackColor=clWhite
WizardSmallImageBackColor=clWhite
; 添加以下行以支持Unicode
[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\\ChineseSimp.isl"
; 添加以下行以设置字体
[Messages]
BeveledLabel=安装向导

[Files]
Source: "{app_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\CAT1 ProTest Suite"; Filename: "{{app}}\\CAT1 ProTest Suite.exe"
Name: "{{commondesktop}}\\CAT1 ProTest Suite"; Filename: "{{app}}\\CAT1 ProTest Suite.exe"
Name: "{{group}}\\卸载 CAT1 ProTest Suite"; Filename: "{{uninstallexe}}"

[Run]
Filename: "{{app}}\\CAT1 ProTest Suite.exe"; Description: "启动应用"; Flags: nowait postinstall skipifsilent
"""
    else:
        iss_content = f"""[Setup]
AppName=CAT1 ProTest Suite
AppVersion=1.0
DefaultDirName={{autopf}}\\CAT1 ProTest Suite
OutputDir={os.path.join(project_root, "dist")}
OutputBaseFilename=CAT1_ProTest_Suite_Setup
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={{app}}\\CAT1 ProTest Suite.exe
UninstallDisplayName=CAT1 ProTest Suite Uninstaller
UninstallFilesDir={{app}}\\Uninstall
CreateUninstallRegKey=yes
WizardStyle=modern
; 添加Unicode支持
WizardImageBackColor=clWhite
WizardSmallImageBackColor=clWhite

[Files]
Source: "{app_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\CAT1 ProTest Suite"; Filename: "{{app}}\\CAT1 ProTest Suite.exe"
Name: "{{commondesktop}}\\CAT1 ProTest Suite"; Filename: "{{app}}\\CAT1 ProTest Suite.exe"
Name: "{{group}}\\Uninstall CAT1 ProTest Suite"; Filename: "{{uninstallexe}}"

[Run]
Filename: "{{app}}\\CAT1 ProTest Suite.exe"; Description: "Launch Application"; Flags: nowait postinstall skipifsilent
"""

    # 保存ISS脚本
    iss_file = os.path.join(project_root, "build_exe.iss")
    with open(iss_file, 'w', encoding='utf-8-sig') as f:
        f.write(iss_content)

    # 调用Inno Setup编译器
    try:
        subprocess.run([iscc_path, iss_file], check=True)
        print(f"安装程序已生成: {installer_output}")
        return True
    except Exception as e:
        print(f"创建安装程序失败: {str(e)}")
        return False


# 应用程序入口
app_entry = os.path.join(project_root, "main.py")

# 清理旧的打包文件
if clean_build_dirs():
    print("清理旧的打包文件成功！")
else:
    print("清理旧的打包文件失败，继续打包...")

# 打包配置
PyInstaller.__main__.run([
    app_entry,
    '--name=CAT1 ProTest Suite',
    '--onedir',
    '--windowed',
    f'--icon={PathManager.ICONS_DIR / "app_icon.ico"}',
    f'--add-data={resources_dir};resources',
    f'--add-data={docs_dir};docs',
    f'--add-data={numpy_path};numpy',
    '--contents-directory=Resources',  # 更改内部资源目录名称为Resources
    '--hidden-import=pyqtgraph',
    '--hidden-import=pyqtgraph.graphicsItems.PlotItem',
    '--hidden-import=pyqtgraph.graphicsItems.ViewBox',
    '--hidden-import=pyqtgraph.graphicsItems.AxisItem',
    '--hidden-import=pyqtgraph.graphicsItems.GraphicsItem',
    '--hidden-import=usb.core',
    '--hidden-import=usb.util',
    '--hidden-import=numpy',
    '--hidden-import=numpy.core._multiarray_umath',
    '--hidden-import=numpy.core._dtype_ctypes',
    '--hidden-import=numpy.linalg._umath_linalg',
    '--hidden-import=numpy.linalg.lapack_lite',
    '--hidden-import=encodings',
    '--hidden-import=encodings.aliases',
    '--hidden-import=encodings.cp437',
    '--hidden-import=encodings.utf_8',
    '--exclude-module=numpy.distutils',
    '--exclude-module=numpy.f2py',
    '--exclude-module=numpy.testing',
    '--exclude-module=pyqtgraph.opengl',
    '--additional-hooks-dir=' + os.path.join(project_root, 'hooks'),
    '--clean',
    '--noconfirm',
    '--noupx',
    '--collect-all=numpy',  # 收集numpy的所有依赖
    '--collect-all=pyqtgraph',  # 收集pyqtgraph的所有依赖
    '--collect-all=pyusb',  # 收集pyusb的所有依赖
    '--hidden-import=usb.backend.libusb1',  # 添加这一行
    '--hidden-import=usb.backend.libusb0',  # 添加这一行
])

# 创建安装程序
if create_installer():
    print("安装程序创建成功！")
else:
    print("安装程序创建失败，但应用程序已打包完成。")
