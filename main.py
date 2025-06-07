import time
from pywinauto import Application
from pywinauto.keyboard import send_keys
from utils.connector import get_wrapper_object

def wechat_send_message():
    """发送消息到文件传输助手"""
    dlg_wrapper = get_wrapper_object('WeChat.exe', '微信')
    # 确保窗口可见
    if not dlg_wrapper.is_visible():
        dlg_wrapper.set_focus()

    # 打开搜索框并输入联系人名称
    dlg_wrapper.set_focus()
    dlg_wrapper.type_keys('^f')  # Ctrl+F
    time.sleep(1)  # 等待搜索框出现
    dlg_wrapper.type_keys('文件传输助手', with_spaces=True)
    time.sleep(1)  # 等待搜索结果加载
    send_keys('{ENTER}')
    dlg_wrapper.type_keys('测试信息', with_spaces=True)
    time.sleep(1)
    send_keys('{ENTER}')

if __name__ == '__main__':
    wechat_send_message()