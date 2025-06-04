from pywinauto import Application

app = Application(backend='uia').connect(path='WeChat.exe')
dlg_spec = app.window(title='微信')
dlg_spec.print_control_identifiers()