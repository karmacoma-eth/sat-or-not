import random

from typing import Optional

type Literal = int
type Clause = tuple[Literal]
type Formula = list[Clause]
type Assignment = list[bool | None]

# Map from variable index to variable name
variable_names = {i: chr(96 + i) for i in range(1, 27)}  # Original variable names, a-z

# Negated variable names
variable_names.update(
    {-i: f"!{chr(96 + i)}" for i in range(1, 27)}
)


def cardinality(formula: Formula) -> int:
    """
    Returns the number of variables in a formula.

    Parameters:
    - formula: A list of clauses, where each clause is a tuple of literals.

    Note:
    - variables are be 1-indexed, and negative integers represent negated variables
    - there should be no gaps in variable numbering. For example, if there are 3 variables,
      they should be numbered 1, 2, 3 -- not 1, 2, 4.

    Returns:
    The number of variables in the formula
    """
    return max(abs(literal) for clause in formula for literal in clause)


def evaluate(literal: Literal, assignment: Assignment) -> Optional[bool]:
    """
    Evaluates a literal given a partial assignment of variables to truth values.

    Parameters:
    - literal: A positive or negative integer representing a variable or its negation.
    - assignment: A partial assignment of variables to truth values.

    Returns:
    The truth value of the literal if defined in the assignment
    """
    assert literal != 0, "invalid literal"

    if literal > 0:
        return assignment[literal]

    if assignment[-literal] is None:
        return None

    return not assignment[-literal]


def clause_satisfied(clause: Clause, assignment: Assignment) -> bool:
    """
    A clause is satisfied if at least one of the literals in the clause is true under the given assignment.
    """

    return any(evaluate(literal, assignment) is True for literal in clause)


def clause_unsatisfied(clause: Clause, assignment: Assignment) -> bool:
    """
    A clause is unsatisfied if all the literals in the clause are false under the given assignment.
    """

    return all(evaluate(literal, assignment) is False for literal in clause)


def dpll(formula: Formula, assignment: Assignment | None = None) -> Assignment | None:
    """
    DPLL algorithm for solving CNF formulas.

    Parameters:
    - formula: A list of clauses, where each clause is a tuple of literals.
    - assignment: A partial assignment of variables to truth values.

    Note:
    - variables are be 1-indexed, and negative integers represent negated variables
    - there should be no gaps in variable numbering. For example, if there are 3 variables,
      they should be numbered 1, 2, 3 -- not 1, 2, 4.
    - scales ok with the number of clauses, but poorly with the number of variables

    Returns:
    A satisfying assignment if one exists, otherwise None.
    """

    if assignment is None:
        assignment = [None] * (cardinality(formula) + 1)

    # If all clauses are satisfied, return the current assignment
    if all(clause_satisfied(clause, assignment) for clause in formula):
        # Remove the dummy variable at index 0
        return assignment[1:]

    # If any clause is unsatisfied, return None
    if any(clause_unsatisfied(clause, assignment) for clause in formula):
        return None

    # Choose a variable to assign
    # (pick the first unassigned variable instead of a random one, for simplicity)
    var = next((i for i, value in enumerate(assignment) if value is None), None)
    assert var is not None, "No unassigned variables left"

    # Try setting the variable to True
    assignment[var] = True
    result = dpll(formula, assignment)
    if result is not None:
        return result

    # Try setting the variable to False
    assignment[var] = False
    result = dpll(formula, assignment)
    if result is not None:
        return result

    # If neither assignment leads to a satisfying solution, backtrack
    assignment[var] = None
    return None


def generate_3sat_instance(n, k) -> Formula:
    """
    Generates a random 3-SAT instance.

    Parameters:
    - n: Number of variables.
    - k: Number of clauses.

    Returns:
    A list of clauses, where each clause is a tuple of 3 integers.
    Positive integers represent the corresponding variable, negative integers represent its negation.
    """
    clauses = []
    for _ in range(k):
        # Select 3 unique variables for each clause
        variables = random.sample(range(1, n + 1), 3)
        # Randomly negate some of the variables
        clause = tuple(random.choice([v, -v]) for v in variables)
        clauses.append(clause)
    return clauses


def generate_msat_instance(n: int, m: int, k: int) -> Formula:
    """
    Generates a random m-SAT instance with n variables, m variables per clause, and k clauses.

    Parameters:
    - n: Total number of variables.
    - m: Number of variables per clause.
    - k: Total number of clauses.

    Returns:
    A list of clauses, where each clause is a tuple of m integers. Positive integers represent
    the corresponding variable, and negative integers represent its negation.
    """
    clauses = []
    used_clauses = set()

    while len(clauses) < k:
        # Allow repetition of variables if m > n
        variables = [random.randint(1, n) for _ in range(m)]
        # Randomly negate some of the variables
        clause = tuple(random.choice([v, -v]) for v in variables)

        if clause in used_clauses:
            continue

        clauses.append(clause)
    return clauses


def render(clauses: Formula, or_symbol="∨", and_symbol="∧") -> str:
    """
    Renders a list of 3-SAT clauses into a human-readable string.

    Parameters:
    - clauses: A list of clauses, where each clause is a tuple of 3 integers.

    Returns:
    A string representing the 3-SAT formula.
    """
    # Convert each clause to a string and join clauses with a logical AND
    clause_strings = [render_clause(clause, or_symbol=or_symbol) for clause in clauses]
    return f" {and_symbol} ".join(clause_strings)


def render_clause(clause: Clause, or_symbol: str = "∨") -> str:
    """
    Renders a single clause into a human-readable string.

    Parameters:
    - clause: A tuple of 3 integers.

    Returns:
    A string representing the clause.
    """
    return f"({f' {or_symbol} '.join(variable_names[literal] for literal in clause)})"


def print_stats(n, m, k, iterations=1000):
    import time

    gen_time = 0
    render_time = 0
    solve_time = 0
    dpll_time = 0
    sat_count = 0

    example_sat = None
    example_unsat = None

    for _ in range(iterations):
        gen_start = time.time()
        clauses = generate_msat_instance(n, m, k)
        gen_time += time.time() - gen_start

        render_start = time.time()
        render(clauses)
        render_time += time.time() - render_start

        dpll_start = time.time()
        model = dpll(clauses)
        dpll_time += time.time() - dpll_start

        if model is not None:
            sat_count += 1
            if example_sat is None:
                example_sat = clauses

        else:
            if example_unsat is None:
                example_unsat = clauses

    print(f"Total generation time: {gen_time:.2f}s")
    print(f"Total rendering time: {render_time:.2f}s")
    print(f"Total Z3 solving time: {solve_time:.2f}s")
    print(f"Total DPLL solving time: {dpll_time:.2f}s")
    print(f"Percentage of SAT instances: {sat_count / iterations * 100:.2f}%")
    print(f"Example SAT instance: {example_sat}")
    print(f"Example UNSAT instance: {example_unsat}")


def main():
    import sys

    n, m, k = (int(sys.argv[x]) for x in (1, 2, 3))
    print(f"Stats for {n} variables, {m} variables per clause, {k} clauses")
    print_stats(n, m, k)


if __name__ == "__main__":
    main()
