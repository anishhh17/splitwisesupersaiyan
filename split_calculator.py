from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from typing import List, Dict

class SplitCalculator:
    @staticmethod
    def calculate_bill_split(items: List[Dict], votes: Dict[str, List[str]], payer_id: str) -> Dict:
        # 1. Find all users who ate at least one item
        all_eaters = set()
        for user_list in votes.values():
            all_eaters.update(user_list)
        if not all_eaters:
            # No one ate anything, payer owes nothing
            return {"payer_id": payer_id, "totals": {payer_id: 0}}

        # 2. Calculate each user's base item total
        user_base_totals = defaultdict(Decimal)
        for item in items:
            if not item.get('is_tax_or_tip', False):
                item_id = str(item['id'])
                price = Decimal(str(item['price']))
                eaters = votes.get(item_id, [])
                if eaters:
                    share = price / len(eaters)
                    for uid in eaters:
                        user_base_totals[uid] += share

        # 3. Calculate tax/tip total and split equally among all eaters
        tax_tip_total = sum(Decimal(str(item['price'])) for item in items if item.get('is_tax_or_tip', False))
        tax_tip_per_person = tax_tip_total / Decimal(len(all_eaters))

        # 4. Build user_totals: base + tax/tip share (do not quantize yet)
        user_totals = {}
        for uid in all_eaters:
            base = user_base_totals[uid] if uid in user_base_totals else Decimal('0.00')
            total = base + tax_tip_per_person
            user_totals[uid] = total

        # 5. Quantize all non-payer user totals
        rounded_totals = {}
        for uid, val in user_totals.items():
            if uid != payer_id:
                if not isinstance(val, Decimal):
                    val = Decimal(str(val))
                rounded_totals[uid] = val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # 6. Set payer's value to negative sum of all other users' rounded values
        payer_val = -sum(rounded_totals.values())
        if not isinstance(payer_val, Decimal):
            payer_val = Decimal(str(payer_val))
        payer_val = payer_val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        rounded_totals[payer_id] = payer_val

        # 7. Assert sum is close to zero
        assert abs(sum(rounded_totals.values())) < 0.01, f"Totals do not sum to zero: {rounded_totals}"

        # 8. Convert all values to float for output
        return {"payer_id": payer_id, "totals": {uid: float(val) for uid, val in rounded_totals.items()}} 