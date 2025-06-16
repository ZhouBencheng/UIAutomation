import logging
import os
import re
import shutil
import time

from pywinauto import Desktop, Application
from pywinauto.controls.uiawrapper import UIAWrapper
import yaml
import xml.etree.ElementTree as ET

import utils.classifier as classifier
from utils.gui_tree_exporter import export_gui_xml_structure, indent_xml

TEST_INPUTS = ["测试", "文件传输助手", "Hello", "12345", "!@#$%"]
logger = logging.getLogger()


def get_control_id(ctrl: UIAWrapper, gui_xml_tree: ET.ElementTree):
    """
    用绝对XPATH获取控件的唯一标识符，优先使用auto_id、title或name属性，最后使用索引
    """
    def get_best_attr(elem):
        for attr in ["auto_id", "title", "name"]:
            val = elem.attrib.get(attr, "")
            if val:
                val = val.replace('"', '\\"')
                return f'@{attr}="{val}"'
        return None

    root_elem = gui_xml_tree.getroot()
    ancestors = [] # 获取控件的祖先列表
    current_ctrl = ctrl
    while current_ctrl is not None:
        ancestors.insert(0, current_ctrl)
        try:
            parent_ctrl = current_ctrl.parent()
        except Exception:
            parent_ctrl = None
        current_ctrl = parent_ctrl

    logger.debug(f"ancestors: {ancestors}")
    if not ancestors or root_elem.tag != ancestors[1].friendly_class_name():
        raise Exception("Root node mismatch, cannot generate XPath")

    xpath_parts = [f"/{root_elem.tag}"]
    parent_elem = root_elem
    for ctrl_obj in ancestors[2:]:
        tag = ctrl_obj.friendly_class_name()
        same_type_children = parent_elem.findall(tag)
        if not same_type_children:
            logger.debug(f"Fail to find children with tag: {tag} in parent: {parent_elem.tag}")
            raise Exception("Cannot find control path in XML structure")

        matched = False
        for idx, child_elem in enumerate(same_type_children):
            best_attr = get_best_attr(child_elem)
            ctrl_auto_id = getattr(ctrl_obj, "automation_id", lambda: "")()
            ctrl_title = getattr(ctrl_obj, "window_text", lambda: "")()
            ctrl_name = getattr(ctrl_obj, "element_info", None)
            ctrl_name = ctrl_name.name if ctrl_name else ""
            # Compare attribute values
            if best_attr:
                attr_name, attr_val = re.match(r'@(\w+)="(.*)"', best_attr).groups()
                if (attr_name == "auto_id" and ctrl_auto_id == attr_val) or \
                   (attr_name == "title" and ctrl_title == attr_val) or \
                   (attr_name == "name" and ctrl_name == attr_val):
                    xpath_parts.append(f'/{tag}[{best_attr}]')
                    parent_elem = child_elem
                    matched = True
                    break
        if not matched: # 如果没有找到匹配的属性，最后使用索引
            try:
                parent_ctrl = ctrl_obj.parent()
            except Exception:
                logger.debug("Parent node mismatch, get the root node")
                parent_ctrl = None
            if parent_ctrl:
                siblings = [sib for sib in parent_ctrl.children() if sib.friendly_class_name() == tag]
            else:
                logger.debug("Parent node not found, only exist the root node in this level")
                siblings = [ctrl_obj]
            try:
                index = siblings.index(ctrl_obj)
            except ValueError:
                logging.debug(f"Cannot find <{ctrl_obj}> in its siblings: {siblings}")
                index = 0  # 默认使用第一个索引
            if index + 1 > len(same_type_children):
                raise Exception("XML structure mismatch, index out of range")
            child_elem = same_type_children[index]
            xpath_parts.append(f"/{tag}[{index}]")
            parent_elem = child_elem

    xpath = "".join(xpath_parts)
    return xpath


def is_state_similar(state1: ET.ElementTree, state2: ET.ElementTree) -> bool:
    """判断两个界面结构是否相似（忽略内容差异）"""
    def normalize(elem):
        # 删除会随内容变化的属性
        for attr in ["title", "name", "path", "rect", "handle", "auto_id", "is_dynamic"]:
            if attr in elem.attrib:
                elem.attrib.pop(attr)
        # 对所有子节点递归处理
        for child in list(elem):
            normalize(child)
    import copy # 深拷贝
    e1 = copy.deepcopy(state1.getroot())
    e2 = copy.deepcopy(state2.getroot())
    normalize(e1)
    normalize(e2)
    # 转换为字符串比较
    xml_str1 = ET.tostring(e1)
    xml_str2 = ET.tostring(e2)
    if xml_str1 == xml_str2:
        logging.debug(f"XML structure match")
        return True
    else:
        return False

