import unittest
import winreg
import app


def string_key_count(path, check=0):
    base_key, sub_key = app.get_key(path)
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        count = winreg.QueryInfoKey(handle)[check]
        handle.Close()
        return count
    except OSError:
        return -1


def get_value_from_key(path):
    base_key, sub_key, value = app.get_key_value(path)
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        data = winreg.QueryValueEx(handle, value)
        handle.Close()
        return str(data[0])
    except OSError:
        return -1


class Test(unittest.TestCase):
    def test_get_key(self):
        key_tuple = app.get_key('4\\')
        self.assertEqual(key_tuple, (winreg.HKEY_CURRENT_CONFIG, ''))
        key_tuple = app.get_key('4\\New Key #1\\New Key #2')
        self.assertEqual(key_tuple, (winreg.HKEY_CURRENT_CONFIG, 'New Key #1\\New Key #2'))

    def test_get_key_value(self):
        key_tuple = app.get_key_value('4\\New Key #1\\New Key #2\\\\value\\\\0')
        self.assertEqual(key_tuple, (winreg.HKEY_CURRENT_CONFIG, 'New Key #1\\New Key #2', '0'))

    def test_get_key_value_data(self):
        key_tuple = app.get_key_value_data('4\\New Key #1\\New Key #2\\\\value\\\\New Value #1\\\\data\\\\3')
        self.assertEqual(key_tuple, (winreg.HKEY_CURRENT_CONFIG, 'New Key #1\\New Key #2', 'New Value #1', '3'))

    def test_create_key(self):
        initial_count = string_key_count('4\\New Key #1\\New Key #2')
        app.create_key('4\\New Key #1\\New Key #2')
        final_count = string_key_count('4\\New Key #1\\New Key #2')
        self.assertGreater(final_count, initial_count)

    def test_create_value(self):
        initial_count = string_key_count('4\\New Key #1\\New Key #2', check=1)
        app.create_value('4\\New Key #1\\New Key #2\\New Key #1\\\\value\\\\3')
        final_count = string_key_count('4\\New Key #1\\New Key #2\\New Key #1', check=1)
        self.assertGreater(final_count, initial_count)

    def test_edit_value(self):
        app.edit_value('4\\New Key #1\\New Key #2\\New Key #1\\\\value\\\\New Value #1\\\\data\\\\1')
        value = get_value_from_key('4\\New Key #1\\New Key #2\\New Key #1\\\\value\\\\New Value #1')
        self.assertEqual('1', value)
        app.edit_value('4\\New Key #1\\New Key #2\\New Key #1\\\\value\\\\New Value #1\\\\data\\\\0')
        value = get_value_from_key('4\\New Key #1\\New Key #2\\New Key #1\\\\value\\\\New Value #1')
        self.assertEqual('0', value)

    def test_delete_value(self):
        initial_count = string_key_count('4\\New Key #1\\New Key #2', check=1)
        app.delete_value('4\\New Key #1\\New Key #2\\New Key #1\\\\value\\\\New Value #2')
        final_count = string_key_count('4\\New Key #1\\New Key #2\\New Key #1', check=1)
        self.assertGreater(final_count, initial_count)

    def test_delete_key(self):
        initial_count = string_key_count('4\\New Key #1\\New Key #2')
        app.delete_key('4\\New Key #1\\New Key #2\\New Key #2')
        final_count = string_key_count('4\\New Key #1\\New Key #2')
        self.assertLess(final_count, initial_count)


if __name__ == '__main__':
    unittest.main()
