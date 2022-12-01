from json import dumps
import unittest
import winreg
import app


def string_key_count(path, check=0):
    base_key, sub_key = app.get_key_subkey(path)
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        count = winreg.QueryInfoKey(handle)[check]
        handle.Close()
        return count
    except OSError:
        return -1


def get_value_from_key(path):
    base_key, sub_key, value = app.get_key_subkey_param1(path)
    try:
        handle = winreg.OpenKey(base_key, sub_key, access=winreg.KEY_QUERY_VALUE)
        data = winreg.QueryValueEx(handle, value)
        handle.Close()
        return str(data[0])
    except OSError:
        return 'err'


class Test(unittest.TestCase):
    def test_get_key(self):
        key_tuple = app.get_key_subkey('4\\')
        self.assertEqual(key_tuple, (winreg.HKEY_CURRENT_CONFIG, ''))
        key_tuple = app.get_key_subkey('4\\New Key #1\\New Key #2')
        self.assertEqual(key_tuple, (winreg.HKEY_CURRENT_CONFIG, 'New Key #1\\New Key #2'))

    def test_get_key_value(self):
        key_tuple = app.get_key_subkey_param1('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\mod')
        self.assertEqual(key_tuple, (winreg.HKEY_CURRENT_CONFIG, 'New Key #1\\New Key #2\\New Key #1', 'mod'))

    def test_get_key_value_data(self):
        key_tuple = app.get_key_subkey_param1_param2('4\\New Key #1\\New Key #2\\\\param1\\\\New Value '
                                                     '#1\\\\param2\\\\3')
        self.assertEqual(key_tuple, (winreg.HKEY_CURRENT_CONFIG, 'New Key #1\\New Key #2', 'New Value #1', '3'))

    def test_create_key(self):
        initial_count = string_key_count('4\\New Key #1\\New Key #2')
        app.create_key('4\\New Key #1\\New Key #2')
        final_count = string_key_count('4\\New Key #1\\New Key #2')
        self.assertGreater(final_count, initial_count)

    def test_create_value(self):
        initial_count = string_key_count('4\\New Key #1\\New Key #2', check=1)
        app.create_value('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\3')
        app.create_value('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\3')
        app.create_value('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\3')
        final_count = string_key_count('4\\New Key #1\\New Key #2\\New Key #1', check=1)
        self.assertGreater(final_count, initial_count)

    def test_edit_value(self):
        app.edit_value('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\New Value #1\\\\param2\\\\1')
        value = get_value_from_key('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\New Value #1')
        self.assertEqual('1', value)
        app.edit_value('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\New Value #1\\\\param2\\\\0')
        value = get_value_from_key('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\New Value #1')
        self.assertEqual('0', value)

    def test_rename_value(self):
        value = get_value_from_key('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\New Value #5')
        self.assertEqual('0', value)
        app.rename_value('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\New Value #5\\\\param2\\\\mod')
        value = get_value_from_key('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\New Value #5')
        self.assertEqual('err', value)
        value = get_value_from_key('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\mod')
        self.assertEqual('0', value)
        app.rename_value('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\mod\\\\param2\\\\New Value #5')
        value = get_value_from_key('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\New Value #5')
        self.assertEqual('0', value)

    def test_delete_value(self):
        initial_count = string_key_count('4\\New Key #1\\New Key #2', check=1)
        app.delete_value('4\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\New Value #2')
        final_count = string_key_count('4\\New Key #1\\New Key #2\\New Key #1', check=1)
        self.assertGreater(final_count, initial_count)

    def test_delete_key(self):
        initial_count = string_key_count('4\\New Key #1\\New Key #2')
        app.delete_key('4\\New Key #1\\New Key #2\\New Key #2')
        final_count = string_key_count('4\\New Key #1\\New Key #2')
        self.assertLess(final_count, initial_count)

    def test_rename_key(self):
        app.delete_key('4\\abc')
        app.create_key('4\\')
        app.create_value('4\\New Key #13\\\\param1\\\\3')
        app.edit_value('4\\New Key #13\\\\param1\\\\New Value #1\\\\param2\\\\15')
        self.assertEqual(1, 1)
        self.assertEqual(app.rename_key('4\\New Key #13\\\\param1\\\\abc'), dumps('[RENAME_KEY]: Success'))
        val = get_value_from_key('4\\abc\\\\param1\\\\New Value #1')
        self.assertEqual(val, '15')

    def test_search(self):
        rez = app.find_string('4\\\\\\param1\\\\\\\\param2\\\\abc')
        self.assertEqual(dumps('4\\abc\\\\value\\\\'), rez)
        # valoare in cheia data ca parametru
        rez = app.find_string('4\\New Key #12\\New Key #1\\\\param1\\\\\\\\param2\\\\abc')
        self.assertEqual(dumps('4\\New Key #12\\New Key #1\\New Key #2\\\\value\\\\abc'), rez)
        # valoare in alta cheie
        rez = app.find_string('4\\New Key #12\\New Key #1\\New Key #2\\New Key #1\\\\param1\\\\\\\\param2\\\\xyz')
        self.assertEqual(dumps('4\\New Key #7\\\\value\\\\xyz'), rez)
        # valoare in alt registru
        rez = app.find_string('3\\S-1-5-21-299591297-3445868481-2478295680-1001_Classes\\\\param1\\\\\\\\param2\\\\xyz')
        self.assertEqual(dumps('4\\New Key #7\\\\value\\\\xyz'), rez)
        # valoare inexistenta
        rez = app.find_string('3\\S-1-5-21-299591297-3445868481-2478295680-1001_Classes\\\\param1\\\\\\\\param2'
                              '\\\\xyzawetawetwetewatewtwa')
        self.assertEqual(dumps(''), rez)
        # verificat daca ignora valorile din spate
        rez = app.find_string('4\\New Key #12\\New Key #1\\New Key #2\\\\param1\\\\omoratima\\\\param2\\\\abc')
        self.assertEqual(dumps('4\\New Key #12\\New Key #1\\New Key #2\\\\value\\\\valmax'), rez)


if __name__ == '__main__':
    unittest.main()
