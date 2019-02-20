"""Test action.py
"""
import unittest
from action import UnboundAction

class TestAction(unittest.TestCase):

    def test_unbound_action(self):

        def f(str1, str2, str3, str4=None):
            return str1 + str2 + str3 + (str4 if str4 else '')

        action = UnboundAction(f, "abc", "def")
        self.assertEqual(action("ghi"), "abcdefghi")
        
