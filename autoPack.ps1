# 全局变量设置
$targetPath = "D:\Program Files (x86)\Steam\steamapps\common\Rusted Warfare\mods\units" # 设置目标路径，默认为none表示不复制，需要时可以修改为具体路径

# 设置源文件夹和目标文件夹
$sourceFolder = Join-Path $PSScriptRoot "ACMod-Sunset_and_shimmer"
$modName = (Split-Path $sourceFolder -Leaf) + "-Debug"

# 设置完整路径
$buildFolder = Join-Path $PSScriptRoot "Build"

# 检查源文件夹是否存在
if (-not (Test-Path $sourceFolder)) {
    Write-Error "源文件夹不存在: $sourceFolder"
    exit 1
}
Write-Host "找到源文件夹: $sourceFolder"
$outputPath = Join-Path $buildFolder "$modName.rwmod"
$tempZipPath = Join-Path $buildFolder "$modName.zip"
$targetFile = Join-Path $targetPath "$modName.rwmod"

# 确保Build文件夹存在
if (-not (Test-Path $buildFolder)) {
    New-Item -ItemType Directory -Path $buildFolder -Force | Out-Null
    Write-Host "创建构建目录: $buildFolder"
}

# 如果存在旧文件则删除
if (Test-Path $outputPath) {
    Remove-Item $outputPath -Force
}
if (Test-Path $tempZipPath) {
    Remove-Item $tempZipPath -Force
}

try {
    # 先创建zip文件
    Write-Host "正在压缩文件..."
    Get-ChildItem -Path $sourceFolder | Compress-Archive -DestinationPath $tempZipPath -Force
    
    # 重命名为rwmod
    Rename-Item -Path $tempZipPath -NewName ([System.IO.Path]::GetFileName($outputPath)) -Force
    Write-Host "模组已成功打包到: $outputPath"

    # 检查是否需要复制到目标目录
    if ($targetPath -ne "none" -and (Test-Path $targetPath)) {
        if (Test-Path $targetFile) {
            Remove-Item $targetFile -Force
        }
        
        Copy-Item $outputPath $targetFile -Force
        Write-Host "文件已成功复制到: $targetFile"
    } elseif ($targetPath -eq "none") {
        Write-Host "已跳过复制操作"
    } else {
        Write-Host "错误: 目标目录不存在: $targetPath"
    }
} catch {
    Write-Error "处理过程中出错: $_"
    exit 1
}
