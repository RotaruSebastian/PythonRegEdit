from flask import Flask, render_template
from urllib.parse import unquote
from json import dumps
import win32con
import win32api

app = Flask(__name__)

main_keys = {
    0: win32con.HKEY_CLASSES_ROOT,
    1: win32con.HKEY_CURRENT_USER,
    2: win32con.HKEY_LOCAL_MACHINE,
    3: win32con.HKEY_CURRENT_USER,
    4: win32con.HKEY_CURRENT_CONFIG
}

value_types = {
    win32con.REG_BINARY: 'REG_BINARY',
    win32con.REG_DWORD: 'REG_DWORD',
    win32con.REG_DWORD_BIG_ENDIAN: 'REG_DWORD_BIG_ENDIAN',
    win32con.REG_EXPAND_SZ: 'REG_EXPAND_SZ',
    win32con.REG_LINK: 'REG_LINK',
    win32con.REG_MULTI_SZ: 'REG_MULTI_SZ',
    win32con.REG_NONE: 'REG_NONE',
    win32con.REG_QWORD: 'REG_QWORD',
    win32con.REG_RESOURCE_LIST: 'REG_RESOURCE_LIST',
    win32con.REG_FULL_RESOURCE_DESCRIPTOR: 'REG_FULL_RESOURCE_DESCRIPTOR',
    win32con.REG_RESOURCE_REQUIREMENTS_LIST: 'REG_RESOURCE_REQUIREMENTS_LIST',
    win32con.REG_SZ: 'REG_SZ'
}


modifiable_types = [win32con.REG_SZ, win32con.REG_MULTI_SZ, win32con.REG_EXPAND_SZ, win32con.REG_DWORD]


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


def key_count(handle, check=0):
    try:
        return win32api.RegQueryInfoKey(handle)[check]
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
        handle = win32api.RegOpenKeyEx(base_key, sub_key)
        current_keys = []
        sub_key_count = key_count(handle)
        for i in range(sub_key_count):
            current_keys.append(win32api.RegEnumKey(handle, i))
        i = 1
        new_key_name = f'New Key #{str(i)}'
        while new_key_name in current_keys:
            i += 1
            new_key_name = f'New Key #{str(i)}'
        new_key = win32api.RegCreateKey(handle, new_key_name)
        win32api.RegCloseKey(new_key)
        win32api.RegCloseKey(handle)
    except OSError as e:
        return dumps(f'[CREATE_KEY]: {str(e)}')
    return dumps('[CREATE_KEY]: Success')


@app.route('/create_value/<path:param>')
def create_value(param):
    base_key, sub_key, value_type = get_key_value(param)
    try:
        handle = win32api.RegOpenKeyEx(base_key, sub_key, 0, win32con.KEY_QUERY_VALUE | win32con.KEY_SET_VALUE)
        current_values = []
        value_count = key_count(handle, check=1)
        for i in range(value_count):
            current_values.append(win32api.RegEnumValue(handle, i)[0])
        i = 1
        new_value_name = f'New Value #{str(i)}'
        while new_value_name in current_values:
            i += 1
            new_value_name = f'New Value #{str(i)}'
        value_type = int(value_type)
        if 0 <= value_type <= 3:
            value_type = modifiable_types[value_type]
        else:
            value_type = modifiable_types[0]
        if value_type == win32con.REG_MULTI_SZ:
            value_data = ['']
        elif value_type == win32con.REG_DWORD:
            value_data = 0
        else:
            value_data = ''
        win32api.RegSetValueEx(handle, new_value_name, None, value_type, value_data)
        win32api.RegCloseKey(handle)
    except OSError as e:
        return dumps(f'[CREATE_VALUE]: {str(e)}')
    return dumps('[CREATE_VALUE]: Success')


@app.route('/edit_value/<path:param>')
def edit_value(param):
    base_key, sub_key, value_name, value_data = get_key_value_data(param)
    try:
        handle = win32api.RegOpenKeyEx(base_key, sub_key, 0, win32con.KEY_QUERY_VALUE | win32con.KEY_SET_VALUE)
        value_type = win32api.RegQueryValueEx(handle, value_name)[1]
        if value_type == win32con.REG_DWORD:
            value_data = int(value_data)
        elif value_type == win32con.REG_MULTI_SZ:
            value_data = value_data.split('[\\end]')
        win32api.RegSetValueEx(handle, value_name, None, value_type, value_data)
        win32api.RegCloseKey(handle)
    except OSError as e:
        return dumps(f'[EDIT_VALUE]: {str(e)}')
    return dumps('[EDIT_VALUE]: Success')


