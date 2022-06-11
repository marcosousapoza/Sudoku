from typing import Any, Generator, Generic, List, Optional, Set, Tuple, TypeVar, Dict, Callable
from itertools import product
from queue import Queue


D = TypeVar("D")
V = TypeVar("V")

class CSAT(Generic[V, D]):

    def __init__(self) -> None:
        """Initializes Constraint Satisfiability instance
        """
        # Dictionary that stores variables and their domains
        self._vars:Dict[V, List[D]] = {}
        # Dictionary that stores vairables and their corresponding constraint
        self._constr:Dict[Tuple[V, ...], Callable[..., bool]] = {}
        self._constr_lookup:Set[Tuple[V, ...]] = set()
        # Variable that stores all the statistics
        self._stats:Dict[str:Any] = {}

    #SETTERS
    def add_variable(self, var_name:V, domain:List[D]) -> None:
        """Add a variable with its domain to the problem

        Args:
            var_name (V): Name of variable (must be unique). If not
                it will overide old value
            domain (List[D]): domain of the variable 
        """
        assert isinstance(domain, list), "domain has to be a list"
        self._vars[var_name] = domain

    def add_constraint(self, constraint:Callable[..., bool], variables:Tuple[V, ...]) -> None:
        """Adds constraint to the specified variables

        Args:
            constraint (Callable[[Tuple[D, ...]], bool]): Function should return true if and only if
                the values assigned to the variables satisfies the constraint. The argument of the constraint
                should contain the same ordering as the tuple for the variables. The argument for the
                constraint should take the same number of arguments as len(variables).
            variables (Tuple[V, ...]): The names of the variables involved in the constraint. Note that the order matters!
        """
        assert all(map(lambda x: x in self._vars, variables)), "Some variables have not been declared yet."
        #TODO: add check if constraint is correctly specified
        self._constr_lookup.add(variables)
        self._constr[variables] = constraint

    def set_domain(self, variable:V, domain:List[D]):
        """Sets the domain of a variable

        Args:
            variable (V): Variable you want to change the domain of
            domain (List[D]): New domain for the variable
        """
        assert variable in self._vars, "The variable has not been declared yet"
        self._vars[variable] = domain

    #GETTERS
    def get_statistics(self) -> Dict[str, Any]:
        return self._stats

    def get_value(self, variable:V) -> D:
        """Gets the only value the given variable has in its domain.
           if there are more than one value in the domain an error is raised

        Args:
            variable (V): variable of which the value will be returned

        Raises:
            ValueError: If the variable has more than one element in its domain

        Returns:
            D: only value in variables domain
        """
        if not self.is_assigned(variable):
            raise ValueError("The variable has not have a value")
        return self._vars[variable][0]

    def get_constraints(self) -> List[Tuple[V, ...]]:
        """Gets the constraints

        Returns:
            List[Tuple[V, ...]]: List of all constraints
        """
        return self._constr_lookup

    def get_domain(self, variable:V) -> List[D]:
        """Gets the domain of the specified variable

        Args:
            variable (V): variable of which you need the domain

        Returns:
            List[D]: the domain of variable
        """
        return self._vars[variable]

    def get_variables(self) -> List[V]:
        """Returns a list of all variables

        Returns:
            List[V]: list of variables in this SAT problem
        """
        return list(self._vars.keys())

    #FUNCTIONS
    def is_assigned(self, variable:V) -> bool:
        """Checks if variable has only one element in its domain

        Args:
            variable (V): variable you want to check for

        Returns:
            bool: true if variable has only one element in its domain
        """
        return len(self._vars[variable]) == 1

    def in_domain(self, variable:V, value:D) -> bool:
        """checks if value is inside the domain of variable

        Args:
            variable (V): variable
            value (D): value

        Returns:
            bool: true if value is in domain of variable
        """
        return value in self._vars[variable]

    def satisfiable(self, constraint:Tuple[V, ...]) -> bool:
        """Checks if the constraint (specified as a tuple of variables) 
           given the variables and their domains is satisfiable.

        Args:
            constraint (Tuple[V, ...]): constraint

        Raises:
            AttributeError: If the tuple of variables has not been 
                registered as a constraint yet

        Returns:
            bool: true if satisfiable, otherwise false
        """
        if constraint not in self._constr:
            raise AttributeError("The constraint for these variables",
                                 " has not been defined yet.")
        func = self._constr[constraint]
        domains = map(lambda x: self._vars[x], constraint)
        #TODO: Can be optimized with heuristics...
        for combination in product(*domains):
            if func(*combination):
                return True
        return False

    def check_constraint(self, constraint:Tuple[V, ...], values:Tuple[D, ...]) -> bool:
        """Checks if a constraint is satisfiable given some values for the vairbales.

        Args:
            constraint (Tuple[V, ...]): constraint specified as a tuple of variables
            values (Tuple[D, ...]): values for the variables in the constraint (have 
                to be in the domain for each variable inside the constraint)

        Returns:
            bool: true if constraint holds given the values, otherwise false
        """
        assert constraint in self._constr, "The constraint has not been defined"
        assert all(map(lambda x: self.in_domain(*x), zip(constraint, values))), "Some values are not in reach of the domain"
        # update stats
        self._stats['constraint checks'] += 1
        return self._constr[constraint](*values)

    def _reset_stats(self) -> None:
        self._stats['constraint checks'] = 0

    def __repr__(self) -> str:
        r_string = "Variables:\n"
        for var, domain in self._vars.items():
            r_string += "  variable: {}, domain: {}\n".format(var, domain)
        return r_string

    #SOLUTION FINDING
    def _backtracking_search(self, not_assigned:List[V], assigned:Dict[V, D], 
                            heuristic:Callable[[List[V], List[V]], 
                            Tuple[V, Optional[List[D]]]]) -> Generator[List[Tuple[V, D]], None, None]:
        """Recursive function that finds solutions to the SAT problem

        Args:
            not_assigned (List[V]): list of non-assigned variables (have more than one value in the domain)
            values (Dict[V, D]): dictionary of variable value pairs that have been assigned

        Yields:
            List[Tuple[V, D]]: List of variable value pairs that satisfies the SAT problem i.e. every constraint. 
        """
        if len(not_assigned) == 0:
            yield assigned.items()
        else:
            # Get next variable and domain based on huristic
            variable, values = heuristic(not_assigned, assigned.keys())
            not_assigned.remove(variable)
            if values == None:
                values = self.get_domain(variable)

            # Get all constraints
            constraints = [
                c for c in self._constr_lookup 
                if all(map(lambda x: x in assigned or x==variable,c))
            ]

            # Check for every value in domain if constraints hold
            for value in values:
                assigned[variable] = value
                ok = True
                for constraint in constraints:
                    vals = tuple(map(lambda x: assigned[x], constraint))
                    if not self.check_constraint(constraint, vals):
                        ok = False
                        break
                if ok:
                    yield from self._backtracking_search(not_assigned, assigned, heuristic)
            # Since we have not found a solution for this variable...
            del assigned[variable]
            not_assigned.append(variable)

    def find_solution(self, heuristic:Callable[[List[V], List[V]], Tuple[V, Optional[List[D]]]]) -> Optional[List[Tuple[V, D]]]:
        """Finds one solution to the SAT problem

        Args:
            heuristic (Optional[Callable[[Tuple[V, List[D]], Tuple[V, List[D]]], int]], optional): [description]. Defaults to None.

        Returns:
            Optional[List[Tuple[V, D]]]: Returns a list of variable value pairs that satisfies the SAT problem i.e. every constraint
                if it is not satisfiable None will be returned
        """
        # Reset Statistics
        self._reset_stats()
        # Get all the variables relevant for _backtracking_serach
        assigned:Dict[V, D] = {}
        not_assigned:List[V] = []
        for variable in self._vars.keys():
            if self.is_assigned(variable):
                assigned[variable] = self.get_value(variable)
            else:
                not_assigned.append(variable)
        # Find one solutions
        result = next(
            self._backtracking_search(
                not_assigned, 
                assigned,
                heuristic=heuristic
            ), None # default value
        )
        return result

    def find_all_solutions(self, heuristic:Callable[[List[V]], Tuple[V, Optional[List[D]]]]=None) -> List[List[Tuple[V, D]]]:
        """Finds all solutions to this SAT problem

        Args:
            ord (Optional[Callable[[Tuple[V, List[D]], Tuple[V, List[D]]], int]], optional): [description]. Defaults to None.

        Returns:
            List[List[Tuple[V, D]]]: A list of containing solutions to this SAT problem where each solution is represented as
                a list of variable value pairs that satisfies the SAT problem
        """
        # Reset Statistics
        self._reset_stats()
        # Get all the variables relevant for _backtracking_serach
        assigned:Dict[V, D] = {}
        not_assigned:List[V] = []
        for variable in self._vars.keys():
            if self.is_assigned(variable):
                assigned[variable] = self.get_value(variable)
            else:
                not_assigned.append(variable)
        # Find one solutions
        results = list(
            self._backtracking_search(
                not_assigned, 
                assigned,
                heuristic
            )
        )
        return results


