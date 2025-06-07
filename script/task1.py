"""
Task 1: Send a message to WeChat's File Transfer Assistant （给文件传输助手发一则消息）
"""

import time
from utils.connector import get_window_specification

def send_message_to_wechat():
    """发送消息到微信"""
    # 连接到微信应用
    dlg_spec = get_window_specification('WeChat.exe', '微信')
    dlg_wrapper = dlg_spec.wrapper_object()

    # 确保窗口可见并获得焦点
    if not dlg_wrapper.is_visible():
        dlg_wrapper.set_focus()

    search_input_spec = dlg_spec.child_window(title='搜索', control_type='Edit')
    search_input = search_input_spec.wrapper_object()

    contact = '文件传输助手'
    search_input.click_input()
    search_input.type_keys(contact)



if __name__ == '__main__':
    send_message_to_wechat()