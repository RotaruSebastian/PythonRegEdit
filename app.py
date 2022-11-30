from flask import Flask, render_template
from urllib.parse import unquote
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


@app.route('/create_key/<path:param>')
def create_key(param):
    base_key, sub_key = get_key(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        current_keys = []
        sub_key_count = winreg.QueryInfoKey(handle)[0]
        for i in range(sub_key_count):
            current_keys.append(winreg.EnumKey(handle, i))
        new_key_base_name = 'New Key #'
        i = 1
        while new_key_base_name + str(i) in current_keys:
            i += 1
        new_key = winreg.CreateKey(handle, new_key_base_name + str(i))
        new_key.Close()
        handle.Close()
    except OSError as e:
        return json.dumps(str(e))
    return json.dumps([])


@app.route('/delete_key/<path:param>')
def delete_key(param):
    base_key, sub_key = get_key(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        delete_sub_key(handle)
        handle.Close()
    except OSError as e:
        return json.dumps(str(e))
    return json.dumps([])


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
        return json.dumps(str(e))


@app.route('/delete_value/<path:param>')
def delete_value(param):
    base_key, sub_key, value = get_key_value(param)
    try:
        handle = winreg.OpenKey(base_key, sub_key, access=winreg.KEY_WRITE)
        winreg.DeleteValue(handle, value)
        handle.Close()
    except OSError as e:
        return json.dumps(str(e))
    return json.dumps([])


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
        return json.dumps(str(e))
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
        return json.dumps(str(e))
    return json.dumps(result)


@app.route('/')
def root():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(port=80, debug=True)
