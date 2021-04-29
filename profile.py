# %%
import os
from pandas_profiling import ProfileReport
import pandas as pd

# %%
root_dir = "/Users/Jeff/Downloads/baseballdatabank-master/core"
dir_files = os.listdir(root_dir)
print(dir_files)

# %%
for file_name in [dir_files[6]]:
    df = pd.read_csv(f"{root_dir}/{file_name}")
    ProfileReport(
        df, title=f"{file_name} Profiling Report", explorative=True
    ).to_file(f"{root_dir}/profiles/{file_name}_profile.html")

# %%
