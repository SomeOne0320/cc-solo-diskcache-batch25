"""Test diskcache.persistent.Deque."""

import collections
import os
import pickle
import shutil
import tempfile
from unittest import mock

import pytest

import diskcache as dc
from diskcache.core import ENOVAL


def rmdir(directory):
    try:
        shutil.rmtree(directory)
    except OSError:
        pass


@pytest.fixture
def deque():
    deque = dc.Deque()
    yield deque
    rmdir(deque.directory)


def test_init():
    directory = tempfile.mkdtemp()
    sequence = list('abcde')
    deque = dc.Deque(sequence, None)

    assert deque == sequence

    rmdir(deque.directory)
    del deque

    rmdir(directory)
    deque = dc.Deque(sequence, directory)

    assert deque.directory == directory
    assert deque == sequence

    other = dc.Deque(directory=directory)

    assert other == deque

    del deque
    del other
    rmdir(directory)


def test_getsetdel(deque):
    sequence = list('abcde')
    assert len(deque) == 0

    for key in sequence:
        deque.append(key)

    assert len(deque) == len(sequence)

    for index in range(len(sequence)):
        assert deque[index] == sequence[index]

    for index in range(len(sequence)):
        deque[index] = index

    for index in range(len(sequence)):
        assert deque[index] == index

    for index in range(len(sequence)):
        if index % 2:
            del deque[-1]
        else:
            del deque[0]

    assert len(deque) == 0


def test_append(deque):
    deque.maxlen = 3
    for item in 'abcde':
        deque.append(item)
    assert deque == 'cde'


def test_appendleft(deque):
    deque.maxlen = 3
    for item in 'abcde':
        deque.appendleft(item)
    assert deque == 'edc'


def test_index_positive(deque):
    cache = mock.MagicMock()
    cache.__len__.return_value = 3
    cache.iterkeys.return_value = ['a', 'b', 'c']
    cache.__getitem__.side_effect = [KeyError, 101, 102]
    with mock.patch.object(deque, '_cache', cache):
        assert deque[0] == 101


def test_index_negative(deque):
    cache = mock.MagicMock()
    cache.__len__.return_value = 3
    cache.iterkeys.return_value = ['c', 'b', 'a']
    cache.__getitem__.side_effect = [KeyError, 101, 100]
    with mock.patch.object(deque, '_cache', cache):
        assert deque[-1] == 101


def test_index_out_of_range(deque):
    cache = mock.MagicMock()
    cache.__len__.return_value = 3
    cache.iterkeys.return_value = ['a', 'b', 'c']
    cache.__getitem__.side_effect = [KeyError] * 3
    with mock.patch.object(deque, '_cache', cache):
        with pytest.raises(IndexError):
            deque[0]


def test_iter_keyerror(deque):
    cache = mock.MagicMock()
    cache.iterkeys.return_value = ['a', 'b', 'c']
    cache.__getitem__.side_effect = [KeyError, 101, 102]
    with mock.patch.object(deque, '_cache', cache):
        assert list(iter(deque)) == [101, 102]


def test_reversed(deque):
    sequence = list('abcde')
    deque += sequence
    assert list(reversed(deque)) == list(reversed(sequence))


def test_reversed_keyerror(deque):
    cache = mock.MagicMock()
    cache.iterkeys.return_value = ['c', 'b', 'a']
    cache.__getitem__.side_effect = [KeyError, 101, 100]
    with mock.patch.object(deque, '_cache', cache):
        assert list(reversed(deque)) == [101, 100]


def test_state(deque):
    sequence = list('abcde')
    deque.extend(sequence)
    assert deque == sequence
    deque.maxlen = 3
    assert list(deque) == sequence[-3:]
    state = pickle.dumps(deque)
    values = pickle.loads(state)
    assert values == sequence[-3:]
    assert values.maxlen == 3


def test_compare(deque):
    assert not (deque == {})
    assert not (deque == [0])
    assert deque != [1]
    deque.append(0)
    assert deque <= [0]
    assert deque <= [1]


def test_indexerror_negative(deque):
    with pytest.raises(IndexError):
        deque[-1]


def test_indexerror(deque):
    with pytest.raises(IndexError):
        deque[0]


def test_repr():
    directory = tempfile.mkdtemp()
    deque = dc.Deque(directory=directory)
    assert repr(deque) == 'Deque(directory=%r)' % directory


