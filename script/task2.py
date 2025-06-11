"""Task2: Search for a specific message in a contact's chat history"""
import logging
import os
from pywinauto import Desktop, WindowSpecification
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.keyboard import send_keys
from utils.connector import get_window_specification, weixin_app_path, weixin_title
from utils.gui_tree_exporter import export_gui_xml_structure
import yaml
import re

def get_contact(contact:str, list_box_spec: WindowSpecification) -> UIAWrapper:
    """获取联系人的Button Wrapper"""
    seen_titles = set()
    max_scroll = 100
    list_box_wrapper = list_box_spec.wrapper_object()

    for _ in range(max_scroll):
        items = list_box_wrapper.children()
        changed = False
        for item in items:
            unique_key = item.window_text()
            if item not in seen_titles:
                seen_titles.add(unique_key)
                changed = True
                if re.search(contact, unique_key):
                    # item中将只存在一个button，descentdants()方法返回wrapper列表
                    return item

        try:
            list_box_wrapper.set_focus()
            send_keys('{PGDN}')
        except:
            logging.debug("Failed to scroll the list control.")
            break

        if not changed:
            logging.debug("No new items found, stopping extraction.")
            break

    logging.debug("No new button found")
    return list_box_spec.child_window(title_re=f'{contact}.*', control_type='ListItem').wrapper_object()


def search_message_in_contact():
    """在微信联系人聊天记录中搜索特定消息"""
    app_path = weixin_app_path
    window_title = weixin_title
    # 连接到微信应用
    dlg_spec = get_window_specification(app_path, window_title)
    dlg_wrapper = dlg_spec.wrapper_object()

    # 确保窗口可见并获得焦点
    if not dlg_wrapper.is_visible():
        dlg_wrapper.set_focus()

    # 解析微信初始GUI状态
    action_trace = []
    output_dir = r"..\tasks\task2"
    state_num  = 1
    state_path = os.path.split(export_gui_xml_structure(dlg_wrapper, output_dir, state_num))[1]

    # 点击微信联系人
    contact = 'ben'
    list_box_spec = dlg_spec.child_window(title='会话', control_type='List')
    contact_button_wrapper = get_contact(contact, list_box_spec)
    contact_button_wrapper.click_input()

    # 解析搜索完成后的GUI状态
    state_num += 1 # 2
    new_state_path = os.path.split(export_gui_xml_structure(dlg_wrapper, output_dir, state_num))[1]

    action_trace.append({
        'Action': 'click',
        'Control': {
            'type': 'Button',
            'title': contact
        },
        'Input': 'null',
        'State': state_path,
        'New_State': new_state_path,
    })

    # 点击“聊天记录”按钮
    chat_history_button_spec = dlg_spec.child_window(title='聊天记录', control_type='Button')
    chat_history_button_wrapper = chat_history_button_spec.wrapper_object()
    chat_history_button_wrapper.click_input()

    # 解析点击聊天记录后的GUI状态
    chat_history_window_spec = Desktop(backend='uia').window(title=f'与“{contact}”的聊天记录')
    chat_history_window_wrapper = chat_history_window_spec.wrapper_object()
    state_num += 1 # 3
    state_path = new_state_path
    new_state_path = os.path.split(export_gui_xml_structure(chat_history_window_wrapper, output_dir, state_num))[1]

    action_trace.append({
        'Action': 'click',
        'Control': {
            'type': 'Button',
            'title': '聊天记录'
        },
        'Input': 'null',
        'State': state_path,
        'New_State': new_state_path,
    })

    # 搜索框输入待查找内容
    search_input_spec = chat_history_window_spec.child_window(class_name='mmui::XValidatorTextEdit', control_type='Edit')
    search_input_wrapper = search_input_spec.wrapper_object()
    message = 'Hello, ben'
    search_input_wrapper.click_input()
    search_input_wrapper.type_keys(message, with_spaces=True)

    state_num += 1 # 4
    state_path = new_state_path
    new_state_path = os.path.split(export_gui_xml_structure(chat_history_window_wrapper, output_dir, state_num))[1]

    action_trace.append({
        'Action': 'input',
        'Control':{
            'type': 'Edit',
            'title': '',
            'class_name': 'mmui::XValidatorTextEdit'
        },
        'Input': message,
        'State': state_path,
        'New_State': new_state_path,
    })

    with open(os.path.join(output_dir, 'utg2.yaml'), 'w', encoding='utf-8') as f:
        yaml.dump(action_trace, f, allow_unicode=True)

if __name__ == "__main__":
    search_message_in_contact()
