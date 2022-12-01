from flask import Flask, render_template
from urllib.parse import unquote
# import win32security
# import win32api
import winreg
import json

app = Flask(__name__)

main_keys = {
    0: winreg.HKEY_CLASSES_ROOT,
    1: winreg.HKEY_CURRENT_USER,
    2: winreg.HKEY_LOCAL_MACHINE,
    3: winreg.HKEY_CURRENT_USER,
    4: winreg.HKEY_CURRENT_CONFIG
}

value_types = {
    winreg.REG_BINARY: 'REG_BINARY',
    winreg.REG_DWORD: 'REG_DWORD',
    winreg.REG_DWORD_BIG_ENDIAN: 'REG_DWORD_BIG_ENDIAN',
    winreg.REG_EXPAND_SZ: 'REG_EXPAND_SZ',
    winreg.REG_LINK: 'REG_LINK',
    winreg.REG_MULTI_SZ: 'REG_MULTI_SZ',
    winreg.REG_NONE: 'REG_NONE',
    winreg.REG_QWORD: 'REG_QWORD',
    winreg.REG_RESOURCE_LIST: 'REG_RESOURCE_LIST',
    winreg.REG_FULL_RESOURCE_DESCRIPTOR: 'REG_FULL_RESOURCE_DESCRIPTOR',
    winreg.REG_RESOURCE_REQUIREMENTS_LIST: 'REG_RESOURCE_REQUIREMENTS_LIST',
    winreg.REG_SZ: 'REG_SZ'
}


modifiable_types = [winreg.REG_SZ, winreg.REG_MULTI_SZ, winreg.REG_EXPAND_SZ, winreg.REG_DWORD]


def get_key(param):
    param = unquote(param)
    base_key = main_keys[int(param[0])]
    sub_key = str(param[2:])
    return base_key, sub_key


def get_key_value(param):
    param = unquote(param)
    pos = param.find('\\\\value\\\\')
    base_key = main_keys[int(param[0])]
    sub_key = str(param[2:pos])
    value = str(param[pos + 9:])
    return base_key, sub_key, value


def get_key_value_data(param):
    param = unquote(param)
    pos1 = param.find('\\\\value\\\\')
    pos2 = param.find('\\\\data\\\\')
    base_key = main_keys[int(param[0])]
    sub_key = str(param[2:pos1])
    value = str(param[pos1 + 9: pos2])
    data = str(param[pos2 + 8:])
    return base_key, sub_key, value, data


# def get_default_data(data):
#     if data == winreg.REG_SZ or data == winreg.REG_MULTI_SZ or data == winreg.REG_EXPAND_SZ:
#         return ''
#     elif data == winreg.REG_DWORD:
#         return 0
#     raise OSError


def key_count(handle, check=0):
    try:
        count = winreg.QueryInfoKey(handle)[check]
        return count
    except OSError:
        return -1


def get_type_from_string(string):
    for key, value in value_types.items():
        if value == string:
            return key


