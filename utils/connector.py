from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper
import logging

logging.basicConfig(level=logging.INFO)

def get_wrapper_object(app_path: str, title: str) -> UIAWrapper:
    """连接到微信应用并返回窗口的UIA包装对象"""
    # 连接到微信应用
    # 注意：请确保WeChat.exe的路径正确，可能需要根据实际情况调整
    app = Application(backend='uia').connect(path=app_path)
    logging.info(f"Successfully connect to {app_path}")

    dlg_spec = app.window(title_re=title)
    dlg_wrapper = dlg_spec.wrapper_object()
    return dlg_wrapper

def get_window_specification(app_path: str, title: str):
    """获取窗口的规格说明"""
    app = Application(backend='uia').connect(path=app_path)
    logging.info(f"Successfully connect to {app_path}")

    dlg_spec = app.window(title_re=title)
    return dlg_spec