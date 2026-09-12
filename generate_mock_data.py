import pandas as pd
from deltalake.writer import write_deltalake
import os

# 1. Generate dummy insurance claims data
data = {
    "CLAIM_ID": ["CLM-1001", "CLM-1002", "CLM-1003", "CLM-1004"],
    "POLICY_ID": ["POL-999", "POL-888", "POL-777", "POL-888"],
    "CLAIM_AMOUNT": [1500.00, 8500.50, 250.00, 1200.00],
    "STATUS": ["OPEN", "CLOSED", "OPEN", "IN_REVIEW"]
}
df = pd.DataFrame(data)

# 2. Define our local "OneLake" directory
onelake_path = "mock_onelake/claims_delta"
os.makedirs(onelake_path, exist_ok=True)

# 3. Write the data as a Delta table
write_deltalake(onelake_path, df, mode="overwrite")
print(f"✅ Successfully generated mock Delta files at: {onelake_path}")