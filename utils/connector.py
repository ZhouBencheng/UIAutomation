from pywinauto import Application, Desktop
from pywinauto.controls.uiawrapper import UIAWrapper
import logging

logging.basicConfig(level=logging.INFO)
weixin_app_path = r'C:\Program Files\Tencent\Weixin\Weixin.exe'
weixin_title = '微信'

def get_wrapper_object(app_path: str, title: str) -> UIAWrapper:
    """连接到微信应用并返回窗口的UIA包装对象"""
    app = Application(backend='uia').connect(path=app_path)
    dlg_wrapper = Desktop(backend='uia').window(title=title).wrapper_object()
    logging.info(f"Successfully connect to {app_path}")

    return dlg_wrapper

def get_window_specification(app_path: str, title: str):
    """获取窗口的规格说明"""
    app = Application(backend='uia').connect(path=app_path)
    dlg_spec = Desktop(backend='uia').window(title=title)
    logging.info(f"Successfully connect to {app_path}")

    return dlg_spec