# ȫ�ֱ�������
$targetPath = "D:\Program Files (x86)\Steam\steamapps\common\Rusted Warfare\mods\units" # ����Ŀ��·����Ĭ��Ϊnone��ʾ�����ƣ���Ҫʱ�����޸�Ϊ����·��

# ����Դ�ļ��к�Ŀ���ļ���
$sourceFolder = Join-Path $PSScriptRoot "ACMod-Sunset_and_shimmer"
$modName = (Split-Path $sourceFolder -Leaf) + "-Debug"

# ��������·��
$buildFolder = Join-Path $PSScriptRoot "Build"

# ���Դ�ļ����Ƿ����
if (-not (Test-Path $sourceFolder)) {
    Write-Error "Դ�ļ��в�����: $sourceFolder"
    exit 1
}
Write-Host "�ҵ�Դ�ļ���: $sourceFolder"
$outputPath = Join-Path $buildFolder "$modName.rwmod"
$tempZipPath = Join-Path $buildFolder "$modName.zip"
$targetFile = Join-Path $targetPath "$modName.rwmod"

# ȷ��Build�ļ��д���
if (-not (Test-Path $buildFolder)) {
    New-Item -ItemType Directory -Path $buildFolder -Force | Out-Null
    Write-Host "��������Ŀ¼: $buildFolder"
}

# ������ھ��ļ���ɾ��
if (Test-Path $outputPath) {
    Remove-Item $outputPath -Force
}
if (Test-Path $tempZipPath) {
    Remove-Item $tempZipPath -Force
}

try {
    # �ȴ���zip�ļ�
    Write-Host "����ѹ���ļ�..."
    Get-ChildItem -Path $sourceFolder | Compress-Archive -DestinationPath $tempZipPath -Force
    
    # ������Ϊrwmod
    Rename-Item -Path $tempZipPath -NewName ([System.IO.Path]::GetFileName($outputPath)) -Force
    Write-Host "ģ���ѳɹ������: $outputPath"

    # ����Ƿ���Ҫ���Ƶ�Ŀ��Ŀ¼
    if ($targetPath -ne "none" -and (Test-Path $targetPath)) {
        if (Test-Path $targetFile) {
            Remove-Item $targetFile -Force
        }
        
        Copy-Item $outputPath $targetFile -Force
        Write-Host "�ļ��ѳɹ����Ƶ�: $targetFile"
    } elseif ($targetPath -eq "none") {
        Write-Host "���������Ʋ���"
    } else {
        Write-Host "����: Ŀ��Ŀ¼������: $targetPath"
    }
} catch {
    Write-Error "��������г���: $_"
    exit 1
}
