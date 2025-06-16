import os

from utils.connector import weixin_title, get_wrapper_object
from utils import explorer
from utils.logger_config import set_logger
from utils.doc_generator import convert_xml_to_appdoc

if __name__ == '__main__':
    logger = set_logger()
    explorer_flag = True   # explorer开关
    conversion_flag = True # conversion开关

    if explorer_flag or not os.listdir('utg'):
        logger.info('Start exploring...')
        dlg_wrapper = get_wrapper_object(weixin_title)
        handle = dlg_wrapper.element_info.handle
        expl = explorer.Explorer(handle, 'utg')
        expl.explore()

    if conversion_flag or not os.path.exists('doc/appdoc.yaml'):
        logger.info('Start generating documentation...')
        convert_xml_to_appdoc('utg', 'utg/UTG.yaml', 'doc/appdoc.yaml')