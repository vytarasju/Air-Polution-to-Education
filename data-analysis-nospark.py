import pandas as pd
from scipy.stats import linregress
import matplotlib.pyplot as plt
import seaborn as sns

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

project_wd = "/home/vytska/dev/big-data-project/"
education_worldbank_wd = project_wd + "/csv/world-bank-education.csv"
pollution_wd = project_wd + "/csv/air-pol.csv"

education_worldbank_df = pd.read_csv(education_worldbank_wd)
pollution_df = pd.read_csv(pollution_wd)

pollution_selected = pollution_df[['SpatialDimValueCode', 'Period', 'Dim1', 'FactValueNumeric']] \
  .sort_values(by=['SpatialDimValueCode', 'Period', 'Dim1']).reset_index().drop(columns=['index'])
pollution_selected.columns = ['Country Code', 'Period', 'Area', 'PM2.5']


education_worldbank_selected = education_worldbank_df[['Country Code', 'Indicator Name'] + [str(year) for year in range(2010, 2020)]]
education_worldbank_selected = pd.melt(education_worldbank_selected, id_vars=['Country Code', 'Indicator Name'], \
                                        var_name='Period', value_name='Value').pivot(index=['Country Code', 'Period'], \
                                                                                      columns='Indicator Name', values='Value').reset_index()
education_worldbank_selected['Period'] = pollution_selected['Period'].astype(int)

education_worldbank_selected = education_worldbank_selected.dropna(axis=1, thresh=0.3*len(education_worldbank_selected))

merged_data = pd.merge(education_worldbank_selected, pollution_selected, on=['Country Code', 'Period'])
merged_data_numeric = merged_data.drop(columns=['Country Code', 'Area'])

correlation_matrix = merged_data[merged_data_numeric.columns].corr()['PM2.5']
filtered_correlation = correlation_matrix[abs(correlation_matrix) > 0.4].drop('PM2.5')

#Get Linear Regression
#Scatter plot with regression line
def plotLinReg(y_name, linear_regression):
  plt.figure(figsize=(10, 6))
  sns.scatterplot(x='PM2.5', y=y_name, data=data_regression, color='blue')
  plt.plot(data_regression['PM2.5'], linear_regression.intercept + linear_regression.slope * data_regression['PM2.5'], color='red', label='Regression Line')

  # Annotate the plot with regression information
  plt.annotate(f"Slope: {linear_regression.slope:.3f}\nIntercept: {linear_regression.intercept:.3f}\nR-squared: {linear_regression.rvalue**2:.3f}\nP-value: {linear_regression.pvalue:.3f}\nStandard error: {linear_regression.stderr:.3f}",
              xy=(0.05, 1.05), xycoords='axes fraction', fontsize=10, bbox=dict(boxstyle="round", alpha=0.1), color='black')

  plt.title('Scatter Plot with Regression Line')
  plt.xlabel('PM2.5')
  plt.ylabel(y_name)
  plt.legend()
  plt.tight_layout()
  plt.savefig('graphic.png')

feature_highlight = 'School enrollment, secondary, female (% gross)'
data_regression = merged_data[['PM2.5', feature_highlight]].dropna()
linear_regression = linregress(data_regression['PM2.5'], data_regression[feature_highlight])
# plotLinReg(feature_highlight, linear_regression)


# Assuming filtered_correlation is your DataFrame
# plt.figure(figsize=(12, 15))
# filtered_correlation.plot(kind='barh', color='skyblue')

# # Adjust y-axis label positions for better readability
# plt.yticks(range(len(filtered_correlation.index)), filtered_correlation.index, rotation=0)  # Adjust the rotation angle

# plt.xlabel('Correlation Coefficient')
# plt.title('Correlation between PM2.5 and Other Features')
# plt.tight_layout()  # Ensures that the labels fit within the figure

# plt.savefig('graphic.png')