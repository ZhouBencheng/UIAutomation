from utils.connector import weixin_title, get_wrapper_object
from utils import explorer
from utils.logger_config import set_logger

if __name__ == '__main__':
    logger = set_logger()
    logger.info('Start exploring...')

    dlg_wrapper = get_wrapper_object(weixin_title)
    handle = dlg_wrapper.element_info.handle
    expl = explorer.Explorer(handle)
    expl.explore()