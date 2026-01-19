import random
import math
from collections import namedtuple
from typing import Optional



class Node:
    def __init__(self, path=''):
        self.path = path 
        self.left = None
        self.right = None
        self.value = None
        self.parent = None
        self.visits = 0
        self.total_reward = 0.0
        self.mean_reward = 0.0
    
    def is_leaf(self):
        return self.left is None and self.right is None
    
    def get_ucb_score(self, parent_visits, c_param=1.4):
        if self.visits == 0:
            return float('inf')
        exploitation = self.mean_reward
        exploration = c_param * math.sqrt(math.log(parent_visits) / self.visits)
        return exploitation + exploration



def edit_distance(p1: str, p2: str) -> int:
    count = 0
    min_len = min(len(p1), len(p2))
    for i in range(min_len):
        if p1[i] == p2[i]:
            pass
        else:
            count = count + 1
    return count



def build_tree(depth, target_path):
    def build(current_depth, current_path, parent = None):
        if current_depth == depth:
            return None
        node = Node(current_path)
        node.parent = parent
        if current_depth == depth - 1:
            d_i = edit_distance(current_path, target_path[:len(current_path)])
            B = 10.0
            tau = 20 / 5
            x_i = B * math.exp(-d_i / tau)
            random.seed(int(current_path, 2))
            epsilon_i = random.gauss(0, 1)
            node.value = x_i + epsilon_i
        node.left = build(current_depth+1, current_path+"0", node)
        node.right = build(current_depth+1, current_path+"1", node)
        return node
    return build(0,'')



def get_node_by_path(root, path):
    node = root
    for bit in path:
        if bit == '0':
            node = node.left
        else:
            node = node.right
        if node is None:
            return None
    return node



def count_visited_nodes(node: Node) -> int:
    if not node:
        return 0
    count = 1 if node.visits > 0 else 0
    count += count_visited_nodes(node.left)
    count += count_visited_nodes(node.right)
    return count



def select(root: Node, c_param: float) -> tuple[Node, int]:
    node = root
    nodes_visited = 1
    while not node.is_leaf():
        unexpanded = [c for c in [node.left, node.right] if c and c.visits == 0]
        if unexpanded:
            return unexpanded[0], nodes_visited
        visited_children = [c for c in [node.left, node.right] if c and c.visits > 0]
        if not visited_children:
            break
        node = max(visited_children, key=lambda c: c.get_ucb_score(node.visits, c_param))
        nodes_visited += 1
    return node, nodes_visited



def rollout_to_leaf(node: Node, target_path: str) -> Node:
    current = node
    depth_reached = 0
    while not current.is_leaf():
        children = [c for c in [current.left, current.right] if c]
        if children:
            current = random.choice(children)
            depth_reached += 1
        else:
            break
    return current, depth_reached



def simulate(node: Node, num_rollouts: int = 5) -> float:
    return node.value or 0.0



def backpropagate(node: Node, reward: float):
    current = node
    while current is not None:
        current.visits += 1
        current.total_reward += reward
        current.mean_reward = current.total_reward / current.visits
        current = current.parent



def mcts_iteration(root: Node, target_path: str, c_param: float):
    selected, nodes_visited = select(root, c_param)
    if not selected.is_leaf():
        unexpanded = [c for c in [selected.left, selected.right] if c and c.visits == 0]
        if unexpanded:
            selected = unexpanded[0]
    leaf_node, depth_reached = rollout_to_leaf(selected, target_path)
    reward = simulate(leaf_node)
    backpropagate(leaf_node, reward)
    return leaf_node.path, reward, nodes_visited, depth_reached



def get_best_path(root: Node) -> str:
    best_node = root
    while not best_node.is_leaf():
        children = [c for c in [best_node.left, best_node.right] if c and c.visits > 0]
        if not children:
            break
        best_node = max(children, key=lambda c: c.mean_reward)
    return best_node.path



def mcts_with_stats(root: Node, target_path: str, num_iterations: int, c_param: float = 1.4):
    total_nodes_visited = 0
    depth_values = []
    rewards_progress = []
    best_reward_so_far = float('-inf')
    for i in range(num_iterations):
        path, reward, nodes_visited, depth_reached = mcts_iteration(root, target_path, c_param)
        total_nodes_visited += nodes_visited
        depth_values.append(depth_reached)
        if reward > best_reward_so_far:
            best_reward_so_far = reward
        rewards_progress.append(best_reward_so_far)
    target_node = get_node_by_path(root, target_path)
    best_path = get_best_path(root)
    best_node = get_node_by_path(root, best_path)
    visited_nodes = count_visited_nodes(root)
    total_nodes = 2**20 - 1
    efficiency = visited_nodes / total_nodes
    effectiveness = (best_node.value / target_node.value) if target_node and target_node.value and best_node and best_node.value > 0 else 0
    return {
        'c_param': c_param,
        'iterations': num_iterations,
        'total_nodes_visited': total_nodes_visited,
        'visited_nodes': visited_nodes,
        'efficiency': efficiency,
        'effectiveness': effectiveness,
        'best_reward': best_node.value if best_node and best_node.value else 0,
        'target_reward': target_node.value if target_node and target_node.value else 0,
        'max_depth_reached': max(depth_values) if depth_values else 0,
        'reward_progress': rewards_progress
    }



if __name__ == "__main__":
    import matplotlib.pyplot as plt

    target_path = '01100100001110001100'
    c_values = [0.0, 0.5, 1.0, 2.0, 5.0]
    stats_list = []

    print("C_PARAM | Iter | Visited(%) | Effctv% | Best/Target | MaxDepth")
    print("-" * 70)

    for c in c_values:
        root = build_tree(21, target_path)
        stats = mcts_with_stats(root, target_path, 20, c)
        stats_list.append(stats)
        print(f"{stats['c_param']}  | {stats['iterations']}  | "
              f"{stats['visited_nodes']}({stats['efficiency']*100:.2f}%) | "
              f"{stats['effectiveness']*100:.2f}% | "
              f"{stats['best_reward']:.4f}/{stats['target_reward']:.4f} | {stats['max_depth_reached']}")

    plt.figure(figsize=(12, 6))
    for stats in stats_list:
        plt.plot(range(1, stats['iterations'] + 1), stats['reward_progress'], label=f"c={stats['c_param']}")

    plt.xlabel("Iteration")
    plt.ylabel("Best Reward So Far")
    plt.title("Reward Improvement Over Iterations")
    plt.legend()
    plt.show()
