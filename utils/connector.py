from pywinauto import Desktop
from pywinauto.controls.uiawrapper import UIAWrapper
import logging

weixin_app_path = r'C:\Program Files\Tencent\Weixin\Weixin.exe'
weixin_title = '微信'
logger = logging.getLogger(__name__)

def get_wrapper_object(title: str = None) -> UIAWrapper:
    """连接到微信应用并返回窗口的UIA包装对象"""
    dlg_wrapper = Desktop(backend='uia').window(title=title).wrapper_object()
    logger.info(f"Successfully connect to {title}")

    return dlg_wrapper

def get_window_specification(title: str):
    """获取窗口的规格说明"""
    dlg_spec = Desktop(backend='uia').window(title=title)
    logger.info(f"Successfully connect to {title}")

    return dlg_spec