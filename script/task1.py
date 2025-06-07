"""
Task 1: Send a message to WeChat's File Transfer Assistant （给文件传输助手发一则消息）
"""
import os.path

from utils.connector import get_window_specification
from utils.gui_tree_exporter import export_gui_xml_structure

def send_message_to_wechat():
    """发送消息到微信"""
    app_path = 'WeChat.exe'
    window_title = '微信'
    # 连接到微信应用
    dlg_spec = get_window_specification(app_path, window_title)
    dlg_wrapper = dlg_spec.wrapper_object()

    # 确保窗口可见并获得焦点
    if not dlg_wrapper.is_visible():
        dlg_wrapper.set_focus()

    # 解析微信初始GUI状态
    output_dir = "../task/task1"
    state_num  = 1
    export_gui_xml_structure(app_path, window_title, output_dir, state_num)

    # 打开搜索框并输入联系人名称
    search_input_spec = dlg_spec.child_window(title='搜索', control_type='Edit')
    search_input = search_input_spec.wrapper_object()
    contact = '文件传输助手'
    search_input.click_input()
    search_input.type_keys(contact)

    # 解析搜索完成后的GUI状态
    state_num += 1
    export_gui_xml_structure(app_path, window_title, output_dir, state_num)

    # 点击联系人
    contact_spec = dlg_spec.child_window(title_re=f"{contact}", control_type='Button')
    contact_wrapper = contact_spec.wrapper_object()
    contact_wrapper.click_input()

if __name__ == '__main__':
    send_message_to_wechat()