@app.route('/create_key/<path:param>')
def create_key(param):
    base_key, sub_key = get_key(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        current_keys = []
        sub_key_count = key_count(handle)
        for i in range(sub_key_count):
            current_keys.append(winreg.EnumKey(handle, i))
        i = 1
        new_key_name = f'New Key #{str(i)}'
        while new_key_name in current_keys:
            i += 1
            new_key_name = f'New Key #{str(i)}'
        new_key = winreg.CreateKey(handle, new_key_name)
        new_key.Close()
        handle.Close()
    except OSError as e:
        return json.dumps(f'[CREATE_KEY]: {str(e)}')
    return json.dumps('[CREATE_KEY]: Success')


@app.route('/create_value/<path:param>')
def create_value(param):
    base_key, sub_key, value = get_key_value(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key, access=winreg.KEY_READ | winreg.KEY_WRITE)
        current_values = []
        value_count = key_count(handle, check=1)
        for i in range(value_count):
            current_values.append(winreg.EnumValue(handle, i)[0])
        i = 1
        new_value_name = f'New Value #{str(i)}'
        while new_value_name in current_values:
            i += 1
            new_value_name = f'New Value #{str(i)}'
        value = int(value)
        if 0 <= value <= 3:
            value = modifiable_types[value]
        else:
            value = modifiable_types[0]
        if value == winreg.REG_MULTI_SZ:
            default = ['']
        elif value == winreg.REG_DWORD:
            default = 0
        else:
            default = ''
        winreg.SetValueEx(handle, new_value_name, None, value, default)
        handle.Close()
    except OSError as e:
        return json.dumps(f'[CREATE_VALUE]: {str(e)}')
    return json.dumps('[CREATE_VALUE]: Success')


@app.route('/edit_value/<path:param>')
def edit_value(param):
    base_key, sub_key, value, data = get_key_value_data(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        handle.Close()
    except OSError as e:
        return json.dumps(f'[EDIT_VALUE]: {str(e)}')
    return json.dumps('[EDIT_VALUE]: Success')


@app.route('/rename_key/<path:param>')
def rename_key(param):
    # copiat manual
    base_key, sub_key, name = get_key_value(param)
    return json.dumps('[RENAME_KEY]: Success')

    # try:
    #     handle = winreg.OpenKey(base_key, sub_key)
    #     try:
    #         os.remove('abc')
    #     except OSError:
    #         print('nimic')
    #     winreg.SaveKey(handle, 'abc')
    #     # try:
    #     #     delete_sub_key(handle)
    #     # except OSError:
    #     #     print('nimic')
    #     handle.Close()
    #     if sub_key.__contains__('\\'):
    #         sub_key = sub_key[0:sub_key.rfind('\\')]
    #     else:
    #         sub_key = ''
    #     handle = winreg.ConnectRegistry(None, base_key)
    #     winreg.LoadKey(handle, name, 'abc')
    #     os.remove('abc')
    # except OSError as e:
    #     return json.dumps(str(e))


@app.route('/delete_key/<path:param>')
def delete_key(param):
    base_key, sub_key = get_key(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        delete_sub_key(handle)
        handle.Close()
    except OSError as e:
        return json.dumps(f'[DELETE_KEY]: {str(e)}')
    return json.dumps('[DELETE_KEY]: Success')


def delete_sub_key(handle):
    while True:
        try:
            sub_key = winreg.EnumKey(handle, 0)
            sub_handle = winreg.OpenKey(handle, sub_key)
            delete_sub_key(sub_handle)
            sub_handle.Close()
        except OSError:
            break
    try:
        winreg.DeleteKey(handle, "")
    except OSError as e:
        return json.dumps([f'DELETE_SUB_KEY]: {str(e)}'])


@app.route('/delete_value/<path:param>')
def delete_value(param):
    base_key, sub_key, value = get_key_value(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key, access=winreg.KEY_WRITE)
        winreg.DeleteValue(handle, value)
        handle.Close()
    except OSError as e:
        return json.dumps(f'[DELETE_VALUE]: {str(e)}')
    return json.dumps('[DELETE_VALUE]: Success')


@app.route('/inspect_key/<path:param>')
def inspect_key(param):
    base_key, sub_key = get_key(param)
    result = []
    found_default = False
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        length = winreg.QueryInfoKey(handle)[1]
        for i in range(length):
            value = list(winreg.EnumValue(handle, i))
            if value[0] == '':
                found_default = True
                result = [['(default)', value[1], 'REG_SZ']] + result
            else:
                value[2] = value_types[value[2]]
                result.append(list(value))
        handle.Close()
        if not found_default:
            result = [['(default)', '(value not set)', 'REG_SZ']] + result
    except OSError as e:
        return json.dumps(f'[INSPECT_KEY]: {str(e)}')
    return json.dumps(result)


@app.route('/expand_key/<path:param>')
def expand_key(param):
    base_key, sub_key = get_key(param)
    result = []
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        length = winreg.QueryInfoKey(handle)[0]
        for i in range(length):
            sub_sub_key = winreg.EnumKey(handle, i)
            temp_handle = winreg.OpenKey(handle, sub_sub_key)
            has_sub_keys = str(winreg.QueryInfoKey(temp_handle)[0])
            temp_handle.Close()
            result.append([has_sub_keys, sub_sub_key])
        handle.Close()
    except OSError as e:
        return json.dumps(f'[EXPAND_KEY]: {str(e)}')
    return json.dumps(result)


@app.route('/')
def root():
    return render_template('index.html')


# def enable_privilege(privilege):
#     token = win32security.OpenProcessToken(win32api.GetCurrentProcess(),
#                                            win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY)
#     win32security.AdjustTokenPrivileges(token, 0, [(win32security.LookupPrivilegeValue(None, privilege),
#                                                     win32security.SE_PRIVILEGE_ENABLED)])
#     win32api.CloseHandle(token)


if __name__ == '__main__':
    # enable_privilege('SeBackupPrivilege')
    # enable_privilege('SeRestorePrivilege')
    app.run(port=80, debug=True)
