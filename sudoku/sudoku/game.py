from __future__ import annotations
from typing import Callable, List, Tuple, Optional
from itertools import combinations
from sudoku.sudoku.csat import BinCSAT
import random


class Sudoku():
    
    def __init__(self, data:str, file=False) -> None:
        # Read sudoku
        if file:
            self._board:List[List[int]] = Sudoku.readsudoku(data)
        else:
            self._board:List[List[int]] = Sudoku.readsudoku_str(data)
        # Create Binaray SAT problem instance
        self._problem:BinCSAT[int, int] = BinCSAT()
        # Add variables to SAT problem
        for i in range(9):
            for j in range(9):
                unique_name = Sudoku._encode_index(i, j)
                value = self._board[i][j]
                if value == 0:
                    domain = list(range(1, 10))
                else:
                    domain = [value]
                self._problem.add_variable(unique_name, domain=domain)
        # Add constraints to SAT problem
        not_equal = lambda x, y: x != y
        # Add row-constraints
        for i in range(9):
            variables = [Sudoku._encode_index(i, j) for j in range(9)]
            for var1, var2 in combinations(variables, 2):
                self._problem.add_constraint(not_equal, (var1, var2))
        # Add column-constraints
        for i in range(9):
            variables = [Sudoku._encode_index(j, i) for j in range(9)]
            for var1, var2 in combinations(variables, 2):
                self._problem.add_constraint(not_equal, (var1, var2))
        # Add box-constraints
        for i in range(3):
            for j in range(3):
                variables = [Sudoku._encode_index(i*3+u%3, j*3+u//3) for u in range(9)]
                for var1, var2 in combinations(variables, 2):
                    self._problem.add_constraint(not_equal, (var1, var2))

    def __str__(self) -> str:
        output = "╔═══════╦═══════╦═══════╗\n"
        for i in range(9):
            if i==3 or i==6:
                output += "╠═══════╬═══════╬═══════╣\n"
            output += "║ "
            for j in range(9):
                s = '.'
                if j==3 or j==6:
                    output += "║ " 
                if self._board[i][j] > 0:
                    s = str(self._board[i][j])
                output += s + " "
            output += "║\n"
        output += "╚═══════╩═══════╩═══════╝\n"
        return output

    def solve(self) -> bool:
        """Solves the sudoku

        Returns:
            bool: True if sudoku was solved
        """
        
        # Define some heuristics for SAT solver
        def min_remaining(not_assigned:List[int]) -> int | None:
            # min remaining values constraint
            domains = sorted(map(
                lambda x: (x, self._problem.get_domain(x)), 
                not_assigned
            ), key=lambda x: len(x[1]))
            domains = list(filter(
                lambda x: len(x[1]) <= len(domains[0][1]), 
                domains
            ))
            if len(domains) != 0:
                return domains[0][0]
            return None

        def most_constraining(not_assigned:List[int]) -> int | None:
            # most constraining
            constraints = map(
                lambda x: (x, self._problem.get_constraints(
                    lambda t: x in t
                )),
                not_assigned
            )
            constraints = sorted(constraints, key=lambda x: len(x[1]))
            constraints = list(filter(
                lambda x: len(x[1]) >= len(constraints[0][1]), 
                constraints
            ))
            if len(constraints) != 0:
                return constraints[0][0]
            return None

        def heuristic2(not_assigned:List[int], assignd:List[int]) -> Tuple[int, List[int]]:
            # Get variables that are involved in arcs with assigned variables
            considering = []
            max_const = 0

            constraints = self._problem.get_constraints()
            for variable in not_assigned:

                nr_constr = len([
                    c for c in constraints if
                    (variable in c) and
                    (c[0] in assignd or c[1] in assignd)
                ])
                if nr_constr > max_const:
                    considering = [variable]
                    max_const = nr_constr
                elif nr_constr == max_const:
                    considering.append(variable)
            # Get the minimum remaining values variable
            x = min_remaining(considering)
            if x != None:
                return x, None
            # Get the most constraining variable
            x = most_constraining(considering)
            if x != None:
                return x, None
            return considering[0], None

        # Make arc-consistent
        possible = self._problem.make_arc_consistent()
        if not possible:
            return False
        # Solving the problem
        solution = self._problem.find_solution(heuristic=heuristic2)
        if solution == None:
            return False
        # Converting back to sudoku instance
        for unique_name, value in solution:
            x, y = Sudoku._decode_id(unique_name)
            self._board[x][y] = value
        return True

    @staticmethod
    def _encode_index(x:int, y:int) -> int:
        return x*9+y

    @staticmethod
    def _decode_id(name:int) -> Tuple[int, int]:
        return (name//9, name%9)

    @staticmethod
    def readsudoku(filename:str) -> List[int]:
        assert filename != None and filename != "", "Invalid filename"
        try:
            with open(filename, 'r') as file:
                data = file.read()
                grid = Sudoku.readsudoku_str(data)
        except Exception:
            raise AttributeError("error opening file: "+filename)
        return grid

    @staticmethod
    def readsudoku_str(string:str) -> List[int]:
        grid = [[-1 for i in range(9)] for j in range(9)]
        try:
            lines = string.split("\n")
            for i in range(9):
                line = lines[i]
                for j in range(9):
                    num_value = int(line[j])
                    grid[i][j] = num_value
        except:
            raise AttributeError("error reading string")
        return grid
    
    def to_file_string(self) -> str:
        output = ""
        for i in range(len(self._board)):
            for j in range(len(self._board[0])):
                output += self._board[i][j]
        output += "\n"
        return output


class TestSudoku(Sudoku):
      
    def __init__(self, filename: str) -> None:
        super().__init__(filename)

    # Define some heuristics for SAT solver
    def _min_remaining(self, not_assigned:List[int], assignd:List[int]) -> List[int]:
        # min remaining values constraint
        min_val = float('inf')
        min_remaining = {x:0 for x in not_assigned}
        for var in not_assigned:
            l = len(self._problem.get_domain(var))
            min_remaining[var] = l
            min_val = min(min_val, l)
        lst = [x for x, y in min_remaining.items() if y <= min_val]
        return lst

    def _most_finalized_arcs(self, not_assigned:List[int], assignd:List[int]) -> List[int]:
        # Get variables that are involved in arcs with assigned variables
        # convert to set (faster)
        not_assigned_set = set(not_assigned)
        assigned_set = set(assignd)

        max_val = 0
        finalized_arcs = {k:0 for k in not_assigned}
        for x, y in self._problem.get_constraints():
            if x in not_assigned_set and y in assigned_set:
                finalized_arcs[x] += 1
                if finalized_arcs[x] > max_val:
                    max_val = finalized_arcs[x]
            if y in not_assigned_set and x in assigned_set:
                finalized_arcs[y] += 1
                if finalized_arcs[y] > max_val:
                    max_val = finalized_arcs[y]
        return [x[0] for x in finalized_arcs.items() if x[1] >= max_val]

    def _most_constraining(self, not_assigned:List[int], assignd:List[int]) -> List[int]:
        # most constraining
        constraints = {var:0 for var in not_assigned}
        max_val = 0
        for const in self._problem.get_constraints():
            for var in const:
                if var in constraints:
                    constraints[var] += 1
                    max_val = max(max_val, constraints[var])
        constraints_val = [
            x[0] for x in constraints.items()
            if x[1] >= max_val
        ]
        return constraints_val

    def bad_heuristic(self) -> Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]:
        """Selecting variable randomly

        Returns:
            Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]: heuristic
        """
        def f(not_assigned: List[int], assigned: List[int]) -> Tuple[int, None]:
            return random.choice(not_assigned), None
        return f

    def heuristic1(self) -> Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]:
        """Applies measures in the following order:
           - Most finalized arcs
           - Minimum remaining value
           - Most constraining

        Returns:
            Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]: heuristic function
        """
        def f(not_assigned: List[int], assigned: List[int]) -> Tuple[int, None]:
            considering = self._most_finalized_arcs(not_assigned, assigned)
            if len(considering) == 1:
                return considering[0], None
            considering = self._min_remaining(considering, assigned)
            if len(considering) == 1:
                return considering[0], None
            considering = self._most_constraining(considering, assigned)
            return random.choice(considering), None
        return f
    
    def heuristic2(self) -> Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]:
        """Applies measures in the following order:
           - Minimum remaining value
           - Most finalized arcs
           - Most constraining

        Returns:
            Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]: heuristic function
        """
        def f(not_assigned: List[int], assigned: List[int]) -> Tuple[int, None]:
            considering = self._min_remaining(not_assigned, assigned)
            if len(considering) == 1:
                return considering[0], None
            considering = self._most_finalized_arcs(considering, assigned)
            if len(considering) == 1:
                return considering[0], None
            considering = self._most_constraining(considering, assigned)
            return random.choice(considering), None
        return f

    def heuristic3(self) -> Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]:
        """Applies measures in the following order:
           - Minimum remaining value
           - Most constraining
           - Most finalized arcs

        Returns:
            Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]: heuristic function
        """
        def f(not_assigned: List[int], assigned: List[int]) -> Tuple[int, None]:
            considering = self._min_remaining(not_assigned, assigned)
            if len(considering) == 1:
                return considering[0], None
            considering = self._most_constraining(considering, assigned)
            if len(considering) == 1:
                return considering[0], None
            considering = self._most_finalized_arcs(considering, assigned)
            return random.choice(considering), None
        return f

    def heuristic4(self) -> Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]:
        """Applies measures in the following order:
           - Most constraining
           - Most finalized arcs
           - Minimum remaining value

        Returns:
            Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]: heuristic function
        """
        def f(not_assigned: List[int], assigned: List[int]) -> Tuple[int, None]:
            considering = self._most_constraining(not_assigned, assigned)
            if len(considering) == 1:
                return considering[0], None
            considering = self._most_finalized_arcs(considering, assigned)
            if len(considering) == 1:
                return considering[0], None
            considering = self._min_remaining(considering, assigned)
            return random.choice(considering), None
        return f

    def heuristic5(self) -> Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]:
        """Applies measures in the following order:
           - Most constraining
           - Minimum remaining value
           - Most finalized arcs

        Returns:
            Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]: heuristic function
        """
        def f(not_assigned: List[int], assigned: List[int]) -> Tuple[int, None]:
            considering = self._most_constraining(not_assigned, assigned)
            if len(considering) == 1:
                return considering[0], None
            considering = self._min_remaining(considering, assigned)
            if len(considering) == 1:
                return considering[0], None
            considering = self._most_finalized_arcs(considering, assigned)
            return random.choice(considering), None
        return f

    def heuristic6(self) -> Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]:
        """Applies measures in the following order:
           - Most finalized arcs
           - Most constraining
           - Minimum remaining value

        Returns:
            Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]: heuristic function
        """
        def f(not_assigned: List[int], assigned: List[int]) -> Tuple[int, None]:
            considering = self._most_finalized_arcs(not_assigned, assigned)
            if len(considering) == 1:
                return considering[0], None
            considering = self._most_constraining(considering, assigned)
            if len(considering) == 1:
                return considering[0], None
            considering = self._min_remaining(considering, assigned)
            return random.choice(considering), None
        return f

    def nr_comparisons(self) -> int:
        """gets the number of comparisons used in this csat problem

        Returns:
            int: number of comparisons used
        """
        return self._problem.get_statistics()['constraint checks']

    def solve_(self, arc_consistent:bool, 
              heuristic:Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]) -> bool:
        """Solves the sudoku

        Args:
            arc_consistent (bool): True if the problem should be made arc-consistent beforehand
            heuristic (Callable[[List[int], List[int]], Tuple[int, Optional[List[int]]]]): heuristic

        Returns:
            bool: true if solved. False otherwise
        """
        # Make arc-consistent
        if arc_consistent:
            if not self._problem.make_arc_consistent():
                return False
        # Solving the problem
        solution = self._problem.find_solution(heuristic=heuristic)
        for unique_name, value in solution:
            x, y = Sudoku._decode_id(unique_name)
            self._board[x][y] = value
        return True
