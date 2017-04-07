import unittest
from time_utils import timestr2ts


class TestTimeUtils(unittest.TestCase):

    def test_timestr2ts(self):
        self.assertEqual(timestr2ts('2017-04-09', 8), 1491667200)
        self.assertEqual(timestr2ts('2017-04-08 13', 8), 1491627600)
        self.assertEqual(timestr2ts('2017-04-07 18:15', 8), 1491560100)
        self.assertEqual(timestr2ts('2017-04-08 01:16:09', 8), 1491585369)
        self.assertEqual(timestr2ts('', 8), -1)
        self.assertEqual(timestr2ts('2017-04-08 01:16:09.000', 8), -1)

if __name__ == '__main__':
    unittest.main()

