import os
import re
import yaml
import xml.etree.ElementTree as ET
from openai import OpenAI
import logging
from pathlib import Path

logger = logging.getLogger()
model = 'gpt-4.1'
interactive_tags = ['Button', 'Edit', 'ListItem', 'ComboBox']

def parse_utg(utg_path) -> dict:
    """
    解析 UTG.yaml，返回 transitions_map: 
    key=(source_state_id, control_xpath)，value=跳转的新状态列表。
    """
    with open(utg_path, 'r', encoding='utf-8') as f:
        utg_data = yaml.safe_load(f)
    transitions = utg_data.get('transitions', [])
    trans_map = {}
    for t in transitions:
        state = t.get('State')
        ctrl = t.get('Control_Identifier')
        new_state = t.get('New_State_Num')
        key = (state, ctrl)
        trans_map.setdefault(key, []).append(new_state)
    return trans_map

def get_page_name_summary(xml_content: str) -> tuple:
    """
    使用 OpenAI API 为给定的页面 XML 生成页面名称和功能摘要（一句话）。
    返回 (page_name, summary)。接口返回 JSON 包含 "page_name" 和 "summary" 字段。
    """
    agent = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""请阅读以下微信界面的XML结构，想一个合适的页面名称，并用一句话描述该界面的功能。