class BinCSAT(CSAT[V, D], Generic[V, D]):

    def __init__(self) -> None:
        """Initializes binary SAT problem
        """
        super().__init__()

    def add_constraint(self, constraint:Callable[[Tuple[D, D]], bool], variables:Tuple[V, V]) -> None:
        """Adds constraint to the specified variables

        Args:
            constraint (Callable[[Tuple[D, D]], bool]): Function should return true if and only if
                the values assigned to the variables satisfies the constraint. The argument of the constraint
                should contain the same ordering as the tuple for the variables. The argument for the
                constraint should take the same number of arguments as len(variables).
            variables (Tuple[V, V]): The names of the variables involved in the constraint. Note that the order matters!
        """
        return super().add_constraint(constraint, variables)

    def satisfiable(self, variables:Tuple[V, V]) -> bool:
        """Checks if the constraint (specified as a tuple of variables) 
           given the variables and their domains is satisfiable.

        Args:
            variables (Tuple[V, V]): constraint

        Raises:
            AttributeError: If the tuple of variables has not been 
                registered as a constraint yet

        Returns:
            bool: true if satisfiable, otherwise false
        """
        return super().satisfiable(variables)

    def get_constraints(self) -> List[Tuple[V, V]]:
        """Gets the constraints

        Returns:
            List[Tuple[V, V]]: List of all constraints
        """
        return super().get_constraints()

    def make_arc_consistent(self) -> bool:
        """Makes the binary SAT problem arc consistent using the AC3 algorithm.

        Returns:
            bool: True if the problem is arc-consistent. False if the problem is not solable
                  given the constraints.
        """
        return self._ac3()

    def arcs(self, constraint:Tuple[V, V]) -> List[Tuple[V, V]]:
        """Creates the arcs for the constraint.

        Args:
            constraint (Tuple[V, V]): constraint

        Returns:
            List[Tuple[V, V]]: the two arcs
        """
        assert constraint in self._constr, "There is no constraint matching the variables"
        return [(constraint[0], constraint[1]), (constraint[1], constraint[0])]

    def _ac3(self) -> bool:
        """Applies the AC3 algorithm

        Returns:
            bool: True if every domain of every variable involved in a constraint has a
                  cardinality that is larger than 0.
        """
        # Setup Queue
        worklist:Queue[Tuple[V, V]] = Queue()
        # Variables that are used often
        constraints = self.get_constraints()
        search = lambda z: x in z and not y in z
        # Add all arcs to the queue:
        for const in self.get_constraints():
            for arc in self.arcs(const):
                worklist.put(arc)
        # Run AC3:
        while not worklist.empty():
            x, y = worklist.get()
            if self._reduce(x, y):
                # Check if domain is empty:
                if len(self._vars[x]) == 0:
                    return False
                else:
                    for u, v in filter(search, constraints):
                        worklist.put((u, v))
        return True

    def _reduce(self, x:V, y:V) -> bool:
        """As specified in the AC3 algorithm

        Args:
            x (V): Variable
            y (V): Variable

        Returns:
            bool: True if domain of x changed.
        """
        change = False
        # Find the constraints where x and y are involved
        for u, v in self._constr.keys():
            if (u == x and v == y):
                break
            elif (u == y and v == x):
                x, y = y, x
                break
        # Reduce the arc
        if self.is_assigned(x): # Reduction is forced if arc is not satisfied
            vx = self.get_value(x)
            for vy in self.get_domain(y):
                if not self._constr[(x, y)](vx, vy):
                    self._vars[y].remove(vy)
                    change = True
        else:
            for vx in self.get_domain(x):
                # Find a value for y for which constraint holds
                value_found = False
                for vy in self.get_domain(y):
                    if self._constr[(x, y)](vx, vy):
                        value_found = True
                # If there is no such value remove vx from dom(x)
                if not value_found:
                    self._vars[x].remove(vx)
                    change = True
        return change

    def __repr__(self) -> str:
        return super().__repr__()