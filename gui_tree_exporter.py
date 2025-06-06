import os
import json
from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper
import xml.etree.ElementTree as ET
from datetime import datetime
from pywinauto.keyboard import send_keys

############################### 容器滚动器 ###############################

def scroll_back(list_ctrl: UIAWrapper, scroll_step=1, max_iter=100):
    """向上滚动容器"""
    print("[DEBUG] Start scrolling back in the list control")
    for _ in range(max_iter):
        try:
            list_ctrl.set_focus()
            send_keys('{PGUP}')  # 或 send_keys('{PGUP}')、list_ctrl.scroll等
        except Exception:
            print("[DEBUG] Failed to scroll back in the list control.")
            break
        # 等待一小段时间以确保滚动完成
        # send_keys('{WAIT}')

def extract_all_list_items(list_ctrl: UIAWrapper, scroll_step=1, max_iter=100) -> list:
    """自动滚动容器并递归解析所有子项，返回去重后的完整元素列表"""
    print("[DEBUG] Start extracting list items")
    seen_items = set()   # 记录已采集的唯一标识（如title、auto_id等）
    all_items_info = []

    for _ in range(max_iter):
        # 获取当前可见的所有子项
        try:
            children = list_ctrl.children()
        except Exception:
            print("[DEBUG] Failed to retrieve children from the list control.")
            break
        changed = False
        for child in children:
            title = child.window_text()
            unique_key = (title, child.element_info.automation_id)
            if unique_key not in seen_items:
                seen_items.add(unique_key)
                all_items_info.append(extract_control_info(child))
                changed = True
        # 尝试滚动
        try:
            list_ctrl.set_focus()
            send_keys('{PGDN}')
            # list_ctrl.type_keys('{PGDN}')
        except Exception:
            print("[DEBUG] Failed to scroll the list control.")
            break
        if not changed:  # 若本轮无新增条目，认为已滚至底部
            print("[DEBUG] No new items found, stopping extraction.")
            break

    scroll_back(list_ctrl)
    return all_items_info

############################### 将GUI解析为XML结构 ###############################

def indent_xml(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent_xml(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def control_info_to_xml(ctrl: UIAWrapper, depth: int = 0, max_depth: int = 10, prefix: str = "") -> ET.Element:
    if depth > max_depth:
        return None

    elem = ET.Element(ctrl.friendly_class_name(), {
        "title": ctrl.window_text(),
        "auto_id": ctrl.element_info.automation_id or "",
        "rect": str(ctrl.rectangle()),
        "depth": str(depth),
        "path": prefix
    })

    try:
        children = ctrl.children()
    except Exception as e:
        children = []

    for child in children:
        if child.friendly_class_name() == "ListBox":
            # 对于 ListBox 控件，提取所有子项
            items = extract_all_list_items(child)
            for item in items:
                item_elem = ET.Element("ListItem", item)
                elem.append(item_elem)
        else:
            child_elem = control_info_to_xml(child, depth + 1, max_depth, prefix + f" -> {child.friendly_class_name()}[{child.window_text()}]")
            if child_elem is not None:
                elem.append(child_elem)
    return elem

############################### 将GUI解析为JSON结构 ###############################

def extract_control_info(ctrl: UIAWrapper, depth: int = 0, max_depth: int = 10, prefix: str = "") -> dict:
    """递归提取控件信息"""
    if depth > max_depth:
        return {}

    info = {
        "title": ctrl.window_text(),
        "control_type": ctrl.friendly_class_name(),
        "auto_id": ctrl.element_info.automation_id,
        "rect": str(ctrl.rectangle()),
        "depth": str(depth),
        "path": prefix,
    }

    try:
        children = ctrl.children()
    except Exception as e:
        children = []

    info["children"] = [
        extract_all_list_items(child) if child.friendly_class_name() == "ListBox" else
        extract_control_info(child, depth + 1, max_depth, prefix + f" -> {child.friendly_class_name()}[{child.window_text()}]")
        for child in children
    ]
    return info

############################### GUI解析器 ###############################

def export_gui_structure(app_path: str, window_title: str, output_dir="gui_export", screenshot=False):
    """ 将GUI导出为JSON和XML两种形式 """
    app = Application(backend="uia").connect(path=app_path)
    print(f"[INFO] Successfully connect to {app_path}")
    dlg = app.window(title_re=window_title)
    dlg.wait("visible", timeout=3)

    dlg_wrapper = dlg.wrapper_object()

    # 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{window_title}_{timestamp}")
    os.makedirs(output_path, exist_ok=True)

    print(f"[INFO] Start extracting GUI structure for: {window_title}")

    # 控件JSON结构导出
    gui_structure = extract_control_info(dlg_wrapper)
    with open(os.path.join(output_path, "structure.json"), "w", encoding="utf-8") as f:
        json.dump(gui_structure, f, ensure_ascii=False, indent=2)
    print(f"[INFO] JSON structure exported to: {output_path}")

    # 控件XML结构导出
    root = control_info_to_xml(dlg_wrapper)
    indent_xml(root)
    tree = ET.ElementTree(root)
    xml_path = os.path.join(output_path, "structure.xml")
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    print(f"[INFO] XML structure exported to: {xml_path}")

    # 可选截图
    if screenshot:
        image_path = os.path.join(output_path, "screenshot.png")
        image = dlg_wrapper.capture_as_image()
        image.save(image_path)
        print(f"[INFO] Screenshot saved to: {image_path}")


if __name__ == "__main__":
    # 以 Windows Wechat 为例
    export_gui_structure(
        app_path="WeChat.exe",
        window_title="微信",       # 支持正则匹配
        output_dir="gui_export",
        screenshot=False          # 可设置为 False 关闭截图
    )
