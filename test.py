from urllib.parse import quote
from json import dumps
import unittest
import winreg
import app


def string_key_count(path, check=0):
    """Auxiliary function, gets the path to a registry key and returns its number of sub-keys or values.

    :param path: url containing path to a registry key, must be decoded using `app.get_key_subkey`
    :type path: str
    :param check: if 0, function returns the number of sub-keys, if 1 function returns the number of values
    :type check: int
    :return: number of sub-keys or values
    :rtype: int
    """

    base_key, sub_key = app.get_key_subkey(path)
    try:
        handle = winreg.OpenKey(base_key, sub_key)
        count = winreg.QueryInfoKey(handle)[check]
        handle.Close()
        return count
    except OSError:
        return -1


def get_value_from_key(path):
    """Auxiliary function, gets the path to a registry key and the name of a value, returns the data inside that value.

    :param path: url containing path to a key and the name of a value, must be decoded using `app.get_key_subkey_param1`
    :type path: str
    :return: data from the given value
    :rtype: str
    """

    base_key, sub_key, value = app.get_key_subkey_param1(path)
    try:
        handle = winreg.OpenKey(base_key, sub_key, access=winreg.KEY_QUERY_VALUE)
        data = winreg.QueryValueEx(handle, value)
        handle.Close()
        return str(data[0])
    except OSError:
        return 'err'


class Test(unittest.TestCase):
    """Unit testing class for most of the functions from the app module"""

    def test_get_key(self):
        key_tuple = app.get_key_subkey(quote('4\\'))
        self.assertEqual(key_tuple, (winreg.HKEY_CURRENT_CONFIG, ''))
        key_tuple = app.get_key_subkey(quote('4\\New Key #1\\New Key #2'))
        self.assertEqual(key_tuple, (winreg.HKEY_CURRENT_CONFIG, 'New Key #1\\New Key #2'))

    def test_get_key_value(self):
        key_tuple = app.get_key_subkey_param1(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('mod'))
        self.assertEqual(key_tuple, (winreg.HKEY_CURRENT_CONFIG, 'New Key #1\\New Key #2\\New Key #1', 'mod'))

    def test_get_key_value_data(self):
        key_tuple = app.get_key_subkey_param1_param2(quote('4\\New Key #1\\New Key #2') + '/' + quote('New Value #1')
                                                     + '/' + quote('3'))
        self.assertEqual(key_tuple, (winreg.HKEY_CURRENT_CONFIG, 'New Key #1\\New Key #2', 'New Value #1', '3'))

    def test_create_key(self):
        initial_count = string_key_count(quote('4\\New Key #1\\New Key #2'))
        app.create_key(quote('4\\New Key #1\\New Key #2'))
        final_count = string_key_count(quote('4\\New Key #1\\New Key #2'))
        self.assertGreater(final_count, initial_count)

    def test_create_value(self):
        initial_count = string_key_count(quote('4\\New Key #1\\New Key #2'), check=1)
        app.create_value(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('3'))
        app.create_value(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('3'))
        app.create_value(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('3'))
        final_count = string_key_count(quote('4\\New Key #1\\New Key #2\\New Key #1'), check=1)
        self.assertGreater(final_count, initial_count)

    def test_edit_value(self):
        app.edit_value(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('New Value #1') + '/' + quote('1'))
        value = get_value_from_key(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('New Value #1'))
        self.assertEqual('1', value)
        app.edit_value(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('New Value #1') + '/' + quote('0'))
        value = get_value_from_key(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('New Value #1'))
        self.assertEqual('0', value)

    def test_rename_value(self):
        value = get_value_from_key(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('New Value #5'))
        self.assertEqual('0', value)
        app.rename_value(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('New Value #5') + '/'
                         + quote('mod'))
        value = get_value_from_key(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('New Value #5'))
        self.assertEqual('err', value)
        value = get_value_from_key(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('mod'))
        self.assertEqual('0', value)
        app.rename_value(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('mod') + '/'
                         + quote('New Value #5'))
        value = get_value_from_key(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('New Value #5'))
        self.assertEqual('0', value)

    def test_delete_value(self):
        initial_count = string_key_count(quote('4\\New Key #1\\New Key #2'), check=1)
        app.delete_value(quote('4\\New Key #1\\New Key #2\\New Key #1') + '/' + quote('New Value #2'))
        final_count = string_key_count(quote('4\\New Key #1\\New Key #2\\New Key #1'), check=1)
        self.assertGreater(final_count, initial_count)

    def test_delete_key(self):
        initial_count = string_key_count(quote('4\\New Key #1\\New Key #2'))
        app.delete_key(quote('4\\New Key #1\\New Key #2\\New Key #2'))
        final_count = string_key_count(quote('4\\New Key #1\\New Key #2'))
        self.assertLess(final_count, initial_count)

    def test_rename_key(self):
        app.delete_key(quote('4\\abc'))
        app.create_key(quote('4\\'))
        app.create_value(quote('4\\New Key #13') + '/' + quote('3'))
        app.edit_value(quote('4\\New Key #13') + '/' + quote('New Value #1') + '/' + quote('15'))
        self.assertEqual(1, 1)
        self.assertEqual(app.rename_key(quote('4\\New Key #13') + '/' + quote('abc')), dumps('[RENAME_KEY]: Success'))
        val = get_value_from_key(quote('4\\abc') + '/' + quote('New Value #1'))
        self.assertEqual(val, '15')

    def test_search(self):
        rez = app.find_string(quote('4\\') + '/' + '/' + quote('abc'))
        self.assertEqual(dumps('4\\1,System\\abc\\\\value\\\\'), rez)
        # valoare in cheia data ca parametru
        rez = app.find_string(quote('4\\New Key #12\\New Key #1') + '/' + '/' + quote('abc'))
        self.assertEqual(dumps('4\\New Key #12\\New Key #1\\New Key #2\\\\value\\\\abc'), rez)
        # valoare in alta cheie
        rez = app.find_string(quote('4\\New Key #12\\New Key #1\\New Key #2\\New Key #1') + '//' + quote('xyz'))
        self.assertEqual(dumps('4\\New Key #7\\\\value\\\\xyz'), rez)
        # valoare in alt registru
        rez = app.find_string(quote('3\\S-1-5-21-299591297-3445868481-2478295680-1001_Classes') + '//' + quote('xyz'))
        self.assertEqual(dumps('4\\New Key #7\\\\value\\\\xyz'), rez)
        # valoare inexistenta
        rez = app.find_string(quote('3\\S-1-5-21-299591297-3445868481-2478295680-1001_Classes') + '//'
                              + quote('xyzawetawetwetewatewtwa'))
        self.assertEqual(dumps(''), rez)
        # verificat daca ignora valorile din spate
        rez = app.find_string(quote('4\\New Key #12\\New Key #1\\New Key #2') + '/' + quote('verif') + '/'
                              + quote('abc'))
        self.assertEqual(dumps('4\\New Key #12\\New Key #1\\New Key #2\\\\value\\\\valmax'), rez)


if __name__ == '__main__':
    unittest.main()
