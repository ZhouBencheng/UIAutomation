import logging
import openai
import os

from openai import OpenAI
from pywinauto.controls.uiawrapper import UIAWrapper

static_containers = ["Pane", "Dialog", "Window", "Group",
                     "Image", "GroupBox", "Toolbar", "Custom",
                     "Static", "Text", "Thumb"]

_group_semantics_cache = {}

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
    message = [
        {
            "role": "system",
            "content": (
                "You are an expert in GUI control classification for software applications."
                "You will be given a list of visible text labels or content strings, each representing the main information shown on a GUI control"
                "Your task is to infer—based only on these texts—whether these controls are intended to perform the same kind of core function within the context of their interface."
                "If the controls serve clearly different core functions, return False."
                "If the controls serve the same kind of core function, or if it is impossible to determine any functional distinction based only on their text, return True."
                "Note: You must return only a boolean value."
            )
        },
        {
            "role": "user",
            "content": f'controls_text_list:{text_list}'
        }
    ]
    model = 'gpt-4.1'
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        response = client.chat.completions.create(
            model=model,
            messages=message,
            max_tokens=10,
            temperature=0.3,
        )
        answer = response.choices[0].message.content.strip().lower()
        return answer == 'true'
    except Exception as e:
        logging.error(f"Fail to call {model} from the backend")
        return  False

# 第一次分类，判断控件是否存在一系列结构相同的兄弟控件
def is_dynamic_control(control: UIAWrapper) -> bool:
    try:
        parent_control = control.parent()
    except Exception:
        logging.debug(f'Parent control not found for {control.window_text()}')
        return False # 没有父容器则认为是静态控件

    try: # 获取兄弟节点列表
        siblings = [sib
                    for sib in parent_control.children()
                    if is_similar_structure(sib, control)]
    except Exception:
        siblings = []

    if len(siblings) > 1:
        parent_id = parent_control.element_info.handle or parent_control.element_info.automation_id or id(parent_control)
        group_key = (parent_id, control.friendly_class_name(), control.class_name(), len(siblings))
        if group_key in _group_semantics_cache:
            return _group_semantics_cache[group_key]
        text_list = list(sib.element_info.name or sib.window_text() for sib in siblings)
        # 二次分类
        distinct = analyze_control_texts(text_list)

        _group_semantics_cache[group_key] = distinct
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