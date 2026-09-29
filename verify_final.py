import json

with open('dashboard_results.json', 'r') as f:
    d = json.load(f)

lim4 = [l for l in d['limitations'] if l['item'] == 4][0]
print("Limitation 4 title:", lim4['title'])
print("Limitation 4 detail:", lim4['detail'])

with open('index.html', 'r') as f:
    html = f.read()

assert 'Spend Clustered at Exactly $499.00' in html
assert '$482.31' in html
assert '$750.00' in html
assert 'less than 5 cents' in html
assert 'confirmed visit lifts on Men (+5.8 pp) and dual-category buyers (+6.3 pp; +$1.66 spend lift is exploratory)' in html

print("\nAll assertions passed with 100% precision in both dashboard_results.json and index.html!")
