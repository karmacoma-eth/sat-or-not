import random
import z3

from typing import Optional

# Map from variable index to variable name
variable_names = {i: chr(96 + i) for i in range(1, 27)}  # Original variable names, a-z
variable_names.update(
    {-i: f"!{chr(96 + i)}" for i in range(1, 27)}
)  # Negated variable names


def generate_3sat_instance(n, k) -> list[tuple[int]]:
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


def generate_msat_instance(n: int, m: int, k: int) -> list[tuple[int]]:
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


def render(clauses: list[tuple[int]], or_symbol="∨", and_symbol="∧") -> str:
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


def render_clause(clause: tuple[int], or_symbol: str = "∨") -> str:
    """
    Renders a single clause into a human-readable string.

    Parameters:
    - clause: A tuple of 3 integers.

    Returns:
    A string representing the clause.
    """
    return f"({f' {or_symbol} '.join(variable_names[literal] for literal in clause)})"


def solve_cnf_instance(clauses: list[tuple[int]]) -> Optional[dict]:
    solver = z3.Solver()

    # Generate Z3 Boolean variables. Assuming variables in clauses are 1-indexed and can be negative for negation.
    max_var_index = max(abs(var) for clause in clauses for var in clause)
    variables = {i: z3.Bool(f"x{i}") for i in range(1, max_var_index + 1)}

    # translate into z3 clauses
    for clause in clauses:
        # Convert clause to Z3 format
        z3_clause = z3.Or(
            [
                variables[abs(var)] if var > 0 else z3.Not(variables[abs(var)])
                for var in clause
            ]
        )
        solver.add(z3_clause)

    # Solve the instance

    if solver.check() == z3.sat:
        model = solver.model()
        return {symbol.name(): bool(model[symbol]) for symbol in model.decls()}
    else:
        return None  # No solution found


def print_stats(n, m, k, iterations=1000):
    import time

    gen_times = []
    render_times = []
    solve_times = []
    sat_count = 0

    example_sat = None
    example_unsat = None

    for _ in range(iterations):
        gen_start = time.time()
        clauses = generate_msat_instance(n, m, k)
        gen_times.append(time.time() - gen_start)

        render_start = time.time()
        rendered_formula = render(clauses)
        render_times.append(time.time() - render_start)

        solve_start = time.time()
        model = solve_cnf_instance(clauses)  # Replace with actual Z3 call
        solve_times.append(time.time() - solve_start)

        if model is not None:
            sat_count += 1
            if example_sat is None:
                example_sat = rendered_formula

        else:
            if example_unsat is None:
                example_unsat = rendered_formula

    print(f"Total generation time: {sum(gen_times):.2f}s")
    print(f"Total rendering time: {sum(render_times):.2f}s")
    print(f"Total solving time: {sum(solve_times):.2f}s")
    print(f"Percentage of SAT instances: {sat_count / iterations * 100:.2f}%")
    print(f"Example SAT instance: {example_sat}")
    print(f"Example UNSAT instance: {example_unsat}")


def main():
    n = 3
    m = 3
    k = 6
    print(f"Stats for {n} variables, {m} variables per clause, {k} clauses")
    print_stats(n, m, k)