@app.route('/rename_value/<path:param>')
def rename_value(param):
    base_key, sub_key, old_name, new_name = get_key_value_data(param)
    try:
        handle = win32api.RegOpenKeyEx(base_key, sub_key, 0, win32con.KEY_QUERY_VALUE | win32con.KEY_SET_VALUE)
        val = win32api.RegQueryValueEx(handle, old_name)
        win32api.RegSetValueEx(handle, new_name, None, val[1], val[0])
        win32api.RegDeleteValue(handle, old_name)
        win32api.RegCloseKey(handle)
    except OSError as e:
        return dumps(f'[EDIT_VALUE]: {str(e)}')
    return dumps('[EDIT_VALUE]: Success')


# @app.route('/rename_key/<path:param>')
# def rename_key(param):
#     base_key, sub_key, name = get_key_value(param)
#     try:
#         sub_key = sub_key[0: sub_key.rfind('\\')]
#         handle = win32api.RegOpenKey(win32con.HKEY_CURRENT_CONFIG, sub_key, 0, win32con.KEY_ALL_ACCESS)
#         handle2 = win32api.RegCreateKey(win32con.HKEY_CURRENT_CONFIG, name)
#         win32api.RegCopyTree(handle, None, handle2)
#         win32api.RegCloseKey(handle)
#     except OSError:
#         return -1
#     return 0
#     return dumps('[RENAME_KEY]: Success')


@app.route('/delete_key/<path:param>')
def delete_key(param):
    base_key, sub_key = get_key(param)
    try:
        handle = win32api.RegOpenKeyEx(base_key, sub_key, 0, win32con.KEY_ALL_ACCESS)
        delete_sub_key(handle)
        win32api.RegCloseKey(handle)
        win32api.RegDeleteKey(base_key, sub_key)
    except OSError as e:
        return dumps(f'[DELETE_KEY]: {str(e)}')
    return dumps('[DELETE_KEY]: Success')


def delete_sub_key(handle):
    try:
        count = key_count(handle)
        for i in range(count):
            sub_key = win32api.RegEnumKey(handle, 0)
            sub_handle = win32api.RegOpenKeyEx(handle, sub_key, 0, win32con.KEY_ALL_ACCESS)
            delete_sub_key(sub_handle)
            win32api.RegCloseKey(sub_handle)
            win32api.RegDeleteKey(handle, sub_key)
    except OSError:
        return


@app.route('/delete_value/<path:param>')
def delete_value(param):
    base_key, sub_key, value = get_key_value(param)
    try:
        handle = win32api.RegOpenKeyEx(base_key, sub_key, 0, win32con.KEY_SET_VALUE)
        win32api.RegDeleteValue(handle, value)
        win32api.RegCloseKey(handle)
    except OSError as e:
        return dumps(f'[DELETE_VALUE]: {str(e)}')
    return dumps('[DELETE_VALUE]: Success')


@app.route('/inspect_key/<path:param>')
def inspect_key(param):
    base_key, sub_key = get_key(param)
    result = []
    found_default = False
    try:
        handle = win32api.RegOpenKeyEx(base_key, sub_key)
        length = key_count(handle, check=1)
        for i in range(length):
            value = list(win32api.RegEnumValue(handle, i))
            if value[0] == '':
                found_default = True
                result = [['(default)', value[1], 'REG_SZ']] + result
            else:
                value[2] = value_types[value[2]]
                result.append(list(value))
        win32api.RegCloseKey(handle)
        if not found_default:
            result = [['(default)', '(value not set)', 'REG_SZ']] + result
    except OSError as e:
        return dumps(f'[INSPECT_KEY]: {str(e)}')
    return dumps(result)


@app.route('/expand_key/<path:param>')
def expand_key(param):
    base_key, sub_key = get_key(param)
    result = []
    try:
        handle = win32api.RegOpenKeyEx(base_key, sub_key)
        length = key_count(handle)
        for i in range(length):
            sub_sub_key = win32api.RegEnumKey(handle, i)
            temp_handle = win32api.RegOpenKeyEx(handle, sub_sub_key, sam=win32con.KEY_QUERY_VALUE)
            has_sub_keys = str(win32api.RegQueryInfoKey(temp_handle)[0])
            win32api.RegCloseKey(temp_handle)
            result.append([has_sub_keys, sub_sub_key])
        win32api.RegCloseKey(handle)
    except OSError as e:
        return dumps(f'[EXPAND_KEY]: {str(e)}')
    return dumps(result)


@app.route('/')
def root():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(port=80, debug=True)
