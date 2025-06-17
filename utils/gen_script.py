import os
import yaml
from difflib import SequenceMatcher
from openai import OpenAI


class UIScriptGenerator:
    """
    自动化任务脚本生成模块:
    输入: 用户的自然语言任务描述
    利用 RAG 知识库 (appdoc.yaml 控件定义, UTG.yaml 状态转移)
    输出: UI 操作步骤脚本（中文自然语言 + 伪代码）
    """
    def __init__(self, appdoc_path: str, utg_path: str):
        # 加载应用控件定义 (appdoc.yaml)
        with open(appdoc_path, 'r', encoding='utf-8') as f:
            self.appdoc = yaml.safe_load(f)
        # 加载状态转换定义 (UTG.yaml)
        with open(utg_path, 'r', encoding='utf-8') as f:
            self.utg = yaml.safe_load(f)
        # 提取控件列表，结构化存储: 名称, XPath, 动态标志, 列表名
        self.controls = []
        if isinstance(self.appdoc, dict) and 'controls' in self.appdoc:
            control_list = self.appdoc['controls']
        elif isinstance(self.appdoc, list):
            control_list = self.appdoc
        else:
            control_list = []
        for ctrl in control_list:
            name = ctrl.get('name') or ctrl.get('id', '')
            xpath = ctrl.get('identifier', '')
            desc = ctrl.get('description', '')
            ctrl_dict = {
                'name': name,
                'xpath': xpath,
                'description': desc,
            }
            if ctrl.get('dynamic', '').lower() == 'true':
                ctrl_dict['dynamic'] = True

            self.controls.append(ctrl_dict)

    def similar(self, a: str, b: str) -> float:
        """计算两个字符串的相似度 (0-1)"""
        return SequenceMatcher(None, a, b).ratio()

    def find_relevant_controls(self, task_desc: str):
        """
        根据任务描述查找相关控件，使用名称匹配和相似度排序。
        返回若干最相关的控件列表。
        """
        scores = []
        for ctrl in self.controls:
            score = self.similar(task_desc, ctrl['name'])
            # 若控件名包含任务描述的关键词，可稍微增加匹配度
            if ctrl['name'] in task_desc:
                score += 0.3
            scores.append((score, ctrl))
        # 按相似度降序排序
        scores.sort(key=lambda x: x[0], reverse=True)
        # 过滤得分较低的控件
        relevant = [ctrl for score, ctrl in scores if score > 0.2]
        if not relevant and scores:
            relevant = [scores[0][1]]  # 至少返回最相关的一个
        return relevant[:5]

    def generate_script(self, task_description: str) -> str:
        """
        根据任务描述生成 UI 操作步骤脚本。
        """
        # 查找相关控件
        relevant_ctrls = self.find_relevant_controls(task_description)
        controls_info = ""
        for ctrl in relevant_ctrls:
            controls_info += f"- 名称: {ctrl['name']}, 描述：{ctrl['description']}, is_dynamic: {ctrl['dynamic'] if ctrl['dynamic'] else 'false'}, XPath: {ctrl['xpath']}\n"

        # 整理 UTG 状态转换信息为文本
        try:
            transitions_info = yaml.dump(self.utg, allow_unicode=True)
        except Exception:
            transitions_info = str(self.utg)

        # 构建 GPT-4 提示
        prompt = f"""应用控件定义 (来源 appdoc.yaml):
{controls_info}
状态转换 (来源 UTG.yaml):
{transitions_info}

用户任务: {task_description}

请根据以上信息，为完成该任务生成 UI 操作步骤脚本。要求：
- 使用中文自然语言描述每一步，可包含伪代码格式，如 "点击 控件名" 或 "在 控件名 输入 '文本'"。
- 对于动态控件，使用 `<列表名>.match('关键词')` 的方式引用。
- 如果有多条路径可达任务目标，请提供多条路径（标明路径1、路径2 等）并推荐优先路径。
- 输出格式可使用 Markdown 或纯文本，重点在可读性和结构化。
"""
        messages = [
            {"role": "system", "content": "你是一个熟练的 UI 自动化脚本生成助手。"},
            {"role": "user", "content": prompt}
        ]
        agent = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        try:
            response = agent.chat.completions.create(
                model="gpt-4.1",
                messages=messages,
                temperature=0
            )
            script = response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"调用 OpenAI 接口失败: {e}")
        return script

# 示例调用
if __name__ == "__main__":
    generator = UIScriptGenerator("../doc/appdoc.yaml", "../doc/utg/UTG.yaml")
    task = "发送消息给文件传输助手"
    print(generator.generate_script(task))
