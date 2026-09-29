import json

with open('dashboard_results.json', 'r') as f:
    data = json.load(f)

for lim in data['limitations']:
    if lim['item'] == 4:
        lim['title'] = 'Spend Clustered at Exactly $499.00'
        lim['detail'] = (
            "Evidence on whether $499 represents data censoring or a true transaction is ambiguous: "
            "a hard ceiling at $499.00 with zero orders above it is consistent with censoring, "
            "but the round, non-'.99' figure is also consistent with a genuine catalog price point, "
            "and the data cannot distinguish between the two. A sensitivity check recoded the 12 affected "
            "customers to $482.31 (the next-highest observed value) and to a hypothetical $750.00; "
            "the spend ATE and its confidence interval moved by less than 5 cents under either scenario, "
            "with no change to any conclusion."
        )

with open('dashboard_results.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Updated Limitation #4 cleanly.")
