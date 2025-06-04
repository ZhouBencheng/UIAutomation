from pywinauto import Application, timings, Desktop

app = Application(backend="win32").connect(title='Calculator')

dlg_spec = app.window(title='Calculator')
dlg_spec.print_control_identifiers(depth=3)
