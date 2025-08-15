# Manual verification of split calculation
print('MANUAL SPLIT CALCULATION VERIFICATION:')
print('=====================================')

# Items and who ate them
pizza = 18.99  # Alice, Bob
bread = 6.50   # Alice, Bob, Charlie  
cola = 3.99    # Bob only
tax = 2.51     # Split among all eaters
tip = 5.76     # Split among all eaters

print(f'Pizza {pizza}: Alice & Bob = {pizza/2:.3f} each')
print(f'Bread {bread}: Alice, Bob, Charlie = {bread/3:.3f} each')
print(f'Cola {cola}: Bob only = {cola:.3f}')
print(f'Tax {tax}: All eaters = {tax/3:.3f} each')
print(f'Tip {tip}: All eaters = {tip/3:.3f} each')

alice_owes = pizza/2 + bread/3 + tax/3 + tip/3
bob_owes = pizza/2 + bread/3 + cola + tax/3 + tip/3  
charlie_owes = bread/3 + tax/3 + tip/3

total_bill = pizza + bread + cola + tax + tip

print(f'\nOWED AMOUNTS:')
print(f'Alice owes: {alice_owes:.2f}')
print(f'Bob owes: {bob_owes:.2f}')
print(f'Charlie owes: {charlie_owes:.2f}')
print(f'Total: {alice_owes + bob_owes + charlie_owes:.2f}')

print(f'\nSINCE ALICE PAID {total_bill:.2f}:')
print(f'Alice gets back: {total_bill - alice_owes:.2f}')
print(f'Bob owes Alice: {bob_owes:.2f}')
print(f'Charlie owes Alice: {charlie_owes:.2f}')

print(f'\nActual API results: Alice: -23.32, Bob: 18.4, Charlie: 4.92')
print(f'VERIFICATION:')
print(f'Alice correct: {abs(-23.32 - (total_bill - alice_owes)) < 0.01}')
print(f'Bob correct: {abs(18.4 - bob_owes) < 0.01}') 
print(f'Charlie correct: {abs(4.92 - charlie_owes) < 0.01}')