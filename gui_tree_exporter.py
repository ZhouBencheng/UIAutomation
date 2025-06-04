import os
import json
from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.keyboard import send_keys
from datetime import datetime


def extract_control_info(ctrl: UIAWrapper, depth: int = 0, max_depth: int = 10, prefix: str = "") -> dict:
    """递归提取控件信息"""
    if depth > max_depth:
        return {}

    info = {
        "title": ctrl.window_text(),
        "control_type": ctrl.friendly_class_name(),
        "auto_id": ctrl.element_info.automation_id,
        "rect": str(ctrl.rectangle()),
        "depth": depth,
        "path": prefix,
    }

    try:
        children = ctrl.children()
    except Exception as e:
        children = []

    info["children"] = [
        extract_control_info(child, depth + 1, max_depth, prefix + f" -> {child.friendly_class_name()}[{child.window_text()}]")
        for child in children
    ]
    return info


def export_gui_structure(app_path: str, window_title: str, output_dir="gui_analysis", screenshot=False):
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

    # 控件结构导出
    gui_structure = extract_control_info(dlg_wrapper)
    with open(os.path.join(output_path, "structure.json"), "w", encoding="utf-8") as f:
        json.dump(gui_structure, f, ensure_ascii=False, indent=2)

    print(f"[INFO] JSON structure exported to: {output_path}")

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
        window_title="微信",      # 支持正则匹配
        output_dir="gui_export",
        screenshot=True          # 可设置为 False 关闭截图
    )