def collect_interactive_controls(wrapper: UIAWrapper) -> list:
    """收集当前界面中的可交互控件，注意该方法会过滤所有祖先控件为可交互的可交互控件"""
    try:
        controls = wrapper.descendants()
    except Exception:
        controls = wrapper.children()

    all_interactive_controls = []  # 收集当前状态中的可交互控件
    for ctrl in controls:
        ctrl_type = ctrl.friendly_class_name()
        if ctrl_type in classifier.non_interactive_containers:
            continue  # 跳过不可交互的容器控件
        all_interactive_controls.append(ctrl)

    target_interactive_controls = []
    for ctrl in all_interactive_controls:
        parent_ctrl = ctrl.parent()
        skip = False
        while parent_ctrl is not None:
            if parent_ctrl in all_interactive_controls:
                skip = True
                logger.debug(f"Skip interactive control: {ctrl}")
                break
            try:
                parent_ctrl = parent_ctrl.parent()
            except Exception:
                logger.debug("Fail to get parent control, stop checking")
                break
        if not skip:
            target_interactive_controls.append(ctrl)

    return target_interactive_controls


def get_latest_window_handle(before_handles: list):
    """获取最新打开的窗口句柄"""
    time.sleep(0.5)  # 等待新窗口打开
    after_handles = [w.element_info.handle for w in Desktop(backend="uia").windows()]
    new_handles = set(after_handles) - set(before_handles)
    return new_handles.pop() if len(new_handles) == 1 else None

