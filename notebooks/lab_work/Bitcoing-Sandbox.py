# Databricks notebook source
df = spark.table('workspace.csv.btc_usd_ytd')

# convert to pandas
pdf = df.toPandas()
pdf['snapped_at'] = pdf['snapped_at'].dt.date
pdf.rename( columns={'snapped_at': 'date'}, inplace=True)

# Add Target Column
pdf['Target'] = pdf['price'].shift(-1)
pdf.dropna(inplace=True)

pdf.drop(columns=['total_volume'], inplace=True)
pdf.sort_values(by='date', inplace=True)
pdf.reset_index(drop=True, inplace=True)
display(pdf)

# COMMAND ----------

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# Features and Target
features = ['price', 'market_cap']
y = pdf['Target']
x = pdf[features]

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(
    x, y,
    shuffle = False,
    test_size=0.2
)

# Train Model
model = LinearRegression().fit(X_train, y_train)

y_pred = model.predict(X_test)



# COMMAND ----------

import pandas as pd

x_test_reset = X_test.reset_index(drop=True)
y_test_reset = y_test.reset_index(drop=True)

date_col = pdf.loc[X_test.index]['date'].reset_index(drop=True)

# Build Results table
results = pd.DataFrame({
  'date': date_col,
  'price': x_test_reset['price'].round(2),
  'Predicted Price': y_pred.round(2)
})

# Difference in Price (Amount)
results['difference'] = (results['Predicted Price'] - results['price']).round(2)

# Difference in Price (%)
results['percentage_error'] = ((results['difference']/results['price'])*100).round(2)
display(results)

# COMMAND ----------


