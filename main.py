import time
from pywinauto import Application
from pywinauto.keyboard import send_keys
from utils.connector import get_wrapper_object, weixin_app_path, weixin_title, get_window_specification

def wechat_send_message():
    """发送消息到文件传输助手"""
    dlg_spec = get_window_specification(weixin_app_path, weixin_title)
    dlg_wrapper = dlg_spec.wrapper_object()
    # 确保窗口可见
    if not dlg_wrapper.is_visible():
        dlg_wrapper.set_focus()

    search_input_spec = dlg_spec.child_window(control_type='Edit')
    search_input = search_input_spec.wrapper_object()
    print(search_input.element_info.control_type, '\n',
          search_input.element_info.automation_id, '\n',
          search_input.element_info.framework_id, '\n',
          search_input.element_info.class_name,'\n',
          search_input.element_info.runtime_id,'\n',
          search_input.element_info.control_id, '\n',
          search_input.element_info.name)
    search_input.click_input()
    search_input.type_keys('文件传输助手')

if __name__ == '__main__':
    wechat_send_message()