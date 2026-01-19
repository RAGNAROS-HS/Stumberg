from typing import Iterable, List, Tuple, Dict
from collections import deque, defaultdict
import copy


def solve_cnf(clauses: Iterable[Iterable[int]], num_vars: int) -> Tuple[str, List[int] | None]:
    clause_list = [list(cl) for cl in clauses]
    positive_occ: Dict[int, List[int]] = defaultdict(list)
    negative_occ: Dict[int, List[int]] = defaultdict(list)

    for idx, clause in enumerate(clause_list):
        for lit in clause:
            v = abs(lit)
            if lit > 0:
                positive_occ[v].append(idx)
            else:
                negative_occ[v].append(idx)

    def unit_propagation(
        active_clauses: List[Tuple[int, List[int]]], var_assignment: Dict[int, bool], depth: int
    ):
        queue = deque()
        clause_dict = dict(active_clauses)
        for idx, clause in active_clauses:
            if len(clause) == 1:
                l = clause[0]
                variable = abs(l)
                value = l > 0
                if variable not in var_assignment:
                    queue.append((variable, value))
        while queue:
            variable, value = queue.popleft()
            if variable in var_assignment:
                if var_assignment[variable] != value:
                    print(f"UNSAT (conflicting assignment to variable {variable}) at depth {depth}")
                    return None, None
                continue
            print(f"Unit propagation at depth {depth}: setting {variable} to {value}")
            var_assignment[variable] = value
            to_remove = set()
            occ = positive_occ if value else negative_occ
            for idx in occ[variable]:
                if idx in clause_dict:
                    to_remove.add(idx)
            occ_false = negative_occ if value else positive_occ
            for idx in occ_false[variable]:
                if idx not in clause_dict:
                    continue
                clause = clause_dict[idx]
                new_clause = [l for l in clause if abs(l) != variable or (l > 0) == value]
                if not new_clause:
                    print(f"UNSAT after unit propagation leads to empty clause at depth {depth}")
                    return None, None
                clause_dict[idx] = new_clause
                if len(new_clause) == 1:
                    l = new_clause[0]
                    new_var = abs(l)
                    new_val = l > 0
                    if new_var not in var_assignment:
                        queue.append((new_var, new_val))
            for idx in to_remove:
                clause_dict.pop(idx, None)
        return list(clause_dict.items()), var_assignment

    def davis_putnam(
        active_clauses: List[Tuple[int, List[int]]], var_assignment: Dict[int, bool], depth=0
    ):
        print(f"---\nRecursion depth {depth}: clauses={len(active_clauses)}")
        if not active_clauses:
            print(f"SAT found at depth {depth} with assignment {var_assignment}")
            solution = []
            for variable in range(1, num_vars + 1):
                val = var_assignment.get(variable, True)
                solution.append(variable if val else -variable)
            return ("SAT", solution)
        new_active_clauses = []
        for idx, clause in active_clauses:
            if not clause:
                print(f"UNSAT: empty clause at depth {depth}")
                return ("UNSAT", None)
            s = set(clause)
            if any(-lit in s for lit in s):
                print(f"Tautology removed at depth {depth}: {clause}")
                continue
            new_active_clauses.append((idx, clause))
        active_clauses = new_active_clauses
        active_clauses = [(i, list(cl)) for i, cl in active_clauses]
        active_clauses, var_assignment = unit_propagation(active_clauses, var_assignment.copy(), depth)
        if active_clauses is None:
            return ("UNSAT", None)
        if not active_clauses:
            print(f"SAT found after propagation at depth {depth}")
            solution = []
            for variable in range(1, num_vars + 1):
                val = var_assignment.get(variable, True)
                solution.append(variable if val else -variable)
            return ("SAT", solution)
        # MOMS variable selection
        min_len = min(len(clause) for _, clause in active_clauses)
        var_counts = defaultdict(int)
        for _, clause in active_clauses:
            if len(clause) == min_len:
                for lit in clause:
                    v = abs(lit)
                    if v not in var_assignment:
                        var_counts[v] += 1
        if var_counts:
            split_var = max(var_counts, key=var_counts.get)
        else:
            split_var = None
            for idx, clause in active_clauses:
                for lit in clause:
                    v = abs(lit)
                    if v not in var_assignment:
                        split_var = v
                        break
                if split_var:
                    break
        print(f"Branching at depth {depth}: trying variable {split_var}")
        if split_var is None:
            print(f"UNSAT: No variable left to split at depth {depth}")
            return ("UNSAT", None)
        print(f"Recursing on {split_var}=True at depth {depth}")
        assign_true = var_assignment.copy()
        assign_true[split_var] = True
        true_clauses = []
        for idx, clause in active_clauses:
            if split_var in clause:
                continue
            new_clause = [x for x in clause if x != -split_var]
            true_clauses.append((idx, new_clause))
        result = davis_putnam(true_clauses, assign_true, depth+1)
        if result[0] == "SAT":
            print(f"Returning SAT from {split_var}=True at depth {depth}")
            return result
        print(f"Recursing on {split_var}=False at depth {depth}")
        assign_false = var_assignment.copy()
        assign_false[split_var] = False
        false_clauses = []
        for idx, clause in active_clauses:
            if -split_var in clause:
                continue
            new_clause = [x for x in clause if x != split_var]
            false_clauses.append((idx, new_clause))
        return davis_putnam(false_clauses, assign_false, depth+1)

    init_active = [(i, list(cl)) for i, cl in enumerate(clause_list)]
    return davis_putnam(init_active, {}, 0)
