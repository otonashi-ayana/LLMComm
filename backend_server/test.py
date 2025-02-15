nodes = [["October 05, 2023, 14:30:45", 1], ["January 06, 2023, 16:30:45", 2]]
nodes = sorted(nodes, key=lambda x: x[0])
print(nodes)

recency_vals = [0.99**i for i in range(1, len(nodes) + 1)]
print(recency_vals)

recency_out = dict()
for count, node in enumerate(nodes):
    recency_out[node[1]] = recency_vals[count]

print(recency_out)
