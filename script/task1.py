"""
Task 1: Send a message to WeChat's File Transfer Assistant （给文件传输助手发一则消息）
"""
import os
from utils.connector import get_window_specification
from utils.gui_tree_exporter import export_gui_xml_structure
import yaml

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
    action_trace = []
    output_dir = r"..\tasks\task1"
    state_num  = 1
    state_path = os.path.split(export_gui_xml_structure(dlg_wrapper, output_dir, state_num))[1]

    # 打开搜索框并输入联系人名称
    search_input_spec = dlg_spec.child_window(title='搜索', control_type='Edit')
    search_input = search_input_spec.wrapper_object()
    contact = '文件传输助手'
    search_input.click_input()
    search_input.type_keys(contact)

    # 解析搜索完成后的GUI状态
    state_num += 1
    new_state_path = os.path.split(export_gui_xml_structure(dlg_wrapper, output_dir, state_num))[1]

    action_trace.append({
        'Action': 'input',
        'Control': {
            'type': 'Edit',
            'title': '搜索',
        },
        'Input': contact,
        'State': state_path,
        'New_State': new_state_path
    })

    # 点击联系人
    contact_spec = dlg_spec.child_window(title=f"{contact}", control_type='Button', depth=9)
    contact_wrapper = contact_spec.wrapper_object()
    contact_wrapper.click_input()

    # 解析点击联系人后的GUI状态
    state_num += 1
    state_path = new_state_path
    new_state_path = os.path.split(export_gui_xml_structure(dlg_wrapper, output_dir, state_num))[1]

    action_trace.append({
        'Action': 'click',
        'Control': {
            'type': 'Button',
            'title': contact,
            'depth': 9
        },
        'Input': 'null',
        'State': state_path,
        'New_State': new_state_path
    })

    # 输入消息内容
    message = 'Hello, this is a test message from the automation script!'
    message_input_spec = dlg_spec.child_window(title=contact, control_type='Edit')
    message_input = message_input_spec.wrapper_object()
    message_input.type_keys(message, with_spaces=True)

    # 解析输入消息后的GUI状态
    state_num += 1
    state_path = new_state_path
    new_state_path = os.path.split(export_gui_xml_structure(dlg_wrapper, output_dir, state_num))[1]

    action_trace.append({
        'Action': 'input',
        'Control': {
            'type': 'Edit',
            'title': contact,
        },
        'Input': message,
        'State': state_path,
        'New_State': new_state_path
    })

    # 发送消息
    send_button_spec = dlg_spec.child_window(title='发送(S)', control_type='Button')
    send_button = send_button_spec.wrapper_object()
    send_button.click_input()

    # 解析发送消息后的GUI状态
    state_num += 1
    state_path = new_state_path
    new_state_path = os.path.split(export_gui_xml_structure(dlg_wrapper, output_dir, state_num))[1]

    action_trace.append({
        'Action': 'click',
        'Control': {
            'type': 'Button',
            'title': '发送(S)',
        },
        'Input': 'null',
        'State': state_path,
        'New_State': new_state_path
    })

    with open(os.path.join(output_dir, 'utg1.yaml'), 'w', encoding='utf-8') as f:
        yaml.dump(action_trace, f, allow_unicode=True)


if __name__ == '__main__':
    send_message_to_wechat()