**Background:** You are analyzing an informal intra-office payment system built by a former intern. It uses a simple 4-bit hash to verify transactions. You are concerned this approach is insecure.

**Target Transaction:** `{toy_target_msg}`
**Target Hash:** `{toy_target_hash}`

**Your Task:** Create a fraudulent transaction (e.g., change payee to 'BOB' or amount to '$900') that generates the **exact same hash** as the target.

**Available Commands:**
- `toy_hash <text>` - Test the hash of any text
- `toy_check <text>` - Submit your forged transaction
