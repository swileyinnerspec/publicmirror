import torch
import time
import random
import math

# Set random seed for reproducibility
torch.manual_seed(1)
random.seed(1)
num_iterations=50
dim=2000
# Generate QUBO matrix
Q = torch.rand(dim, dim) * 10
Q = (Q + Q.T) / 2  # Ensure symmetry
Q = Q - Q.mean()   # Normalize

# Adam-based continuous optimization
y = torch.rand(Q.shape[0], requires_grad=True)

def flatten(y): 
	return torch.sigmoid(y - 0.5)

def qubo_loss(y): 
	return (y @ Q @ y)

def print_solution(y, method="Adam"):
	x_solution = (flatten(y).detach() > 0.5).int()
	print(f"{method} solution: {x_solution.tolist()}\tObjective: {(x_solution.float() @ Q @ x_solution.float()).item():.4f}")

def adam(Q,lr):
	optimizer = torch.optim.Adam([y], lr=lr)
	# Time Adam optimization
	for step in range(num_iterations):
		optimizer.zero_grad()
		loss = qubo_loss(flatten(y))
		loss.backward()
		optimizer.step()
		if step % 10 == 0:
			print(f"Step {step}, loss {loss.item():.4f}", end="\t")
			#print_solution(y)
	return (flatten(y) > 0.5).int(), qubo_loss(y), num_iterations

# Simulated Annealing implementation
def simulated_annealing(Q, threshhold, num_iterations, T_init=10.0, cooling_rate=0.995):
	n = Q.shape[0]
	x = torch.randint(0, 2, (n,), dtype=torch.float)  # Random initial binary vector
	best_x = x.clone()
	current_energy = (x @ Q @ x).item()
	best_energy = current_energy
	T = T_init

	for i in range(num_iterations):
		# Propose a bit flip
		idx = random.randint(0, n-1)
		x_new = x.clone()
		x_new[idx] = 1 - x_new[idx]
		new_energy = (x_new @ Q @ x_new).item()
		delta_E = new_energy - current_energy

		# Accept or reject
		if delta_E < 0 or random.random() < math.exp(-delta_E / T):
			x = x_new
			current_energy = new_energy
			if current_energy < best_energy:
				best_x = x.clone()
				best_energy = current_energy
		T *= cooling_rate  # Cool temperature
		if best_energy < threshhold:
			return best_x, best_energy, i
	return best_x, best_energy, num_iterations

start_time = time.time()
y,energy,n = adam(Q,0.3)
adam_time = time.time() - start_time
print(f"Adam final", end="\t")
#print_solution(y)
print(f"Adam training time: {adam_time:.4f} seconds\n")
# Time Simulated Annealing
start_time = time.time()
sa_solution, sa_energy,n = simulated_annealing(Q,energy,6000)
sa_time = time.time() - start_time
#print(f"SA solution: {sa_solution.int().tolist()}\tObjective: {sa_energy:.4f}")
print(f"SA training time: {sa_time:.4f} seconds")
print("SA iterations: ",n)

# Compare results
print("\nComparison:")
print(f"Adam time: {adam_time:.4f}s, Objective: {(flatten(y).detach() > 0.5).int().float() @ Q @ (flatten(y).detach() > 0.5).int().float():.4f}, iterations {num_iterations}")
print(f"SA time: {sa_time:.4f}s, Objective: {sa_energy:.4f}, iterations {n}")