XML:
{xml_content}
请以JSON格式输出，包含 "page_name" 和 "summary" 字段。
示例输出:
{{"page_name": "主页", "summary": "显示聊天列表，用于访问聊天内容"}}"""
    try:
        response = agent.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是微信界面分析助手。"},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content.strip()
        data = yaml.safe_load(answer)  # 使用 safe_load 解析 JSON
        page_name = data.get("page_name", "").strip()
        summary = data.get("summary", "").strip()
        return page_name, summary
    except Exception as e:
        logger.error(f"OpenAI 请求失败: {e}")
        return None, None

def get_control_description(page_name, page_summary, targets_info) -> str:
    """
    使用 OpenAI API 为控件生成功能描述。
    targets_info 为列表，元素为 (targetPageName, targetPageSummary)。
    返回一句话描述控件功能。        
    """
    agent = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # 构造提示信息
    content = f"当前页面为《{page_name}》，功能：{page_summary}。\n"
    content += "该页面存在一个控件，与该控件交互后会进入以下页面：\n"
    for (tname, tsum) in targets_info:
        content += f"页面名称：{tname}，功能：{tsum}\n"
    content += "请推理该控件的功能，并用一句话描述功能。"
    try:
        response = agent.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是微信界面分析助手。"},
                {"role": "user", "content": content}
            ]
        )
        desc = response.choices[0].message.content.strip().strip('"')
        # 取第一句并保证以句号结尾
        desc = desc.split('。')[0]
        if not desc.endswith("。"):
            desc += "。"
        return desc
    except Exception as e:
        logger.error(f"OpenAI 控件描述请求失败: {e}")
        return ""

def build_xpath_map(root: ET.Element) -> tuple[dict, dict]:
    """
    构建元素XPath映射与父元素映射。
    返回 (element_to_xpath, parent_map)：
      - element_to_xpath: 元素 id -> 绝对 XPath 字符串
      - parent_map: 元素 id -> 父元素对象
    XPath 优先使用 [@auto_id]/[@title]/[@name] 定位，否则使用索引。
    """
    element_to_xpath = {}
    parent_map = {}
    def traverse(elem: ET.Element, path: str):
        element_to_xpath[id(elem)] = path
        for child in list(elem):
            parent_map[id(child)] = elem
            siblings = [c for c in list(elem) if c.tag == child.tag]
            index = siblings.index(child)
            if 'auto_id' in child.attrib and child.attrib['auto_id']:
                part = f'/{child.tag}[@auto_id="{child.attrib["auto_id"]}"]'
            elif 'title' in child.attrib and child.attrib['title']:
                part = f'/{child.tag}[@title="{child.attrib["title"]}"]'
            elif 'name' in child.attrib and child.attrib['name']:
                part = f'/{child.tag}[@name="{child.attrib["name"]}"]'
            else:
                part = f'/{child.tag}[{index}]'
            traverse(child, path + part)
    # 根节点
    root_path = f'/{root.tag}'
    traverse(root, root_path)
    return element_to_xpath, parent_map

def parse_xml_file(xml_file) -> (int, ET.Element):
    """
    解析单个 XML 文件，返回状态编号及其根元素。
    如果解析失败，记录错误并返回 None。
    """
    fname = xml_file.name
    match = re.search(r'(\d+)', fname)
    state_id = int(match.group(1)) if match else None
    try:
        tree = ET.parse(xml_file)
    except Exception as e:
        logger.error(f"无法解析XML文件 {fname}: {e}")
        raise Exception("XML解析失败")
    root = tree.getroot()

    return state_id, root

def get_page_info(xml_files: list) -> dict:
    """
    从 XML 文件列表中提取页面信息（名称和摘要）。
    返回字典：{state_id: {"page_name": ..., "summary": ...}}
    """
    page_info = {}
    for xml_file in xml_files:
        fname = xml_file.name
        try:
            state_id, root = parse_xml_file(xml_file)
        except Exception as e:
            continue
        xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')
        page_name, summary = get_page_name_summary(xml_str)
        if not page_name:
            logger.debug(f"Fail to get a page name for state{state_id}, using default.")
            page_name = f"页面{state_id}" if state_id is not None else fname
        if not summary:
            logger.debug(f"Fail to get a summary for state{state_id}, using default.")
            summary = ""
        page_info[state_id] = {"page_name": page_name, "summary": summary}
        logger.info(f"页面 {fname}: 名称='{page_name}', 摘要='{summary}'")
    return page_info

def convert_xml_to_appdoc(xml_dir, utg_path, output_yaml):
    """
    将指定目录下的微信 UI XML 转换为 App Doc 结构，并输出为 YAML 文档。
    """
    # 解析UTG映射
    trans_map = parse_utg(utg_path)
    xml_dir = Path(xml_dir)
    # 扫描所有 XML 文件并按文件名中的数字排序
    xml_files = sorted(
        xml_dir.glob("*.xml"), 
        key=lambda x: int(re.search(r'(\d+)', str(x)).group(1)) if re.search(r'(\d+)', str(x)) else str(x)
    )
    if not xml_files:
        logger.error("未找到任何XML文件。")
        return

    # 第一阶段：为每个页面生成页面名称和摘要
    page_info = get_page_info(xml_files)

    # 第二阶段：构建 AppDoc 结构（页面及控件）
    appdoc = {"pages": []}
    for xml_file in xml_files:
        try:
            state_id, root = parse_xml_file(xml_file)
        except Exception as e:
            continue
        xpath_map, parent_map = build_xpath_map(root)

        # 标记需要跳过的动态控件（同一父节点下第二个及以后的动态控件）
        skip_ids = set()
        for parent in root.iter():
            # 动态控件跳过逻辑
            children = list(parent)
            for tag in ['Button', 'Edit', 'ListItem']:
                dyn_children = [
                    c for c in children 
                    if c.tag == tag and c.attrib.get('is_dynamic', '').lower() == 'true'
                ]
                if len(dyn_children) > 1:
                    for c in dyn_children[1:]:
                        skip_ids.add(id(c))
            # 嵌套可交互控件跳过逻辑
            if parent.tag in interactive_tags:
                ancestor = parent_map.get(id(parent))
                while ancestor is not None:
                    if ancestor.tag in interactive_tags:
                        skip_ids.add(id(parent))
                        break
                    ancestor = parent_map.get(id(ancestor))

        page_entry = {
            "page_name": page_info.get(state_id, {}).get("page_name", f"页面{state_id}"),
            "summary": page_info.get(state_id, {}).get("summary", ""),
            "controls": []
        }
        # 遍历每个控件元素
        for elem in root.iter():
            if id(elem) in skip_ids:
                continue
            tag = elem.tag
            # 只处理指定类型的控件
            if tag not in ['Button', 'Edit', 'ListItem', 'ComboBox']:
                continue
            # 确定控件名：优先使用 'name' 或 'title'，否则用 类名+索引
            ctrl_text = elem.attrib.get('name') or elem.attrib.get('title') or ""
            # 动态控件的模板名称需要概括抽象
            if elem.attrib.get('is_dynamic', '').lower() == 'true':
                agent = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                prompt = f"给你提供一个动态控件实例的name示例，生成一个能够抽象概括这类控件的通用名称：{ctrl_text}"
                response = agent.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是微信界面分析助手。注意：你只能返回一个控件的通用名称"},
                        {"role": "user", "content": prompt}
                    ]
                )
                ctrl_text = response.choices[0].message.content.strip().lower()
            parent = parent_map.get(id(elem))
            index = 0
            if parent is not None:
                same = [c for c in list(parent) if c.tag == tag]
                if elem in same:
                    index = same.index(elem)
            if not ctrl_text:
                ctrl_text = f"{tag}{index}"
            control_name = f"{page_entry['page_name']}-{ctrl_text}"
            # 控件唯一标识符（XPath）
            identifier = xpath_map.get(id(elem), "")
            # 功能描述：根据 UTG 交互结果推理
            description = ""
            if state_id is not None and identifier:
                targets = []
                key = (state_id, identifier)
                new_states = trans_map.get(key, [])
                for ns in new_states:
                    tgt_name = page_info.get(ns, {}).get("page_name", f"页面{ns}")
                    tgt_sum = page_info.get(ns, {}).get("summary", "")
                    targets.append((tgt_name, tgt_sum))
                if targets:
                    description = get_control_description(
                        page_entry['page_name'], page_entry['summary'], targets
                    )
                else:
                    logger.debug(f"没有找到跳转目标，控件 {control_name} 的描述将为空。")
            ctrl_entry = {
                "name": control_name,
                "identifier": identifier,
                "description": description
            }
            page_entry["controls"].append(ctrl_entry)
            logger.debug(f"控件 {control_name}: 路径={identifier}, 描述={description}")
        appdoc["pages"].append(page_entry)

    # 输出为 YAML 文档
    os.makedirs(os.path.dirname(output_yaml), exist_ok=True)
    with open(output_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(appdoc, f, allow_unicode=True, sort_keys=False)
    logger.info(f"已生成 App Doc YAML：{output_yaml}")
