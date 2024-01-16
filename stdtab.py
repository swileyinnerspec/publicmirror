#!/usr/bin/python3 
import math
import scipy.stats as stats

def calculate_table(start, end, interval):
	print("{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format("Value", "ln", "arctan", "sin", "tan", "norm(x/10)", "exp"))
	print("-" * 70)

	current_value = start
	while current_value <= end:
		exp_value = round(math.exp(current_value), 3)
		ln_value = round(math.log(current_value) if current_value > 0 else float('-inf'), 3)
		arctan_value = round(math.atan(current_value), 3)
		sin_value = round(math.sin(math.radians(current_value)), 3)
		tan_value = round(math.tan(math.radians(current_value)), 3)
		normal = round(stats.norm.cdf(current_value / 10), 3)


		print("{:<10.2f} {:<10.3f} {:<10.3f} {:<10.3f} {:<10.3f} {:<10.3f} {:<10.3f}".format(
			current_value, ln_value, arctan_value, sin_value, tan_value, normal, exp_value))


		current_value += interval

# Set the range and interval
start_value = 0
end_value = 19
interval_value = 0.5

# Calculate and print the table
calculate_table(start_value, end_value, interval_value)

