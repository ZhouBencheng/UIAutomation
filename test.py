import time

from pywinauto import Desktop, Application
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
          search_input.element_info.handle, '\n',
          search_input.element_info.automation_id, '\n',
          search_input.element_info.framework_id, '\n',
          search_input.element_info.class_name,'\n',
          search_input.element_info.runtime_id,'\n',
          search_input.element_info.control_id, '\n',
          search_input.element_info.name)

def test_elem_info():
    dlg_spec = get_window_specification(weixin_title)
    dlg_wrapper = dlg_spec.wrapper_object()
    print(dlg_wrapper.element_info.control_type, '\n',
          dlg_wrapper.element_info.handle, '\n',
          dlg_wrapper.element_info.automation_id, '\n',
          dlg_wrapper.element_info.framework_id, '\n',
          dlg_wrapper.element_info.class_name,'\n',
          dlg_wrapper.element_info.runtime_id,'\n',
          dlg_wrapper.element_info.control_id, '\n',
          dlg_wrapper.element_info.name)
    handle = dlg_wrapper.element_info.handle
    test_spec = Desktop(backend='uia').window(handle=handle)
    test_wrapper = test_spec.wrapper_object()
    test_wrapper.maximize()

def test_new_window():
    app = Application(backend="uia").connect(title=weixin_title)
    dlg_spec = app.top_window()
    dlg_wrapper = dlg_spec.wrapper_object()
    prog_button_spec = dlg_spec.child_window(control_type='Button', title='朋友圈')
    prog_button_wrapper = prog_button_spec.wrapper_object()
    before_handles = [w.element_info.handle for w in Desktop(backend="uia").windows()]
    prog_button_wrapper.click_input()
    time.sleep(1)  # 等待小程序面板打开
    def get_latest_window_handle(before_handles: list):
        time.sleep(0.5)  # 等待新窗口打开
        after_handles = [w.element_info.handle for w in Desktop(backend="uia").windows()]
        new_handles = set(after_handles) - set(before_handles)
        if new_handles:
            handle = new_handles.pop()
            return Desktop(backend="uia").window(handle=handle).wrapper_object()

    new_window = get_latest_window_handle(before_handles)
    new_window.close()

def test_search_input():
    dlg_spec = get_window_specification(weixin_title)
    dlg_wrapper = dlg_spec.wrapper_object()
    search_input_spec = dlg_spec.child_window(control_type='Edit')
    search_input = search_input_spec.wrapper_object()
    search_input.set_text('测试输入')
    time.sleep(1)  # 等待输入完成
    search_input.type_keys('^A{BACKSPACE}' + '清除输入')  # 清除输入

def test_restore():
    """测试恢复窗口"""
    dlg_spec = get_window_specification(weixin_title)
    dlg_wrapper = dlg_spec.wrapper_object()
    # prog_button_spec = dlg_spec.child_window(control_type='Button', title='通讯录')
    # prog_button_wrapper = prog_button_spec.wrapper_object()
    # prog_button_wrapper.click_input()
    dlg_wrapper.minimize()
    time.sleep(1)
    dlg_wrapper.restore()  # 恢复窗口

if __name__ == '__main__':
    test_restore()