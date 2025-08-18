@echo off
echo 正在构建mcgx调试版本...
cd /d "E:\程序\xiangmu\mcgx"
pyinstaller mcgx_debug.spec --clean --log-level DEBUG
echo 调试构建完成！
echo 调试版本位置: E:\程序\xiangmu\mcgx\dist\mcgx_debug.exe
pause
