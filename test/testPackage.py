#!/usr/bin/python
# vim:tw=0:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:
"""
"""

from __future__ import generators

import sys
import os
import unittest

class TestCase(unittest.TestCase):
    def setUp(self):
        if globals().get('dell_ft_ie_interface'): del(dell_ft_ie_interface)
        for k in sys.modules.keys():
            if k.startswith("dell_ft_ie_interface"):
                del(sys.modules[k])

    def tearDown(self):
        if globals().get('dell_ft_ie_interface'): del(dell_ft_ie_interface)
        for k in sys.modules.keys():
            if k.startswith("dell_ft_ie_interface"):
                del(sys.modules[k])

    def testRawCompareNumericVersions(self):
        import dell_ft_ie_interface.dup as dup
        self.assertEqual(-1, dup.numericOnlyCompareStrategy( "1", "2"))
        self.assertEqual( 0, dup.numericOnlyCompareStrategy( "1", "1"))
        self.assertEqual( 1, dup.numericOnlyCompareStrategy( "2", "1"))

    def testRawCompareTextVersions(self):
        import dell_ft_ie_interface.dup as dup
        self.assertEqual(-1, dup.textCompareStrategy( "1", "2"))
        self.assertEqual( 0, dup.textCompareStrategy( "1", "1"))
        self.assertEqual( 1, dup.textCompareStrategy( "2", "1"))
        self.assertEqual(-1, dup.textCompareStrategy( "a", "b"))
        self.assertEqual( 0, dup.textCompareStrategy( "a", "a"))
        self.assertEqual( 1, dup.textCompareStrategy( "b", "a"))
        self.assertEqual(-1, dup.textCompareStrategy( "522d", "5a2d"))

    def testPkgCompare(self):
        import dell_ft_ie_interface.dup as dup
        p = dup.DUP(
            name = "testpack_different",
            version = "522d",
            displayname = "fake"
            )
        q = dup.DUP(
            name = "testpack_different",
            version = "5a2d",
            displayname = "fake"
            )
        self.assertEqual(-1, p.compareVersion(q))
        self.assertEqual( 0, p.compareVersion(p))
        self.assertEqual( 1, q.compareVersion(p))

        

if __name__ == "__main__":
    import test.TestLib
    sys.exit(not test.TestLib.runTests( [TestCase] ))
