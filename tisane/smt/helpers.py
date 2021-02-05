from z3 import *

# @param pushed_constraints are constraints that were added as constraints all at once but then caused a conflict
# @param unsat_core is the set of cosntraints that caused a conflict
# @param keep_clause is the clause in unsat_core to keep and that resolves the conflict
def update_clauses(pushed_constraints: list, unsat_core: list, keep_clause: list): 
    # Verify that keep_clause is indeed a subset of unsat_core
    for c in keep_clause:
        assert(c in unsat_core)
    
    updated_constraints = list()
    for pc in pushed_constraints: 
        # Should we remove this constraint?
        if (pc in unsat_core) and (pc not in keep_clause): 
            pass
        else: 
            updated_constraints.append(pc)

    return updated_constraints
    
# @param current_constraints are constraints that are currently SAT before adding @param unsat_core
# @param unsat_core, which are the conflicting clauses
# @returns a set of new clauses with the unsat core resolved with user input
def elicit_user_input(current_constraints: list, unsat_core: list): 
    keep = list()
    while True: 
        # TODO: Allow for something totally new or different?
        idx = int(input(f'These cannot be true at the same time. Which is true? If neither, enter -1. {unsat_core}:'))
        if idx == -1: 
            pass
        elif idx in range(len(unsat_core)): 
            # only keep the constraint that is selected. 
            keep.append(unsat_core[idx])
            print(f"Ok, going to add {unsat_core[idx]} and remove the others.")
            break
        else:
            raise ValueError

    # return current_constraints + keep
    return keep

def verify_update_constraints(solver: Solver, assertions: list): 
    state = solver.check(assertions)
    if (state == unsat): 
        unsat_core = solver.unsat_core() 
        assert(len(state_cg_unsat_core) > 0)

        solver.push() # save state before add @param assertions

        # Ask user for input
        keep_constraint = elicit_user_input(solver.assertions(), unsat_core)
        # Modifies @param assertions
        updated_assertions = update_clauses(assertions, unsat_core, keep_constraint)
        assertions = updated_assertions
    elif (state == sat): 
        pass
    else: 
        raise ValueError(f"State of solver after adding user input conceptual graph constraints is {state}")

    # Double check that the new_assertions do not cause UNSAT
    solver.add(assertions)
    assert(solver.check() == sat)