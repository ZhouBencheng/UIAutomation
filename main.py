from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper

app = Application(backend='uia').connect(path='WeChat.exe')
dlg_spec = app.window(title='微信')
dlg_wrapper = dlg_spec.wrapper_object()
pattern = dlg_wrapper.element_info.get_patterns()
print("Supported Patterns: ", pattern)
def extract_control_info(ctrl: UIAWrapper, depth: int=0, max_depth: int=10):
    if depth > max_depth:
        return
    print(ctrl.element_info)
