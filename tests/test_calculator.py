import unittest

from minagent.tools.base import ToolError
from minagent.tools.calculator import safe_calc


class TestCalculator(unittest.TestCase):
    def test_basic_add(self):
        self.assertEqual(safe_calc("1+2"), "1+2 = 3")

    def test_complex_expression(self):
        self.assertEqual(safe_calc("(3+5)*2"), "(3+5)*2 = 16")

    def test_power(self):
        self.assertEqual(safe_calc("2**10"), "2**10 = 1024")

    def test_float_division(self):
        self.assertEqual(safe_calc("7/2"), "7/2 = 3.5")

    def test_integer_float_display(self):
        self.assertEqual(safe_calc("4/2"), "4/2 = 2")

    def test_negative_number(self):
        self.assertEqual(safe_calc("-3 + 5"), "-3 + 5 = 2")

    def test_syntax_error(self):
        with self.assertRaises(ToolError):
            safe_calc("1+")

    def test_division_by_zero(self):
        with self.assertRaises(ToolError):
            safe_calc("1/0")

    def test_reject_import_injection(self):
        with self.assertRaises(ToolError):
            safe_calc("__import__('os').system('ls')")

    def test_reject_name_access(self):
        with self.assertRaises(ToolError):
            safe_calc("os.system('ls')")

    def test_reject_attribute_access(self):
        with self.assertRaises(ToolError):
            safe_calc("().__class__")


if __name__ == "__main__":
    unittest.main()