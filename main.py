import os
from utils.connector import weixin_title, get_wrapper_object
from utils import explorer
from utils.logger_config import set_logger
from utils.doc_generator import convert_xml_to_appdoc
import gradio as gr
from utils.gen_script import UIScriptGenerator

if __name__ == '__main__':
    logger = set_logger()
    explorer_flag = False   # explorer开关
    conversion_flag = False # conversion开关

    if explorer_flag or not os.listdir('doc/utg'):
        logger.info('Start exploring...')
        dlg_wrapper = get_wrapper_object(weixin_title)
        handle = dlg_wrapper.element_info.handle
        expl = explorer.Explorer(handle, 'doc/utg')
        expl.explore()

    if conversion_flag or not os.path.exists('doc/appdoc.yaml'):
        logger.info('Start generating documentation...')
        convert_xml_to_appdoc('doc/utg', 'doc/utg/UTG.yaml', 'doc/appdoc.yaml')

    script_generator = UIScriptGenerator('doc/appdoc.yaml', 'doc/utg/UTG.yaml')

    gr.Interface(fn=script_generator.generate_script,
                 inputs=gr.Textbox(label="Task Description", placeholder="Describe the task you want to automate..."),
                 outputs=gr.Markdown(label="Generated Script"),
                 allow_flagging="never",
                 title="UI Automation Script Generator").launch()