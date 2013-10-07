from mock import patch


class MockTestCase(object):

    def patch(self, *args, **kwargs):
        patcher = patch(*args, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()