def test_copy(deque):
    sequence = list('abcde')
    deque.extend(sequence)
    temp = deque.copy()
    assert deque == sequence
    assert temp == sequence


def test_count(deque):
    deque += 'abbcccddddeeeee'

    for index, value in enumerate('abcde', 1):
        assert deque.count(value) == index


def test_extend(deque):
    sequence = list('abcde')
    deque.extend(sequence)
    assert deque == sequence


def test_extendleft(deque):
    sequence = list('abcde')
    deque.extendleft(sequence)
    assert deque == list(reversed(sequence))


def test_pop(deque):
    sequence = list('abcde')
    deque.extend(sequence)

    while sequence:
        assert deque.pop() == sequence.pop()


def test_pop_indexerror(deque):
    with pytest.raises(IndexError):
        deque.pop()


def test_popleft(deque):
    sequence = list('abcde')
    deque.extend(sequence)

    while sequence:
        value = sequence[0]
        assert deque.popleft() == value
        del sequence[0]


def test_popleft_indexerror(deque):
    with pytest.raises(IndexError):
        deque.popleft()


def test_remove(deque):
    deque.extend('abaca')
    deque.remove('a')
    assert deque == 'baca'
    deque.remove('a')
    assert deque == 'bca'
    deque.remove('a')
    assert deque == 'bc'


def test_remove_valueerror(deque):
    with pytest.raises(ValueError):
        deque.remove(0)


def test_remove_keyerror(deque):
    cache = mock.MagicMock()
    cache.iterkeys.return_value = ['a', 'b', 'c']
    cache.__getitem__.side_effect = [KeyError, 100, 100]
    cache.__delitem__.side_effect = [KeyError, None]
    with mock.patch.object(deque, '_cache', cache):
        deque.remove(100)


def test_reverse(deque):
    deque += 'abcde'
    deque.reverse()
    assert deque == 'edcba'


def test_rotate_typeerror(deque):
    with pytest.raises(TypeError):
        deque.rotate(0.5)


def test_rotate(deque):
    deque.rotate(1)
    deque.rotate(-1)
    deque += 'abcde'
    deque.rotate(3)
    assert deque == 'cdeab'


def test_rotate_negative(deque):
    deque += 'abcde'
    deque.rotate(-2)
    assert deque == 'cdeab'


def test_rotate_indexerror(deque):
    deque += 'abc'

    cache = mock.MagicMock()
    cache.__len__.return_value = 3
    cache.pull.side_effect = [(None, ENOVAL)]

    with mock.patch.object(deque, '_cache', cache):
        deque.rotate(1)


def test_rotate_indexerror_negative(deque):
    deque += 'abc'

    cache = mock.MagicMock()
    cache.__len__.return_value = 3
    cache.pull.side_effect = [(None, ENOVAL)]

    with mock.patch.object(deque, '_cache', cache):
        deque.rotate(-1)


def test_rotate_collections_deque(deque):
    sequence = collections.deque(range(100))
    deque += range(100)

    for steps in (0, 1, -1, 2, -3, 50, -50, 99, 100, -100, 101, 10**12):
        deque.rotate(steps)
        sequence.rotate(steps)
        assert list(deque) == list(sequence)


def test_rotate_after_delete(deque):
    # Deletions leave gaps between the underlying keys.
    sequence = collections.deque(range(20))
    deque += range(20)

    for index in (7, 3, 12, 0, -1, 5):
        del deque[index]
        del sequence[index]

    for steps in (1, -3, 8, 14, 15, -21, 1000):
        deque.rotate(steps)
        sequence.rotate(steps)
        assert list(deque) == list(sequence)


def test_rotate_large_values():
    # Rotate large values in a real directory without reading or writing
    # the corresponding files on disk.
    directory = tempfile.mkdtemp()

    try:
        values = [bytes([num]) * 100_000 for num in range(10)]
        deque = dc.Deque(values, directory)
        sequence = collections.deque(values)

        def value_files():
            files = {}
            for root, _, names in os.walk(directory):
                for name in names:
                    if name.endswith('.val'):
                        path = os.path.join(root, name)
                        stat = os.stat(path)
                        files[path] = (stat.st_size, stat.st_mtime_ns)
            return files

        # Large values are stored in files on disk.
        assert len(value_files()) == len(values)

        for steps in (1, -2, 3, 10, -10, 11, 100, -100, 10**12):
            before = value_files()

            with mock.patch.object(dc.core.Disk, 'fetch') as fetch:
                with mock.patch.object(dc.core.Disk, 'store') as store:
                    with mock.patch.object(dc.core.Disk, 'remove') as remove:
                        deque.rotate(steps)

            assert not fetch.called
            assert not store.called
            assert not remove.called

            sequence.rotate(steps)
            assert list(deque) == list(sequence)
            assert value_files() == before

        # Order persists after closing and reopening the directory.
        deque.cache.close()
        other = dc.Deque(directory=directory)
        assert list(other) == list(sequence)
        other.cache.close()
    finally:
        rmdir(directory)


