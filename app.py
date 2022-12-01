from flask import Flask, render_template
from urllib.parse import unquote
from json import dumps
from win32con import HKEY_CLASSES_ROOT, HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, HKEY_USERS, HKEY_CURRENT_CONFIG
from win32api import RegCreateKey, RegCloseKey, RegCopyTree, RegDeleteTree
from win32api import error as win32error
import winreg

app = Flask(__name__)

main_keys = {
    0: winreg.HKEY_CLASSES_ROOT,
    1: winreg.HKEY_CURRENT_USER,
    2: winreg.HKEY_LOCAL_MACHINE,
    3: winreg.HKEY_USERS,
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


def win32_handle(handle):
    if handle == winreg.HKEY_CLASSES_ROOT:
        return HKEY_CLASSES_ROOT
    elif handle == winreg.HKEY_CURRENT_USER:
        return HKEY_CURRENT_USER
    elif handle == winreg.HKEY_LOCAL_MACHINE:
        return HKEY_LOCAL_MACHINE
    elif handle == winreg.HKEY_USERS:
        return HKEY_USERS
    elif handle == winreg.HKEY_CURRENT_CONFIG:
        return HKEY_CURRENT_CONFIG


def get_key_subkey(param):
    param = unquote(param)
    base_key = main_keys[int(param[0])]
    sub_key = str(param[2:])
    return base_key, sub_key


def get_key_subkey_param1(param):
    param = unquote(param)
    pos = param.find('\\\\param1\\\\')
    base_key = main_keys[int(param[0])]
    sub_key = str(param[2:pos])
    value = str(param[pos + 10:])
    return base_key, sub_key, value


def get_key_subkey_param1_param2(param):
    param = unquote(param)
    pos1 = param.find('\\\\param1\\\\')
    pos2 = param.find('\\\\param2\\\\')
    base_key = main_keys[int(param[0])]
    sub_key = str(param[2:pos1])
    value = str(param[pos1 + 10: pos2])
    data = str(param[pos2 + 10:])
    return base_key, sub_key, value, data


def get_type_from_string(string):
    for key, value in value_types.items():
        if value == string:
            return key


def value_number(base_key, sub_key, value):
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        length = winreg.QueryInfoKey(handle)[1]
        for i in range(length):
            if value == winreg.EnumValue(handle, i)[0]:
                handle.Close()
                return i + 1
        handle.Close()
    except OSError:
        return 0
    return 0


def key_number(base_key, sub_key):
    if sub_key.__contains__('\\'):
        pos = sub_key.rfind('\\')
        parent = sub_key[0:pos]
        child = sub_key[pos + 1:]
    else:
        parent = ''
        child = sub_key
    try:
        handle = winreg.OpenKey(base_key, parent)
        length = winreg.QueryInfoKey(handle)[0]
        for i in range(length):
            if child == winreg.EnumKey(handle, i):
                handle.Close()
                return i + 1
        handle.Close()
    except OSError:
        return 0
    return 0


@app.route('/create_key/<path:param>')
def create_key(param):
    base_key, sub_key = get_key_subkey(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        current_keys = []
        sub_key_count = winreg.QueryInfoKey(handle)[0]
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
        return dumps(f'[CREATE_KEY]: {str(e)}')
    return dumps('[CREATE_KEY]: Success')


@app.route('/create_value/<path:param>')
def create_value(param):
    base_key, sub_key, value_type = get_key_subkey_param1(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key, access=winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE)
        current_values = []
        value_count = winreg.QueryInfoKey(handle)[1]
        for i in range(value_count):
            current_values.append(winreg.EnumValue(handle, i)[0])
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
        if value_type == winreg.REG_MULTI_SZ:
            value_data = ['']
        elif value_type == winreg.REG_DWORD:
            value_data = 0
        else:
            value_data = ''
        winreg.SetValueEx(handle, new_value_name, None, value_type, value_data)
        handle.Close()
    except OSError as e:
        return dumps(f'[CREATE_VALUE]: {str(e)}')
    return dumps('[CREATE_VALUE]: Success')


@app.route('/edit_value/<path:param>')
def edit_value(param):
    base_key, sub_key, value_name, value_data = get_key_subkey_param1_param2(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key, access=winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE)
        value_type = winreg.QueryValueEx(handle, value_name)[1]
        if value_type == winreg.REG_DWORD:
            value_data = int(value_data)
        elif value_type == winreg.REG_MULTI_SZ:
            value_data = value_data.split('[\\end]')
        winreg.SetValueEx(handle, value_name, None, value_type, value_data)
        handle.Close()
    except OSError as e:
        return dumps(f'[EDIT_VALUE]: {str(e)}')
    return dumps('[EDIT_VALUE]: Success')


@app.route('/rename_value/<path:param>')
def rename_value(param):
    base_key, sub_key, old_name, new_name = get_key_subkey_param1_param2(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key, access=winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE)
        val = winreg.QueryValueEx(handle, old_name)
        winreg.SetValueEx(handle, new_name, None, val[1], val[0])
        winreg.DeleteValue(handle, old_name)
        handle.Close()
    except OSError as e:
        return dumps(f'[EDIT_VALUE]: {str(e)}')
    return dumps('[EDIT_VALUE]: Success')


@app.route('/rename_key/<path:param>')
def rename_key(param):
    base_key, sub_key, name = get_key_subkey_param1(param)
    base_key = win32_handle(base_key)
    base_name = sub_key[0:sub_key.rfind('\\') + 1]
    try:
        handle = RegCreateKey(base_key, base_name + name)
        RegCopyTree(base_key, sub_key, handle)
        RegCloseKey(handle)
        RegDeleteTree(base_key, sub_key)
    except win32error as e:
        return dumps(f'[RENAME_KEY]: {str(e)}')
    return dumps('[RENAME_KEY]: Success')


@app.route('/delete_key/<path:param>')
def delete_key(param):
    base_key, sub_key = get_key_subkey(param)
    base_key = win32_handle(base_key)
    try:
        RegDeleteTree(base_key, sub_key)
    except win32error as e:
        return dumps(f'[DELETE_KEY]: {str(e)}')
    return dumps('[DELETE_KEY]: Success')


@app.route('/delete_value/<path:param>')
def delete_value(param):
    base_key, sub_key, value = get_key_subkey_param1(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key, access=winreg.KEY_SET_VALUE)
        winreg.DeleteValue(handle, value)
        handle.Close()
    except OSError as e:
        return dumps(f'[DELETE_VALUE]: {str(e)}')
    return dumps('[DELETE_VALUE]: Success')


@app.route('/find_string/<path:param>')
def find_string(param):
    base_key, sub_key, value, search_string = get_key_subkey_param1_param2(param)
    base_key_int = int(param[0])
    start_value = value_number(base_key, sub_key, value)
    rez = recursive_search(base_key, sub_key, search_string, start_value=start_value)
    while not rez:
        start_key = key_number(base_key, sub_key)
        if sub_key.__contains__('\\'):
            start_key = key_number(base_key, sub_key)
            sub_key = sub_key[0:sub_key.rfind('\\')]
        elif sub_key:
            sub_key = ''
        elif base_key_int < 4:
            base_key_int += 1
            base_key = main_keys[base_key_int]
            start_key = 0
        else:
            return dumps('')
        rez = recursive_search(base_key, sub_key, search_string, start_key=start_key)
    if sub_key:
        sub_key = str(base_key_int) + '\\' + sub_key
    else:
        sub_key = str(base_key_int)
    if rez:
        return dumps(sub_key + '\\' + rez)
    else:
        return dumps('')


def recursive_search(base_key, sub_key, search_string, start_key=0, start_value=0):
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        length = winreg.QueryInfoKey(handle)
        for i in range(start_value, length[1]):
            value = winreg.EnumValue(handle, i)
            if value[0] == search_string or str(value[1]) == search_string:
                handle.Close()
                return '\\value\\\\' + value[0]
        for i in range(start_key, length[0]):
            key = winreg.EnumKey(handle, i)
            if key == search_string:
                handle.Close()
                return key + '\\\\value\\\\'
            rez = recursive_search(handle, key, search_string)
            if rez:
                handle.Close()
                return key + '\\' + rez
        handle.Close()
        return ''
    except OSError:
        return ''


@app.route('/inspect_key/<path:param>')
def inspect_key(param):
    base_key, sub_key = get_key_subkey(param)
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
        return dumps(f'[INSPECT_KEY]: {str(e)}')
    return dumps(result)


@app.route('/expand_key/<path:param>')
def expand_key(param):
    base_key, sub_key = get_key_subkey(param)
    result = []
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        length = winreg.QueryInfoKey(handle)[0]
        for i in range(length):
            sub_sub_key = winreg.EnumKey(handle, i)
            sub_handle = winreg.OpenKey(handle, sub_sub_key, access=winreg.KEY_QUERY_VALUE)
            has_sub_keys = str(winreg.QueryInfoKey(sub_handle)[0])
            sub_handle.Close()
            result.append([has_sub_keys, sub_sub_key])
        handle.Close()
    except OSError as e:
        return dumps(f'[EXPAND_KEY]: {str(e)}')
    return dumps(result)


@app.route('/')
def root():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(port=80, debug=True)
