@echo off
echo 正在构建mcgx.exe...
cd /d "E:\程序\xiangmu\mcgx"
pyinstaller mcgx.spec --clean
echo 构建完成！
echo 可执行文件位置: E:\程序\xiangmu\mcgx\dist\mcgx.exe
pause
