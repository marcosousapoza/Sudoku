from random import seed, randint
from sudoku.sudoku.game Sudoku
import sys


def main(filename):
    sudoku = Sudoku(filename)
    print(sudoku)

    sol = sudoku.solve()
    if sol:
        print(sudoku)
    else:
        print("Sudoku is unsolvable")


if __name__ == '__main__':
    # Make sure that argument was passed
    assert len(sys.argv) >= 2, "You need to give a sudoku file!"
    filename = sys.argv[1]

    """Normal Execution
    """
    main(filename)

