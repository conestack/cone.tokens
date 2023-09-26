from cone.sql.testing import SQLLayer
import sys
import unittest


class TokensLayer(SQLLayer):

    def make_app(self):
        plugins = [
            'cone.ugm',
            'cone.sql',
            'cone.tokens'
        ]
        kw = dict()
        kw['cone.plugins'] = '\n'.join(plugins)
        kw['cone.tokens.config_file'] = '/tmp/tokens.json'
        super().make_app(**kw)


tokens_layer = TokensLayer()


def test_suite():
    from cone.tokens.tests import test_api
    from cone.tokens.tests import test_json_api
    from cone.tokens.tests import test_model
    from cone.tokens.tests import test_token

    suite = unittest.TestSuite()

    suite.addTest(unittest.findTestCases(test_api))
    suite.addTest(unittest.findTestCases(test_json_api))
    suite.addTest(unittest.findTestCases(test_model))
    suite.addTest(unittest.findTestCases(test_token))

    return suite


def run_tests():
    from zope.testrunner.runner import Runner

    runner = Runner(found_suites=[test_suite()])
    runner.run()
    sys.exit(int(runner.failed))


if __name__ == '__main__':
    run_tests()
