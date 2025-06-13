from pywinauto import Desktop, Application

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
    dlg_spec = get_window_specification(weixin_app_path, weixin_title)
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
    test_spec.print_control_identifiers()
    test_wrapper = test_spec.wrapper_object()
    test_wrapper.maximize()

def test_new_window():
    app = Application(backend="uia").connect(title=weixin_title)
    dlg_spec = app.top_window()
    dlg_wrapper = dlg_spec.wrapper_object()
    handle = dlg_wrapper.element_info.handle
    # dlg_wrapper.close()
    test_app = Application(backend='uia').connect(handle=handle)
    test_wrapper = test_app.window(handle=handle)
    test_wrapper.restore()
    # moments_button_spec = dlg_spec.child_window(control_type='Button', title='朋友圈')
    # moments_button_spec.print_control_identifiers()
    # moments_button_wrapper = moments_button_spec.window(control_type='Button').wrapper_object()
    # moments_button_wrapper.invoke()

if __name__ == '__main__':
    test_new_window()