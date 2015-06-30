from cStringIO import StringIO

from wvtest import *

from bup import hashsplit, _helpers, helpers


def nr_regions(x, max_count=None):
    return list(hashsplit._nonresident_page_regions(''.join(map(chr, x)),
                                                    max_count))

@wvtest
def test_nonresident_page_regions():
    WVPASSEQ(helpers.saved_errors, [])
    WVPASSEQ(nr_regions([]), [])
    WVPASSEQ(nr_regions([1]), [])
    WVPASSEQ(nr_regions([0]), [(0, 1)])
    WVPASSEQ(nr_regions([1, 0]), [(1, 1)])
    WVPASSEQ(nr_regions([0, 0]), [(0, 2)])
    WVPASSEQ(nr_regions([1, 0, 1]), [(1, 1)])
    WVPASSEQ(nr_regions([1, 0, 0]), [(1, 2)])
    WVPASSEQ(nr_regions([0, 1, 0]), [(0, 1), (2, 1)])
    WVPASSEQ(nr_regions([0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0]),
             [(0, 2), (5, 3), (9, 2)])
    WVPASSEQ(nr_regions([2, 42, 3, 101]), [(0, 2)])
    # Test limit
    WVPASSEQ(nr_regions([0, 0, 0], None), [(0, 3)])
    WVPASSEQ(nr_regions([0, 0, 0], 1), [(0, 1), (1, 1), (2, 1)])
    WVPASSEQ(nr_regions([0, 0, 0], 2), [(0, 2), (2, 1)])
    WVPASSEQ(nr_regions([0, 0, 0], 3), [(0, 3)])
    WVPASSEQ(nr_regions([0, 0, 0], 4), [(0, 3)])
    WVPASSEQ(nr_regions([0, 0, 1], None), [(0, 2)])
    WVPASSEQ(nr_regions([0, 0, 1], 1), [(0, 1), (1, 1)])
    WVPASSEQ(nr_regions([0, 0, 1], 2), [(0, 2)])
    WVPASSEQ(nr_regions([0, 0, 1], 3), [(0, 2)])
    WVPASSEQ(nr_regions([1, 0, 0], None), [(1, 2)])
    WVPASSEQ(nr_regions([1, 0, 0], 1), [(1, 1), (2, 1)])
    WVPASSEQ(nr_regions([1, 0, 0], 2), [(1, 2)])
    WVPASSEQ(nr_regions([1, 0, 0], 3), [(1, 2)])
    WVPASSEQ(nr_regions([1, 0, 0, 0, 1], None), [(1, 3)])
    WVPASSEQ(nr_regions([1, 0, 0, 0, 1], 1), [(1, 1), (2, 1), (3, 1)])
    WVPASSEQ(nr_regions([1, 0, 0, 0, 1], 2), [(1, 2), (3, 1)])
    WVPASSEQ(nr_regions([1, 0, 0, 0, 1], 3), [(1, 3)])
    WVPASSEQ(nr_regions([1, 0, 0, 0, 1], 4), [(1, 3)])
    WVPASSEQ(helpers.saved_errors, [])


@wvtest
def test_uncache_ours_upto():
    WVPASSEQ(helpers.saved_errors, [])
    history = []
    def mock_fadvise_pages_done(f, ofs, len):
        history.append((f, ofs, len))

    uncache_upto = hashsplit._uncache_ours_upto
    page_size = os.sysconf("SC_PAGE_SIZE")
    orig_pages_done = hashsplit._fadvise_pages_done
    try:
        hashsplit._fadvise_pages_done = mock_fadvise_pages_done
        history = []
        uncache_upto(42, 0, (0, 1), iter([]))
        WVPASSEQ([], history)
        uncache_upto(42, page_size, (0, 1), iter([]))
        WVPASSEQ([(42, 0, 1)], history)
        history = []
        uncache_upto(42, page_size, (0, 3), iter([(5, 2)]))
        WVPASSEQ([], history)
        uncache_upto(42, 2 * page_size, (0, 3), iter([(5, 2)]))
        WVPASSEQ([], history)
        uncache_upto(42, 3 * page_size, (0, 3), iter([(5, 2)]))
        WVPASSEQ([(42, 0, 3)], history)
        history = []
        uncache_upto(42, 5 * page_size, (0, 3), iter([(5, 2)]))
        WVPASSEQ([(42, 0, 3)], history)
        history = []
        uncache_upto(42, 6 * page_size, (0, 3), iter([(5, 2)]))
        WVPASSEQ([(42, 0, 3)], history)
        history = []
        uncache_upto(42, 7 * page_size, (0, 3), iter([(5, 2)]))
        WVPASSEQ([(42, 0, 3), (42, 5, 2)], history)
    finally:
        hashsplit._fadvise_pages_done = orig_pages_done
    WVPASSEQ(helpers.saved_errors, [])


@wvtest
def test_rolling_sums():
    WVPASSEQ(helpers.saved_errors, [])
    WVPASS(_helpers.selftest())
    WVPASSEQ(helpers.saved_errors, [])

@wvtest
def test_fanout_behaviour():
    WVPASSEQ(helpers.saved_errors, [])

    # Drop in replacement for bupsplit, but splitting if the int value of a
    # byte >= BUP_BLOBBITS
    basebits = _helpers.blobbits()
    def splitbuf(buf):
        ofs = 0
        for c in buf:
            ofs += 1
            if ord(c) >= basebits:
                return ofs, ord(c)
        return 0, 0

    old_splitbuf = _helpers.splitbuf
    _helpers.splitbuf = splitbuf
    old_BLOB_MAX = hashsplit.BLOB_MAX
    hashsplit.BLOB_MAX = 4
    old_BLOB_READ_SIZE = hashsplit.BLOB_READ_SIZE
    hashsplit.BLOB_READ_SIZE = 10
    old_fanout = hashsplit.fanout
    hashsplit.fanout = 2

    levels = lambda f: [(len(b), l) for b, l in
        hashsplit.hashsplit_iter([f], True, None)]
    # Return a string of n null bytes
    z = lambda n: '\x00' * n
    # Return a byte which will be split with a level of n
    sb = lambda n: chr(basebits + n)

    split_never = StringIO(z(16))
    split_first = StringIO(z(1) + sb(3) + z(14))
    split_end   = StringIO(z(13) + sb(1) + z(2))
    split_many  = StringIO(sb(1) + z(3) + sb(2) + z(4) +
                            sb(0) + z(4) + sb(5) + z(1))
    WVPASSEQ(levels(split_never), [(4, 0), (4, 0), (4, 0), (4, 0)])
    WVPASSEQ(levels(split_first), [(2, 3), (4, 0), (4, 0), (4, 0), (2, 0)])
    WVPASSEQ(levels(split_end), [(4, 0), (4, 0), (4, 0), (2, 1), (2, 0)])
    WVPASSEQ(levels(split_many),
        [(1, 1), (4, 2), (4, 0), (1, 0), (4, 0), (1, 5), (1, 0)])

    _helpers.splitbuf = old_splitbuf
    hashsplit.BLOB_MAX = old_BLOB_MAX
    hashsplit.BLOB_READ_SIZE = old_BLOB_READ_SIZE
    hashsplit.fanout = old_fanout
    WVPASSEQ(helpers.saved_errors, [])