def test_rotate_single_transaction(deque):
    deque += range(50)
    sequence = collections.deque(range(50))
    sequence.rotate(7)

    transact = dc.Cache.transact
    calls = []

    def counting_transact(self, retry=False):
        calls.append(retry)
        return transact(self, retry)

    with mock.patch.object(dc.Cache, 'transact', counting_transact):
        with mock.patch.object(dc.Cache, 'push') as push:
            with mock.patch.object(dc.Cache, 'pull') as pull:
                deque.rotate(7)

    assert calls == [True]
    assert not push.called
    assert not pull.called
    assert list(deque) == list(sequence)


def test_rotate_fromcache_tag_expire():
    directory = tempfile.mkdtemp()

    try:
        cache = dc.Cache(directory)

        for num in range(6):
            tag = 'tag-%d' % num
            expire = 3600 if num % 2 else None
            cache.push(num, tag=tag, expire=expire)

        # Expire the third item immediately.
        assert cache.touch(500000000000002, expire=-1)

        deque = dc.Deque.fromcache(cache)
        assert list(deque) == [0, 1, 3, 4, 5]

        deque.rotate(2)

        # The expired item does not reappear after rotation.
        assert list(deque) == [4, 5, 0, 1, 3]

        # Tags and expire times follow their values.
        pulled = []

        while True:
            (key, value), expire_time, tag = cache.pull(
                expire_time=True, tag=True
            )
            if key is None:
                break
            pulled.append((value, expire_time, tag))

        assert [value for value, _, _ in pulled] == [4, 5, 0, 1, 3]

        for value, expire_time, tag in pulled:
            assert tag == 'tag-%d' % value
            if value % 2:
                assert expire_time is not None
            else:
                assert expire_time is None

        cache.close()
    finally:
        rmdir(directory)


def test_rotate_fromcache_string_keys():
    # Non-integer keys leave no room for shifting so rotation renumbers all
    # rows in rotated order.
    directory = tempfile.mkdtemp()

    try:
        cache = dc.Cache(directory)

        for letter in 'abcde':
            cache[letter] = letter.upper()

        deque = dc.Deque.fromcache(cache)
        sequence = collections.deque('ABCDE')

        for steps in (1, -2, 3, 7, -7):
            deque.rotate(steps)
            sequence.rotate(steps)
            assert list(deque) == list(sequence)

        cache.close()
    finally:
        rmdir(directory)


def test_rotate_key_boundary(deque):
    # Keys at the bounds leave no room for shifting so rotation renumbers
    # all rows in rotated order.
    deque += range(6)
    sequence = collections.deque(range(6))
    cache = deque.cache

    for base in (1, 999999999999999 - len(deque)):
        with cache.transact(retry=True):
            sql = cache._sql  # pylint: disable=protected-access
            rows = sql('SELECT rowid FROM Cache ORDER BY key').fetchall()

            for index, (rowid,) in enumerate(rows):
                sql(
                    'UPDATE Cache SET key = ? WHERE rowid = ?',
                    (base + index, rowid),
                )

        for steps in (1, 2, -1, -3, 5, 7):
            deque.rotate(steps)
            sequence.rotate(steps)
            assert list(deque) == list(sequence)

        # Keys stay within the push and pull bounds.
        for key in cache.iterkeys():
            assert 0 < key < 999999999999999

    # Appends and pops still work afterwards.
    deque.append(6)
    sequence.append(6)
    deque.appendleft(-1)
    sequence.appendleft(-1)
    assert deque.pop() == sequence.pop()
    assert deque.popleft() == sequence.popleft()
    assert list(deque) == list(sequence)


def test_peek(deque):
    value = b'x' * 100_000
    deque.append(value)
    assert len(deque) == 1
    assert deque.peek() == value
    assert len(deque) == 1
    assert deque.peek() == value
    assert len(deque) == 1
