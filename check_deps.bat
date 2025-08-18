@echo off
echo 检查PyQt5依赖...
python -c "import PyQt5; print('PyQt5:', PyQt5.__version__)"
python -c "import PyQt5.sip; print('PyQt5.sip: OK')"
python -c "import PyQt5.QtCore; print('PyQt5.QtCore: OK')"
python -c "import PyQt5.QtGui; print('PyQt5.QtGui: OK')"
python -c "import PyQt5.QtWidgets; print('PyQt5.QtWidgets: OK')"
python -c "import psutil; print('psutil:', psutil.__version__)"

echo 依赖检查完成！
pause
