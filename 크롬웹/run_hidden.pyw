# -*- coding: utf-8 -*-
"""AI 견적 서버 '숨김' 실행 런처.
pythonw(pyw)로 돌리면 검은 CMD 창 없이 백그라운드로 실행되고,
화면/오류 로그는 상위(견적) 폴더의 server.log 에 저장된다.
"""
import os
import sys
import runpy

# 이 파일은 크롬웹 하위폴더에 있고, 실제 앱(web_server.py/config.json)은 상위 견적 폴더에 있음
_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_HERE)
os.chdir(_APP_DIR)
sys.path.insert(0, _APP_DIR)

_log = open(os.path.join(_APP_DIR, "server.log"), "w", encoding="utf-8", buffering=1)
sys.stdout = _log
sys.stderr = _log

runpy.run_path(os.path.join(_APP_DIR, "web_server.py"), run_name="__main__")
