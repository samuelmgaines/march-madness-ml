import pandas as pd

# Load the dataset
input_file = "../data/mm-results.csv"  # Update this with the actual filename
df = pd.read_csv(input_file)

# Drop score columns
df_filtered = df[df["Round"] == 1].drop(columns=["Score 1", "Score 2"])

# Define the desired seed order
seed_order = [1, 8, 5, 4, 6, 3, 7, 2]

# Process each year separately
for year, year_df in df_filtered.groupby("Year"):
    sorted_df = (year_df.groupby("Region Number", group_keys=False)
                 .apply(lambda g: g.set_index("Seed 1").loc[seed_order].reset_index()))
    output_file = f"../data/first_rounds/{year}_firsts.csv"
    sorted_df.to_csv(output_file, index=False)
    print(f"Saved: {output_file}")
