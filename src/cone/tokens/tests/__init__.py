import sys
import unittest


def test_suite():
    from cone.tokens.tests import test_api
    from cone.tokens.tests import test_model

    suite = unittest.TestSuite()

    suite.addTest(unittest.findTestCases(test_api))
    suite.addTest(unittest.findTestCases(test_model))

    return suite


def run_tests():
    from zope.testrunner.runner import Runner

    runner = Runner(found_suites=[test_suite()])
    runner.run()
    sys.exit(int(runner.failed))


if __name__ == '__main__':
    run_tests()
