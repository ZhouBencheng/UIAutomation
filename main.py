import time
from pywinauto import Application
from pywinauto.keyboard import send_keys

def wechat_send_message():
    """发送消息到文件传输助手"""
    app = Application(backend='uia').connect(path='WeChat.exe')
    dlg_spec = app.window(title='微信')
    dlg_wrapper = dlg_spec.wrapper_object()
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