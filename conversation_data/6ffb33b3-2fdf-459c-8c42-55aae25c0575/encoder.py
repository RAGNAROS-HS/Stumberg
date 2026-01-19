"""
SAT Assignment Part 1 - Non-consecutive Sudoku Encoder (Puzzle -> CNF)

THIS is the file to edit.

Implement: to_cnf(input_path) -> (clauses, num_vars)

You're required to use a variable mapping as follows:
    var(r,c,v) = r*N*N + c*N + v
where r,c are in range (0...N-1) and v in (1...N).

You must encode:
  (1) Exactly one value per cell
  (2) For each value v and each row r: exactly one column c has v
  (3) For each value v and each column c: exactly one row r has v
  (4) For each value v and each sqrt(N)×sqrt(N) box: exactly one cell has v
  (5) Non-consecutive: orthogonal neighbors cannot differ by 1
  (6) Clues: unit clauses for the given puzzle
"""

import math
from typing import Tuple, Iterable


def read_file(input_path):
  with open(input_path, 'r') as file:
    data = file.read()

  nums = data.strip().split()
  num_length = len(nums)
  sudo_size = int(math.sqrt(num_length))

  for i in range(num_length):
    nums[i] = int(nums[i])

  grid = [] #initial representation of sudoku, 2d array, where the nested arrays are the rows
  for i in range(sudo_size):
    row = nums[i*sudo_size:(i+1)*sudo_size]
    grid.append(row)

  return grid, sudo_size

def var_mapper(row, column, value, sudo_size):
  return ((row * (sudo_size * sudo_size)) + (column * sudo_size) + value)

  


def to_cnf(input_path: str) -> Tuple[Iterable[Iterable[int]], int]:
    """
    Read puzzle from input_path and return (clauses, num_vars).

    - clauses: iterable of iterables of ints (each clause), no trailing 0s
    - num_vars: must be N^3 with N = grid size
    """
    grid, sudo_size = read_file(input_path)
    
   #### 
    at_least_one_per_cell = []
    for r in range(sudo_size):
      for c in range(sudo_size):
        clause = []
        for v in range(1, sudo_size+1):
          clause.append(var_mapper(r,c,v,sudo_size))
        at_least_one_per_cell.append(clause)

    at_most_one_per_cell = []
    for r in range(sudo_size):
      for c in range(sudo_size):
        for v1 in range(1, sudo_size+1):
          for v2 in range(v1+1, sudo_size+1):
            at_most_one_per_cell.append([-var_mapper(r, c, v1, sudo_size), -var_mapper(r, c, v2, sudo_size)])

    rule1 = at_least_one_per_cell + at_most_one_per_cell  
    
####
    at_least_one_per_row = []
    at_most_one_per_row = []
    for r in range(sudo_size):
      for v in range(1, sudo_size+1):
        clause = []
        for c in range(sudo_size):
          clause.append(var_mapper(r,c,v,sudo_size))
        at_least_one_per_row.append(clause)

        for c1 in range(sudo_size):
          for c2 in range(c1+1, sudo_size):
            at_most_one_per_row.append([-var_mapper(r, c1, v, sudo_size), -var_mapper(r, c2, v, sudo_size)])

    rule2 = at_least_one_per_row + at_most_one_per_row
####
    at_least_one_per_column = []
    at_most_one_per_column = []
    for c in range(sudo_size):
      for v in range(1, sudo_size+1):
        clause = []
        for r in range(sudo_size):
          clause.append(var_mapper(r,c,v,sudo_size))
        at_least_one_per_column.append(clause)

        for r1 in range(sudo_size):
          for r2 in range(r1+1, sudo_size):
            at_most_one_per_column.append([-var_mapper(r1, c, v, sudo_size), -var_mapper(r2, c, v, sudo_size)])
            
    rule3 = at_least_one_per_column + at_most_one_per_column

####
    at_least_one_per_box = []
    at_most_one_per_box = []
    box_size = int(math.sqrt(sudo_size))

    for box in range(sudo_size):
        br = box // box_size  #box row
        bc = box % box_size   #box column

        for v in range(1, sudo_size + 1):
            
            vars_in_box = []
            for r in range(br * box_size, (br + 1) * box_size):
                for c in range(bc * box_size, (bc + 1) * box_size):
                    vars_in_box.append(var_mapper(r, c, v, sudo_size))
            at_least_one_per_box.append(vars_in_box)

            
            n = len(vars_in_box)
            for i in range(n):
                for j in range(i + 1, n):
                    at_most_one_per_box.append([-vars_in_box[i], -vars_in_box[j]])

    rule4 = at_least_one_per_box + at_most_one_per_box 
    ####        
    non_consecutive= []

    for r in range(sudo_size):
        for c in range(sudo_size):
            # Right neighbor (r, c+1)
            if c < sudo_size - 1:
                for v in range(1, sudo_size):
                    non_consecutive.append([-var_mapper(r, c, v, sudo_size), -var_mapper(r, c + 1, v + 1, sudo_size)])
                    non_consecutive.append([-var_mapper(r, c, v + 1, sudo_size), -var_mapper(r, c + 1, v, sudo_size)])
            # Below neighbor (r+1, c)
            if r < sudo_size - 1:
                for v in range(1, sudo_size):
                    non_consecutive.append([-var_mapper(r, c, v, sudo_size), -var_mapper(r + 1, c, v + 1, sudo_size)])
                    non_consecutive.append([-var_mapper(r, c, v + 1, sudo_size), -var_mapper(r + 1, c, v, sudo_size)])
    rule5 = non_consecutive

    ####
    clues = []

    for r in range(sudo_size):
        for c in range(sudo_size):
            given_value = grid[r][c]
            if given_value != 0:
                clues.append([var_mapper(r, c, given_value, sudo_size)])
    rule6 = clues
    clauses = rule1 + rule2 + rule3 + rule4 + rule5 + rule6
    num_of_vars = sudo_size ** 3
    
    print("num of vars: %d!!!" %num_of_vars)
    print("Number of clauses: %d" % len(clauses))
    ##num of vars is the number of clauses, the actual num of vars is just sudo size cubed, the return values were confusing for me tbh but i think the final return is correct
    #print(grid)
    return (clauses, num_of_vars)
    #raise NotImplementedError