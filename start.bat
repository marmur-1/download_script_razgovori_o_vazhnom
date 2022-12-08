@ECHO OFF
pip install requests 
pip install lxml
pip install bs4 
pip install tqdm
cd %~dp0
python -u main.py