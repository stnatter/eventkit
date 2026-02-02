import unittest

from eventkit import Event

array = list(range(10))


class SelectTest(unittest.TestCase):
    def test_select(self):
        event = Event.sequence(array).filter(lambda x: x % 2)
        self.assertEqual(event.run(), [x for x in array if x % 2])

    def test_skip(self):
        event = Event.sequence(array).skip(5)
        self.assertEqual(event.run(), array[5:])

    def test_take(self):
        event = Event.sequence(array).take(5)
        self.assertEqual(event.run(), array[:5])

    def test_takewhile(self):
        event = Event.sequence(array).takewhile(lambda x: x < 5)
        self.assertEqual(event.run(), array[:5])

    def test_dropwhile(self):
        event = Event.sequence(array).dropwhile(lambda x: x < 5)
        self.assertEqual(event.run(), array[5:])

    def test_changes(self):
        array = [1, 1, 2, 1, 2, 2, 2, 3, 1, 4, 4]
        event = Event.sequence(array).changes()
        self.assertEqual(event.run(), [1, 2, 1, 2, 3, 1, 4])

    def test_changes_by(self):
        # Test with key function extracting odd/even
        array = [1, 3, 2, 4, 5, 6, 7]
        event = Event.sequence(array).changes_by(lambda x: x % 2)
        # 1 (odd), 3 (odd, skip), 2 (even), 4 (even, skip), 5 (odd), 6 (even), 7 (odd)
        self.assertEqual(event.run(), [1, 2, 5, 6, 7])

    def test_changes_by_tuple_key(self):
        # Test with tuple key (simulates bid/ask change detection)
        array = [
            {"bid": 100, "ask": 101, "ts": 1},
            {"bid": 100, "ask": 101, "ts": 2},  # same bid/ask, skip
            {"bid": 100, "ask": 102, "ts": 3},  # ask changed
            {"bid": 101, "ask": 102, "ts": 4},  # bid changed
            {"bid": 101, "ask": 102, "ts": 5},  # same, skip
        ]
        event = Event.sequence(array).changes_by(lambda x: (x["bid"], x["ask"]))
        result = event.run()
        self.assertEqual(len(result), 3)
        self.assertEqual([r["ts"] for r in result], [1, 3, 4])

    def test_changes_by_none_key(self):
        # With None key, should behave like changes()
        array = [1, 1, 2, 1, 2, 2, 2, 3, 1, 4, 4]
        event = Event.sequence(array).changes_by(None)
        self.assertEqual(event.run(), [1, 2, 1, 2, 3, 1, 4])

    def test_unique(self):
        array = [1, 1, 2, 1, 2, 2, 2, 3, 1, 4, 4]
        event = Event.sequence(array).unique()
        self.assertEqual(event.run(), [1, 2, 3, 4])

    def test_last(self):
        event = Event.sequence(array).last()
        self.assertEqual(event.run(), [9])
