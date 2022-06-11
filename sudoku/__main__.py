from sudoku.sudoku.game import Sudoku
from sudoku.examples.examples import get_random_sudoku
import sys
from argparse import ArgumentParser


def main(data:str, file:bool):
    sudoku = Sudoku(data, file)
    print(sudoku)

    sol = sudoku.solve()
    if sol:
        print(sudoku)
    else:
        print("Sudoku is unsolvable")


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--file', dest='filename', default='')
    parser.add_argument('--random',  action='store_true')
    arg = parser.parse_args()
    """Normal Execution
    """
    if not arg.random:
        main(arg.filename, True)
    else:
        main(get_random_sudoku(), False)

