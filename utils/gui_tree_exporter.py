import logging
import os
import json
from pywinauto.controls.uiawrapper import UIAWrapper
import xml.etree.ElementTree as ET
from datetime import datetime
import utils.classifier as classifier
from utils.connector import get_wrapper_object, weixin_app_path, weixin_title

logger = logging.getLogger()

############################### 容器滚动器 ###############################

def scroll_back(list_ctrl: UIAWrapper, max_iter=100):
    """向上滚动容器"""
    logger.debug(f"Start scrolling back in the list control")
    for _ in range(max_iter):
        try:
            # list_ctrl.set_focus()
            # send_keys('{PGUP}')  # 或 send_keys('{PGUP}')、list_ctrl.scroll等
            list_ctrl.type_keys('{PGUP}')
        except Exception:
            logger.debug("Failed to scroll back in the list control.")
            break
        # 等待一小段时间以确保滚动完成
        # send_keys('{WAIT}')

"""动态返回类型 List[dict] 或 List[ET.Element]"""
def extract_all_list_items(list_ctrl: UIAWrapper, depth=0, prefix: str="", flag=True, max_iter=100):
    """自动滚动容器并递归解析所有子项，返回去重后的完整元素列表"""
    logger.debug(f"Start extracting list items")
    seen_items = set()   # 记录已采集的唯一标识（如title、auto_id等）
    all_items_info = []

    for _ in range(max_iter):
        # 获取当前可见的所有子项
        try:
            children = list_ctrl.children()
        except Exception:
            logger.debug("Failed to retrieve children from the list control.")
            break
        changed = False
        for child in children:
            title = child.window_text()
            unique_key = (title, str(child.rectangle()))
            if unique_key not in seen_items:
                seen_items.add(unique_key)
                all_items_info.append(
                    extract_control_info(child, depth, prefix + f" -> {child.friendly_class_name()}[{child.window_text()}]")
                    if flag else control_info_to_xml(child, depth, prefix + f" -> {child.friendly_class_name()}[{child.window_text()}]")
                )
                changed = True
        # 尝试滚动
        try:
            # list_ctrl.set_focus()
            # send_keys('{PGDN}')
            list_ctrl.type_keys('{PGDN}')
        except Exception:
            logger.debug("Failed to scroll the list control.")
            break
        if not changed:  # 若本轮无新增条目，认为已滚至底部
            logger.debug("No new items found, stopping extraction.")
            break

    scroll_back(list_ctrl)
    return all_items_info

############################### 将GUI解析为XML结构 ###############################

def indent_xml(elem, level=0):
    """xml格式化工具"""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for idx, child in enumerate(elem):
            indent_xml(child, level + 1)
            # 判断是不是最后一个子节点
            if idx == len(elem) - 1:
                child.tail = i
            else:
                child.tail = "\n" + (level + 1) * "  " if level > 0 else "\n"
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def control_info_to_xml(ctrl: UIAWrapper, depth: int = 0, prefix: str = "", llm_trigger: bool = True, max_depth: int = 15) -> ET.Element:
    if depth > max_depth:
        return None

    attrs = {
        "title": ctrl.window_text(),
        "name": ctrl.element_info.name,
        "class_name": ctrl.element_info.class_name,
        "auto_id": ctrl.element_info.automation_id,
        "handle": str(ctrl.element_info.handle),
        "rect": str(ctrl.rectangle()),
        "depth": str(depth),
        "path": prefix.replace("->", "→")
    }
    if llm_trigger and ctrl.friendly_class_name() not in classifier.non_interactive_containers:
        attrs["is_dynamic"] = str(classifier.is_dynamic_control(ctrl))
    elem = ET.Element(ctrl.friendly_class_name(), attrs)

    try:
        children = ctrl.children()
    except Exception as e:
        children = []

    for child in children:
        child_elem = control_info_to_xml(child, depth + 1, prefix + f" -> {child.friendly_class_name()}[{child.window_text()}]")
        if child_elem is not None:
            elem.append(child_elem)
    return elem

def export_gui_xml_structure(dlg_wrapper: UIAWrapper, output_dir="gui_export", state_num=0) -> str:
    """ 将GUI导出为XML格式 """
    # 创建输出目录
    output_path = os.path.join(output_dir)
    os.makedirs(output_path, exist_ok=True)

    logger.info(f"Start extracting GUI structure for: {dlg_wrapper.window_text()}")

    # 控件XML结构导出
    root = control_info_to_xml(dlg_wrapper, llm_trigger=False)
    indent_xml(root)
    tree = ET.ElementTree(root)
    xml_path = os.path.join(output_path, f"state{state_num}.xml")
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    logger.info(f"XML structure exported to: {xml_path}")

    return xml_path # 返回输出路径

############################### 将GUI解析为JSON结构 ###############################

def extract_control_info(ctrl: UIAWrapper, depth: int = 0, prefix: str = "", max_depth: int = 15) -> dict:
    """递归提取控件信息并解析为JSON结构"""
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
        # extract_all_list_items(child, depth + 1, flag=True) if child.friendly_class_name() == "ListBox" else
        extract_control_info(child, depth + 1, prefix + f" -> {child.friendly_class_name()}[{child.window_text()}]")
        for child in children
    ]
    return info

def export_gui_json_structure(dlg_wrapper: UIAWrapper, output_dir="gui_export", state_num=0) -> str:
    """ 将GUI导出为JSON格式 """
    # 创建输出目录
    output_path = os.path.join(output_dir)
    os.makedirs(output_path, exist_ok=True)

    logger.info(f"Start extracting GUI structure for: {dlg_wrapper.window_text()}")

    # 控件JSON结构导出
    gui_structure = extract_control_info(dlg_wrapper)
    json_path = os.path.join(output_path, f"state{state_num}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(gui_structure, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON structure exported to: {output_path}")

    return json_path # 返回输出路径

"""将GUI导出为JSON和XML两种形式，并可选截图功能，该函数在本文件调用，用于测试和演示"""
def export_gui_structure(app_path: str, window_title: str, output_dir="gui_export", screenshot=False):
    """ 将GUI导出为JSON和XML两种形式 """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir += f"/{window_title}_{timestamp}"
    dlg_wrapper = get_wrapper_object(window_title)
    export_gui_json_structure(dlg_wrapper, output_dir)
    export_gui_xml_structure(dlg_wrapper, output_dir)

    # 可选截图
    if screenshot:
        image_path = os.path.join(output_dir, f"{window_title}_screenshot.png")
        image = dlg_wrapper.capture_as_image()
        image.save(image_path)
        logger.info(f"Screenshot exported to: {image_path}")

if __name__ == "__main__":
    # 以 Windows Wechat 为例
    classifier.clear_group_semantics_cache()
    export_gui_structure(
        app_path=weixin_app_path,
        window_title=weixin_title,       # 支持正则匹配
        output_dir="../gui_export",
        screenshot=False          # 可设置为 False 关闭截图
    )
