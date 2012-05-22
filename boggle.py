from collections import defaultdict, namedtuple
import random

#--- Trie functions ------------------------------------------------
# TODO: make a class for this

def make_trie():
    return defaultdict(make_trie)

def add_words(trie, words=[]):
    for word in words:
        add_word(trie, word)
    return trie

def add_word(trie, word):
    if word == '':
        trie['!']  # weirdly, trie['!'] = None breaks everything...
    else:
        add_word(trie[word[0]], word[1:])

def print_trie(trie, indent=0):
    for c in sorted(trie.keys()):
        print '%s%s' % ('  ' * indent, c)
        print_trie(trie.get(c), indent + 1)

def get_words(trie, prefix=''):
    if not trie:
        return []
    w = []
    for c in sorted(trie.keys()):
        if c == '!':
            w.append(prefix)
        else:
            w.extend(get_words(trie.get(c), prefix + c))
    return w

def words_in_file(filename, minlen=4):
    with open(filename) as corpus:
        for line in corpus:
            word = line.split('\t')[0].rstrip().lower()
            if len(word) >= minlen:
                yield word

#--- Boggle stuff ------------------------------------------------

Board = namedtuple('Board', ['grid', 'squares', 'successors'])

def print_board(board):
    for row in board.grid:
        print ' '.join(row)

def random_board(n):
    return make_board(n, lambda: random.choice('abcdefghijklmnopqrstuvwxyz'))

def make_board(n, chooser):
    squares = [(i, j) for i in range(n) for j in range(n)]

    successors = {(i, j): set([(i + a, j + b)
                               for a in range(-1, 2) for b in range(-1, 2)
                               if 0 <= i + a < n and 0 <= j + b < n
                               and (a, b) != (0, 0)])
                  for (i, j) in squares}

    return Board(grid=[[chooser() for _ in range(n)] for _ in range(n)],
                 squares=squares,
                 successors=successors)

def letter_dist(words):
    """Construct the frequency distribution of letters in the given words.

    Returns a tuple (letters, dist, total), where
        letters is a list of all letters found in the words, sorted in
            descending order of frequency;
        dist is a dictionary mapping each letter to its occurrence count; and
        total is the total number of letters, i.e. sum(dist.values()).

    """
    dist = defaultdict(lambda: 0)
    for word in words:
        for letter in word:
            dist[letter] += 1
    items = list(dist.items())
    items.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in items], dist, sum([x[1] for x in items])

def choose_by_dist(choices, dist, total):
    i = random.randrange(total)
    s = 0
    for c in choices:
        if i < s + dist[c]:
            r = c
            break
        else:
            s += dist[c]
    return r

def random_board_dist(n, letters, dist, total):
    return make_board(n, lambda: choose_by_dist(letters, dist, total))

boggle_dice = map(list, [
        'aaafrs', 'aaeeee', 'aafirs', 'adennn', 'aeeeem',
        'aeegmu', 'aegmnn', 'afirsy', 'bjkqxz', 'ccenst',
        'ceiilt', 'ceiplt', 'ceipst', 'ddhnot', 'dhhlor',
        'dhlnor', 'dhlnor', 'eiiitt', 'emottt', 'ensssu',
        'fiprsy', 'gorrvw', 'iprrry', 'nootuw', 'ooottu'])

def random_boggle_board(n):
    """Create a random Boggle puzzle using the official dice."""

    # If n > 5 we'll need more than one set of 25 dice.
    dice = list(boggle_dice)
    random.shuffle(dice)
    sets = 1 + (n * n - 1) / 25
    letters = iter([random.choice(die) for die in dice * sets])
    return make_board(n, lambda: next(letters))  # TODO: make this just take the iterator directly

def path_str(path):
    return '-'.join(['%d:%d' % (p[0], p[1]) for p in path])

def path_word(board, path):
    return ''.join([board.grid[i][j] for (i, j) in path])

def find_words(board, trie):
    """Find all paths in the given board which trace out valid words
    according to the given trie.  Returned is a dictionary which maps
    each word found to a list of the paths which generate it."""
    paths = []
    for (i, j) in board.squares:
        paths.extend(find_paths_from(board,
                                     trie.get(board.grid[i][j]),
                                     [(i, j)]))

    word_paths = defaultdict(lambda: [])
    for path in paths:
        word_paths[path_word(board, path)].append(path)

    return word_paths

def find_paths_from(board, trie, path):
    """Find all paths continuing from the given path which trace out
    valid words continuing from the given trie node."""
    if not trie:
        return []
    w = []
    if trie.get('!') is not None:
        w.append(path)
    for (i, j) in board.successors[path[-1]] - set(path):
        c = board.grid[i][j]
        w.extend(find_paths_from(board, trie.get(c), path + [(i, j)])) 
    return w

def print_solution(word_paths):
    words = sorted(word_paths.keys(),
                   cmp=lambda x, y: cmp(len(x), len(y)) or cmp(x, y))

    print '%d words found (max length: %d)' % (len(words),
                                               max(map(len, words))
                                               if len(words) else 0)
    for (j, word) in enumerate(words):
        print '%d: %s (%s)' % (j + 1, word,
                               ', '.join(map(path_str, word_paths[word])))

if __name__ == "__main__":

    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    filename = sys.argv[2] if len(sys.argv) > 2 else 'TWL06.txt'

    print "number of 4+ letter words in %s: %d" % \
        (filename, len(list(words_in_file(filename))))
    trie = make_trie()
    add_words(trie, words_in_file(filename))
    print 'number of words in trie: %d' % len(get_words(trie))

    letters, dist, total = letter_dist(words_in_file(filename))

    def avg_solution_count(board_maker, reps=1000):
        c = 0
        for i in range(reps):
            board = board_maker()
            soln = find_words(board, trie)
            c += len(soln)
        return 1.0 * c / reps

    print "average solution count with even distribution: %f" % \
        avg_solution_count(lambda: random_board(n))
    print "average solution count with weighted distribution: %f" % \
        avg_solution_count(lambda: random_board_dist(n, letters, dist, total))
    print "average solution count with Boggle dice distribution: %f" % \
        avg_solution_count(lambda: random_boggle_board(n))

#    for i in range(1, 1000):
    for i in range(1, 2):
        if i % 100 == 0:
            print i

        board = random_board_dist(n, letters, dist, total)
#        board = random_boggle_board(n)
        soln = find_words(board, trie)

        if True or len(soln) >= 300:
            print '=== puzzle %d =============================================================' % i
            print_board(board)
            print '---------'
            print_solution(soln)

# TODO: add some assert-based tests
#
# t = make_trie()
# add_word(t, 'pasta')
# add_word(t, 'past')
# add_word(t, 'paste')
# add_word(t, 'patch')
# add_word(t, 'paper')
# 
# print_trie(t)
# print 'get_words=%s' % get_words(t)
#
# board = map(list, ['pas',
#                    'apt',
#                    'rea'])

# # not working...
# @trace
# def getwords(trie, prefix=''):
#     for c in sorted(trie.keys()):
#         if c == '!':
#             print 'c == !: yielding %s' % prefix
#             yield prefix
#         else:
#             print 'c == %s' % c
#             getwords(trie.get(c), prefix + c)
# 
# w = getwords(t)
# print list(w)
