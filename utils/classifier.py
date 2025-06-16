import os
from openai import OpenAI
from pywinauto.controls.uiawrapper import UIAWrapper
import logging

non_interactive_containers = ["Pane", "Dialog", "Window", "Group",
                             "Image", "GroupBox", "Toolbar", "Custom",
                             "Static", "Text", "Thumb"]

_group_semantics_cache = {}
logger = logging.getLogger()

def clear_group_semantics_cache():
    global _group_semantics_cache
    _group_semantics_cache = {}

def is_similar_structure(ctrl1:UIAWrapper, ctrl2:UIAWrapper) -> bool:
    """判断两个控件是否结构类似"""
    return (ctrl1.friendly_class_name() == ctrl2.friendly_class_name() and
            ctrl1.class_name() == ctrl2.class_name())

# 第二次分类，根据控件组的文本信息判断是否进行抽象
def analyze_control_texts(text_list: list) -> bool:
    """
    使用大语言模型对一组控件文本进行语义分析，所谓第二次分类
    如果文本语义代表功能不同，则代表这不是真正意义上的一组动态控件，返回False；如果仅是内容差异则返回True
    :param text_list: 准动态控件的内容列表
    :return: LLM给出判断结果
    """
    if not text_list:
        return False
    logger.debug(f"Analyzing control texts: {text_list}")
    message = [
        {
            "role": "system",
            "content": (
                "You are an expert in GUI control classification for software applications."
                "You will be given a list of visible text labels or content strings, each representing the main information shown on a GUI control"
                "Your tasks are as follows: "
                "1. Dynamic Content Detection: Based solely on the provided texts, infer whether these controls represent 'dynamic content controls'—that is, controls whose main information (such as file names, article titles, links, messages, or data-driven entries) is likely to change frequently depending on user or external data."
                "2. If all the controls in the list represent dynamic content, return True. If any control is clearly static (e.g., fixed function buttons like 'Send', 'Delete', 'Settings'), return False."
                "3. Dynamic content controls' are those whose primary text or data is likely to be different each time the interface loads, such as document titles, chat messages, or feed items."
                "Note: You must return only a boolean value."
            )
        },
        {
            "role": "user",
            "content": f'controls_text_list:{text_list}'
        }
    ]
    model = 'gpt-4.1'
    agent = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        response = agent.chat.completions.create(
            model=model,
            messages=message,
            max_tokens=10,
            temperature=0.3,
        )
        answer = response.choices[0].message.content.strip().lower()
        return answer == 'true'
    except Exception as e:
        logger.error(f"Fail to call {model} from the backend")
        return  False

# 第一次分类，判断控件是否存在一系列结构相同的兄弟控件
def is_dynamic_control(control: UIAWrapper) -> bool:
    try:
        parent_control = control.parent()
    except Exception:
        logger.debug(f'Parent control not found for {control.window_text()}')
        return False # 没有父容器则认为是静态控件

    try: # 获取兄弟节点列表
        siblings = [sib
                    for sib in parent_control.children()
                    if is_similar_structure(sib, control)]
    except Exception:
        siblings = []

    if len(siblings) > 1:
        global _group_semantics_cache
        text_list = list(sib.element_info.name or sib.window_text() for sib in siblings)
        text_tuple = tuple(text_list)
        if text_tuple in _group_semantics_cache:
            logger.debug(f"Hit the group semantics cache.")
            return _group_semantics_cache[text_tuple]

        distinct = analyze_control_texts(text_list) # 二次分类
        _group_semantics_cache[text_tuple] = distinct
        return distinct
    else:
        return False

if __name__ == '__main__':
    text_list = ['文件传输助手 已置顶 [文件] 现代密码学-第6章.pdf 昨天 10:35',
                 '白婧譞 已置顶 我去车棚拿车 09:06',
                 '【十六周】计通2022级 已置顶 常山二十二画生: 芯莘代，鑫征程。长鑫存储2026校园提前批正式启动，邀您见证鑫的理想！\n\n点击链接报名参与宣讲… 09:04消息免打扰 ',
                 '雨课堂 已置顶 作业提交提醒 昨天 22:41消息免打扰 ',
                 '北科大智慧校园 已置顶  04/22消息免打扰 ',
                 '公众号 北京校园: 秋假11天，刚刚他们发布最新校历…… 10:18',
                 '备孕注意事项 李帼瑞: [动画表情]  10:12消息免打扰 ',
                 '现代密码学2025 Roland: 下载课件 10:08消息免打扰 ',
                 '计科224 杜欣露: [小程序] 2025年北京科技大学毕业典礼志愿者 10:01消息免打扰 ',
                 '马杭 可以 09:55']
    analyze_control_texts(text_list)