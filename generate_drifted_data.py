import pandas as pd
from deltalake import write_deltalake

# Upstream added a new 'RISK_SCORE' column without telling us
data = [
    {"CLAIM_ID": "CLM-1005", "POLICY_ID": "POL-5555", "CLAIM_AMOUNT": 850.00, "STATUS": "OPEN", "RISK_SCORE": 88},
    {"CLAIM_ID": "CLM-1006", "POLICY_ID": "POL-6666", "CLAIM_AMOUNT": 12500.00, "STATUS": "CLOSED", "RISK_SCORE": 15}
]
df = pd.DataFrame(data)

onelake_path = "./mock_onelake/claims_delta"

# Append the new batch and evolve the schema
write_deltalake(onelake_path, df, mode="append", schema_mode="merge")
print("✅ Drifted data appended. Delta schema successfully evolved.")