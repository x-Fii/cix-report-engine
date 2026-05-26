import pandas as pd

df = pd.read_csv("Maxis - Asset Listing Form(Store Listing ).csv")
print("Columns:", df.columns.tolist())
print("Types:", df['Type'].unique())
print("States:", df['State'].unique())
print("Regions:", df['Region'].unique())
