import json
from pathlib import Path
from typing import List, Dict, Any, Optional

POLICY_FILE = Path(__file__).resolve().parent.parent / "data" / "policies.json"

class PolicyService:
    def __init__(self):
        self._policies: Optional[List[Dict[str, Any]]] = None

    def _load_policies(self) -> List[Dict[str, Any]]:
        try:
            with open(POLICY_FILE, "r", encoding="utf-8") as f:
                policies = json.load(f)
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError("Return policy data is unavailable.") from error

        if not isinstance(policies, list) or not policies or not all(
            isinstance(policy, dict) for policy in policies
        ):
            raise RuntimeError("Return policy data is empty or invalid.")

        self._policies = policies
        return policies

    def get_all_policies(self) -> List[Dict[str, Any]]:
        return self._policies if self._policies is not None else self._load_policies()

    def search_policy(self, query: str) -> Dict[str, Any]:
        """
        Retrieves relevant return policy using keyword matching and category scoring (RAG).
        """
        query_norm = query.lower().strip()
        policies = self.get_all_policies()

        best_match = None
        best_score = -1

        for policy in policies:
            score = 0
            category = policy.get("category", "").lower()
            
            # Exact or partial category match
            if category in query_norm or query_norm in category:
                score += 10
            
            # Word token matches
            query_words = set(query_norm.split())
            category_words = set(category.split())
            overlap = query_words.intersection(category_words)
            score += len(overlap) * 3

            # Check allowed reasons
            for reason in policy.get("allowed_reasons", []):
                if any(word in reason.lower() for word in query_words):
                    score += 2

            # Check notes
            notes = policy.get("notes", "").lower()
            if any(word in notes for word in query_words if len(word) > 3):
                score += 1

            if score > best_score:
                best_score = score
                best_match = policy

        # Fallback to General policy if score is 0
        if best_score <= 0 or not best_match:
            for p in policies:
                if p.get("category", "").lower() == "general":
                    return p
            return policies[0]

        return best_match

policy_service = PolicyService()
