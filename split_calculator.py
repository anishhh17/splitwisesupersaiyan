from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from typing import List, Dict

class SplitCalculator:
    @staticmethod
    def splitwise_split(total_amount: float, num_participants: int) -> List[float]:
        """
        Split an amount among participants exactly like Splitwise:
        - Each participant gets equal share rounded down to 2 decimals
        - Remaining cents distributed one-by-one to first participants
        - Final sum exactly equals total amount
        
        Args:
            total_amount: Total amount to split (float)
            num_participants: Number of participants (int)
            
        Returns:
            List of amounts for each participant
        """
        if num_participants <= 0:
            raise ValueError("Number of participants must be positive")
        if total_amount < 0:
            raise ValueError("Total amount cannot be negative")
        
        # Convert to cents to avoid floating point errors
        total_cents = round(total_amount * 100)
        
        # Calculate base amount per person (rounded down)
        base_cents_per_person = total_cents // num_participants
        
        # Calculate remaining cents to distribute
        remaining_cents = total_cents % num_participants
        
        # Create result array
        result = []
        
        # Distribute base amount + extra cents to first participants
        for i in range(num_participants):
            if i < remaining_cents:
                # First 'remaining_cents' participants get one extra cent
                participant_cents = base_cents_per_person + 1
            else:
                # Rest get base amount
                participant_cents = base_cents_per_person
            
            # Convert back to dollars with 2 decimal places
            result.append(round(participant_cents / 100, 2))
        
        return result

    @staticmethod
    def calculate_bill_split(items: List[Dict], votes: Dict[str, List[str]], payer_id: str) -> Dict:
        """
        Enhanced bill split calculation with Splitwise-style cent distribution
        """
        # 1. Find all users who ate at least one item
        all_eaters = set()
        for user_list in votes.values():
            all_eaters.update(user_list)
        if not all_eaters:
            return {"payer_id": payer_id, "totals": {payer_id: 0.0}}

        # 2. Calculate each user's base item total using precise splitting
        user_base_totals = defaultdict(Decimal)
        for item in items:
            if not item.get('is_tax_or_tip', False):
                item_id = str(item['id'])
                price = float(item['price'])
                eaters = votes.get(item_id, [])
                if eaters:
                    # Use Splitwise logic for item splitting
                    split_amounts = SplitCalculator.splitwise_split(price, len(eaters))
                    for i, uid in enumerate(eaters):
                        user_base_totals[uid] += Decimal(str(split_amounts[i]))

        # 3. Calculate tax/tip total and split using Splitwise logic
        tax_tip_total = sum(float(item['price']) for item in items if item.get('is_tax_or_tip', False))
        if tax_tip_total > 0:
            eater_list = list(all_eaters)  # Convert to list for consistent ordering
            tax_tip_splits = SplitCalculator.splitwise_split(tax_tip_total, len(eater_list))
            for i, uid in enumerate(eater_list):
                user_base_totals[uid] += Decimal(str(tax_tip_splits[i]))

        # 4. Build final totals (keep precision)
        user_totals = {}
        for uid in all_eaters:
            total = user_base_totals[uid] if uid in user_base_totals else Decimal('0.00')
            user_totals[uid] = float(total)

        # 5. Set payer's value to negative sum of all other users' values
        if payer_id not in user_totals:
            user_totals[payer_id] = 0.0
        
        total_others_owe = sum(amount for uid, amount in user_totals.items() if uid != payer_id)
        user_totals[payer_id] = -total_others_owe

        # 6. Verify sum is approximately zero (allowing for tiny floating point errors)
        total_sum = sum(user_totals.values())
        assert abs(total_sum) < 0.01, f"Totals do not sum to zero: {user_totals}, sum: {total_sum}"

        return {"payer_id": payer_id, "totals": user_totals}