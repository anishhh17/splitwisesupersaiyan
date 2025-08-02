#!/usr/bin/env python3
"""
Comprehensive test suite for bill splitting logic
Tests both the Splitwise-style splitting and full bill calculation
"""

import unittest
from decimal import Decimal
from split_calculator import SplitCalculator


class TestSplitCalculator(unittest.TestCase):
    
    def setUp(self):
        self.calc = SplitCalculator()
    
    def test_splitwise_split_even_amounts(self):
        """Test splitting amounts that divide evenly"""
        # $10.00 ÷ 2 = $5.00 each
        result = self.calc.splitwise_split(10.00, 2)
        self.assertEqual(result, [5.00, 5.00])
        self.assertAlmostEqual(sum(result), 10.00, places=2)
        
        # $12.00 ÷ 4 = $3.00 each
        result = self.calc.splitwise_split(12.00, 4)
        self.assertEqual(result, [3.00, 3.00, 3.00, 3.00])
        self.assertAlmostEqual(sum(result), 12.00, places=2)
    
    def test_splitwise_split_uneven_amounts(self):
        """Test splitting amounts with remainders"""
        # $10.00 ÷ 3 = $3.33, $3.33, $3.34 (last gets extra cent)
        result = self.calc.splitwise_split(10.00, 3)
        expected = [3.34, 3.33, 3.33]  # First person gets the extra cent
        self.assertEqual(result, expected)
        self.assertAlmostEqual(sum(result), 10.00, places=2)
        
        # $25.47 ÷ 4 = $6.36, $6.36, $6.37, $6.38 (first two get extra cents)
        result = self.calc.splitwise_split(25.47, 4)
        # Check that sum is correct
        self.assertAlmostEqual(sum(result), 25.47, places=2)
        # Check that no individual amount has more than 2 decimal places
        for amount in result:
            self.assertEqual(round(amount, 2), amount)
    
    def test_splitwise_split_small_amounts(self):
        """Test splitting very small amounts"""
        # $0.05 ÷ 3 = $0.02, $0.02, $0.01 (first two get extra cent)
        result = self.calc.splitwise_split(0.05, 3)
        expected = [0.02, 0.02, 0.01]
        self.assertEqual(result, expected)
        self.assertAlmostEqual(sum(result), 0.05, places=2)
        
        # $0.01 ÷ 5 = $0.01, $0.00, $0.00, $0.00, $0.00 (only first person pays)
        result = self.calc.splitwise_split(0.01, 5)
        expected = [0.01, 0.00, 0.00, 0.00, 0.00]
        self.assertEqual(result, expected)
        self.assertAlmostEqual(sum(result), 0.01, places=2)
    
    def test_splitwise_split_edge_cases(self):
        """Test edge cases"""
        # Zero amount
        result = self.calc.splitwise_split(0.00, 3)
        self.assertEqual(result, [0.00, 0.00, 0.00])
        
        # Single person
        result = self.calc.splitwise_split(15.67, 1)
        self.assertEqual(result, [15.67])
        
        # Invalid inputs
        with self.assertRaises(ValueError):
            self.calc.splitwise_split(10.00, 0)
        
        with self.assertRaises(ValueError):
            self.calc.splitwise_split(10.00, -1)
        
        with self.assertRaises(ValueError):
            self.calc.splitwise_split(-10.00, 3)
    
    def test_marios_pizza_receipt(self):
        """Test with the actual Mario's Pizza receipt from the image"""
        # Items from the receipt
        items = [
            {"id": "1", "name": "Margherita Pizza", "price": 18.99, "is_tax_or_tip": False},
            {"id": "2", "name": "Garlic Bread", "price": 6.50, "is_tax_or_tip": False},
            {"id": "3", "name": "Coca Cola", "price": 3.99, "is_tax_or_tip": False},
            {"id": "4", "name": "Tax", "price": 2.51, "is_tax_or_tip": True},
            {"id": "5", "name": "Tip", "price": 5.76, "is_tax_or_tip": True},
        ]
        
        # Scenario: All three people share everything equally
        votes = {
            "1": ["alice", "bob", "charlie"],  # Pizza
            "2": ["alice", "bob", "charlie"],  # Garlic Bread  
            "3": ["alice", "bob", "charlie"],  # Coca Cola
        }
        
        result = self.calc.calculate_bill_split(items, votes, "alice")
        
        # Verify total bill amount
        total_bill = sum(item["price"] for item in items)
        self.assertAlmostEqual(total_bill, 37.75, places=2)
        
        # Verify split balances
        totals = result["totals"]
        total_sum = sum(totals.values())
        self.assertAlmostEqual(total_sum, 0.0, places=2)
        
        # Alice (payer) should have negative amount
        self.assertLess(totals["alice"], 0)
        
        # Bob and Charlie should have positive amounts
        self.assertGreater(totals["bob"], 0)
        self.assertGreater(totals["charlie"], 0)
        
        print(f"Mario's Pizza Split Results:")
        print(f"  Total bill: ${total_bill:.2f}")
        for person, amount in totals.items():
            if person == "alice":
                print(f"  {person} (payer): ${amount:.2f}")
            else:
                print(f"  {person}: ${amount:.2f}")
    
    def test_complex_bill_scenario(self):
        """Test a complex bill with different consumption patterns"""
        items = [
            {"id": "1", "name": "Pizza", "price": 24.99, "is_tax_or_tip": False},
            {"id": "2", "name": "Salad", "price": 12.50, "is_tax_or_tip": False},
            {"id": "3", "name": "Drinks", "price": 8.75, "is_tax_or_tip": False},
            {"id": "4", "name": "Dessert", "price": 15.25, "is_tax_or_tip": False},
            {"id": "5", "name": "Tax", "price": 5.13, "is_tax_or_tip": True},
            {"id": "6", "name": "Tip", "price": 13.31, "is_tax_or_tip": True},
        ]
        
        # Different consumption patterns
        votes = {
            "1": ["alice", "bob", "charlie", "diana"],  # All shared pizza
            "2": ["alice", "charlie"],                   # Alice and Charlie shared salad
            "3": ["bob", "diana"],                       # Bob and Diana had drinks
            "4": ["alice"],                              # Only Alice had dessert
        }
        
        result = self.calc.calculate_bill_split(items, votes, "bob")
        
        # Verify split balances
        totals = result["totals"]
        total_sum = sum(totals.values())
        self.assertAlmostEqual(total_sum, 0.0, places=2)
        
        # Verify payer has negative amount
        self.assertLess(totals["bob"], 0)
        
        print(f"\nComplex Bill Split Results:")
        print(f"  Total bill: ${sum(item['price'] for item in items):.2f}")
        for person, amount in totals.items():
            if person == "bob":
                print(f"  {person} (payer): ${amount:.2f}")
            else:
                print(f"  {person}: ${amount:.2f}")
    
    def test_no_eaters_scenario(self):
        """Test scenario where nobody voted for any items"""
        items = [
            {"id": "1", "name": "Pizza", "price": 20.00, "is_tax_or_tip": False},
            {"id": "2", "name": "Tax", "price": 2.00, "is_tax_or_tip": True},
        ]
        
        votes = {}  # Nobody ate anything
        
        result = self.calc.calculate_bill_split(items, votes, "alice")
        
        # Should return zero for payer only
        expected = {"payer_id": "alice", "totals": {"alice": 0.0}}
        self.assertEqual(result, expected)
    
    def test_precision_and_rounding(self):
        """Test that precision is maintained and rounding works correctly"""
        # Test a scenario that would cause issues with naive rounding
        total = 100.00
        people = 7
        
        result = self.calc.splitwise_split(total, people)
        
        # Verify sum is exact (allowing for tiny floating point errors)
        self.assertAlmostEqual(sum(result), total, places=2)
        
        # Verify all amounts have at most 2 decimal places
        for amount in result:
            self.assertEqual(round(amount, 2), amount)
        
        # Verify proper cent distribution logic
        # 100.00 ÷ 7 = 14.285714... 
        # In cents: 10000 ÷ 7 = 1428 remainder 4
        # So: 4 people get 1429 cents (14.29), 3 people get 1428 cents (14.28)
        expected_1429_count = 4  # remainder
        expected_1428_count = 3  # people - remainder
        
        count_1429 = sum(1 for x in result if abs(x - 14.29) < 0.001)
        count_1428 = sum(1 for x in result if abs(x - 14.28) < 0.001)
        
        self.assertEqual(count_1429, expected_1429_count)
        self.assertEqual(count_1428, expected_1428_count)


def run_manual_tests():
    """Run some manual verification tests"""
    calc = SplitCalculator()
    
    print("🧪 Manual Test Results")
    print("=" * 40)
    
    # Test the Splitwise examples
    test_cases = [
        (10.00, 3),
        (25.47, 4), 
        (37.75, 3),  # Mario's Pizza
        (0.05, 3),
        (100.00, 7),
        (1234.56, 13)
    ]
    
    for amount, people in test_cases:
        result = calc.splitwise_split(amount, people)
        print(f"${amount:.2f} ÷ {people} people:")
        print(f"  Result: {[f'${x:.2f}' for x in result]}")
        print(f"  Sum: ${sum(result):.2f} (should be ${amount:.2f})")
        print(f"  Difference: ${abs(sum(result) - amount):.6f}")
        print()


if __name__ == "__main__":
    # Run unittest suite
    print("🚀 Running Unit Tests")
    print("=" * 50)
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 50)
    run_manual_tests()