@echo off
echo 正在构建编码安全版本的mcgx.exe...
cd /d "E:\程序\xiangmu\mcgx"
pyinstaller mcgx_safe.spec --clean
echo 构建完成！
echo 编码安全版本位置: E:\程序\xiangmu\mcgx\dist\mcgx_safe.exe
pause
