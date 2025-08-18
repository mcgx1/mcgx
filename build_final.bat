@echo off
echo 正在构建最终版本mcgx.exe...
cd /d "E:\程序\xiangmu\mcgx"

echo 确保所有依赖已安装...
pip install -r requirements.txt
pip install PyQt5-sip

echo 开始打包...
pyinstaller mcgx_final.spec --clean

echo 构建完成！
echo 最终版本位置: E:\程序\xiangmu\mcgx\dist\mcgx_final.exe
echo 如果仍有问题，请运行此文件查看详细错误信息
pause