class Explorer:
    def __init__(self, main_handle: int, output_dir: str):
        """使用给定窗口句柄初始化Explorer"""
        self.stack_path = []
        self.main_window_spec = Desktop(backend="uia").window(handle=main_handle)
        self.main_wrapper = self.main_window_spec.wrapper_object()
        self.state_counter = 0
        self.visited_states = {}      # 保存每个状态的结构表示用于比较
        self.transitions = []         # 保存状态跳转记录 (UTG 边集合)，待解析为yaml
        self.output_dir = output_dir
        shutil.rmtree(self.output_dir, ignore_errors=True)  # 清空上次的UTG目录shutil.rmtree("utg", ignore_errors=True)  # 清空上次的UTG目录
        # 解析初始状态
        initial_xml = export_gui_xml_structure(self.main_wrapper, output_dir=self.output_dir, state_num=self.state_counter)
        self.visited_states[self.state_counter] = ET.parse(initial_xml)

    def log_interaction(self, current_state_num: int, target_state_num: int, control_identifier: str, action: str, content: str):
        transition = {
            "Action": action,
            "Content": content,
            "Control_Identifier": control_identifier,
            "State": current_state_num,
            "New_State_Num": target_state_num,
        }
        self.transitions.append(transition)

    def export_utg_yaml(self, transitions: list):
        """将状态跳转记录导出为YAML文件"""
        utg_data = {"transitions": transitions}
        output_utg_yaml = os.path.join(self.output_dir, 'UTG.yaml')  # "utg/UTG.yaml"
        os.makedirs(os.path.dirname(output_utg_yaml), exist_ok=True)
        with open(output_utg_yaml, "w", encoding="utf-8") as f:
            yaml.safe_dump(utg_data, f, allow_unicode=True)

    def try_new_state(self, current_wrapper: UIAWrapper, new_win_handle) -> [int, UIAWrapper, ET.ElementTree]:
        """检查是否产生新状态，新状态则返回新状态值，否则返回-1"""
        if new_win_handle is None:
            logger.debug(f"No new window handle found")

        if new_win_handle is None or new_win_handle == current_wrapper.element_info.handle:
            new_state_wrapper = current_wrapper  # 仍然是当前窗口
        else:
            new_state_wrapper = Application(backend="uia").connect(handle=new_win_handle).window(handle=new_win_handle).wrapper_object()

        self.state_counter += 1
        new_state_id = self.state_counter
        new_xml_path = export_gui_xml_structure(new_state_wrapper, output_dir=self.output_dir, state_num=new_state_id)
        new_state = ET.parse(new_xml_path)
        # 检查新状态是否已存在（或与已有状态结构相似）
        target_state_num = new_state_id  # 默认假定为新状态
        for sid, state in self.visited_states.items():
            if is_state_similar(state, new_state):
                target_state_num = sid
                try:
                    os.remove(new_xml_path)
                except OSError:
                    logger.debug(f"Fail to remove {new_xml_path}")
                    pass
                self.state_counter -= 1  # 回滚状态值
                break

        if target_state_num == new_state_id:  # 如果是全新状态，则保存其结构供后续比较，并加入待探索队列
            self.visited_states[new_state_id] = new_state

        return [target_state_num, new_state_wrapper, new_state]

    def explore(self):
        """对GUI进行DFS遍历"""
        self.stack_path = []
        try:
            self._dfs_explore(0, self.main_wrapper, self.visited_states[0] , 0)
        except Exception as e:
            logger.error(f"Explorer crashed: {e}", exc_info=True)
        finally:
            self.export_utg_yaml(self.transitions)

    def _dfs_explore(self, current_state_num: int, current_wrapper: UIAWrapper, current_xml_tree: ET.ElementTree, depth:int = 0):
        """从状态current_state_num开始深度优先搜索"""
        if depth > 1:
            return

        self.stack_path.append(current_state_num)
        logger.info(f"DFS进入状态 {current_state_num}，当前路径栈: {self.stack_path}，当前深度: {depth}")

        # 获取当前界面中等待探索的可交互控件
        target_interactive_controls = collect_interactive_controls(current_wrapper)

        dynamic_groups_handled = set()
        for ctrl in target_interactive_controls:
            ctrl_type = ctrl.friendly_class_name()
            is_dynamic = classifier.is_dynamic_control(ctrl)

            if is_dynamic:
                siblings = []
                try:
                    parent_ctrl = ctrl.parent()
                except Exception:
                    parent_ctrl = None
                if parent_ctrl:
                    siblings = [sib for sib in parent_ctrl.children() if classifier.is_similar_structure(sib, ctrl)]

                if parent_ctrl:
                    parent_id = parent_ctrl.element_info.handle or parent_ctrl.element_info.automation_id or \
                            id(parent_ctrl)
                    group_key = (current_state_num, parent_id, ctrl_type)
                else:
                    group_key = (current_state_num, None, ctrl_type)
                # 若是动态控件且该组已处理，或超过第3个则跳过
                if group_key in dynamic_groups_handled or siblings.index(ctrl) >= 3:
                    continue
                dynamic_groups_handled.add(group_key)

            if ctrl_type == 'Edit':
                for text in TEST_INPUTS:
                    action = "input"
                    content = text
                    try:
                        logger.info(f"Interact with Edit control {ctrl}")
                        before_handles = [w.element_info.handle for w in Desktop(backend="uia").windows()]
                        ctrl.type_keys('^A{BACKSPACE}' + text, with_spaces=True)
                    except Exception as e:
                        logger.debug(f"Fail to type {text} in {ctrl.element_info.handle}: {e}")
                        continue
                    time.sleep(0.5)
                    prev_state_count = len(self.visited_states)
                    new_win_handle = get_latest_window_handle(before_handles)
                    target_state_num, target_state_wrapper, gui_xml_tree = self.try_new_state(current_wrapper, new_win_handle)

                    if target_state_num != current_state_num:
                        self.log_interaction(current_state_num, target_state_num, get_control_id(ctrl, current_xml_tree),
                                            action, content)

                    if len(self.transitions) > prev_state_count: # 如果产生了新状态
                        self._dfs_explore(target_state_num, target_state_wrapper, gui_xml_tree, depth + 1)

                    if target_state_wrapper.element_info.handle != current_wrapper.element_info.handle:
                        try:
                            target_state_wrapper.close()
                        except Exception as e:
                            logger.debug(f"关闭窗口失败: {e}")
                # 最后清空文本框内容
                ctrl.type_keys("^A{BACKSPACE}")
            else:
                action = "click"
                try:
                    logger.info(f"Interact with Button control {ctrl}")
                    before_handles = [w.element_info.handle for w in Desktop(backend="uia").windows()]
                    ctrl.click_input()
                except Exception as e:
                    logger.debug(f"Fail to click in {ctrl.element_info.handle}: {e}")
                    continue
                time.sleep(0.5)
                prev_state_count = len(self.visited_states)
                new_win_handle = get_latest_window_handle(before_handles)
                target_state_num, target_state_wrapper, gui_xml_tree = self.try_new_state(current_wrapper, new_win_handle)

                if target_state_num != current_state_num:
                    self.log_interaction(current_state_num, target_state_num, get_control_id(ctrl, current_xml_tree),
                                        action, 'null')

                if len(self.transitions) > prev_state_count: # 如果产生了新状态
                    self._dfs_explore(target_state_num, target_state_wrapper, gui_xml_tree, depth + 1)

                if target_state_wrapper.element_info.handle != current_wrapper.element_info.handle:
                    try:
                        target_state_wrapper.close()
                    except Exception as e:
                        logger.debug(f"关闭窗口失败: {e}")

            current_wrapper.restore()

        self.stack_path.pop()
        logger.info(f"回退到状态 {self.stack_path[-1] if self.stack_path else 'None'}，当前路径栈: {self.stack_path}")

