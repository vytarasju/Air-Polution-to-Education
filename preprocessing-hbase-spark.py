import happybase
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, mean, round
import matplotlib.pyplot as plt

#!!!To use HAPPYBASE start thrift server with hbase-daemon start thrift
"""PREPROCESSING BEGIN"""
project_wd = "/home/vytska/dev/big-data-project/"
education_worldbank_wd = project_wd + "/csv/world-bank-education.csv"
pollution_wd = project_wd + "/csv/air-pol.csv"

spark = SparkSession.builder.appName("example").getOrCreate()
education_worldbank_df = spark.read.csv(education_worldbank_wd, header=True, inferSchema=True)
pollution_df = spark.read.csv(pollution_wd, header=True, inferSchema=True)

# Selecting specific columns
pollution_selected = pollution_df.select('SpatialDimValueCode', 'Period', 'Dim1', 'FactValueNumeric')
# Sorting the DataFrame
pollution_selected = pollution_selected.orderBy('SpatialDimValueCode', 'Period', 'Dim1')
# Renaming columns
pollution_selected = pollution_selected.withColumnRenamed('SpatialDimValueCode', 'Country') \
                                       .withColumnRenamed('Dim1', 'Area') \
                                       .withColumnRenamed('FactValueNumeric', 'AQ')

# Selecting specific columns
education_worldbank_selected = education_worldbank_df.select(['Country Code', 'Indicator Name'] + [str(year) for year in range(2010, 2020)])
# Melt the DataFrame to long format using melt
education_worldbank_selected = education_worldbank_selected.melt(
    ids=['Country Code', 'Indicator Name'],
    values=[col(str(year)).alias(str(year)) for year in range(2010, 2020)],
    variableColumnName='Year',
    valueColumnName='Value'
)
# Pivot the DataFrame with Indicator Names as columns
education_worldbank_selected = education_worldbank_selected.groupBy("Country Code", "Year").pivot("Indicator Name").agg(expr("first(Value)")).withColumn("Year", col("Year").cast("int"))
# Merging DataFrames on 'Country Code' and 'Period'
merged_data = education_worldbank_selected.join(pollution_selected,
                                                (education_worldbank_selected['Country Code'] == pollution_selected['Country']) &
                                                (education_worldbank_selected['Year'] == pollution_selected['Period']),
                                                how='inner').drop('Country Code', 'Year')
merged_data_numeric = merged_data.drop('Country', 'Area')
"""PREPROCESSING END"""

"""ANALYSIS BEGIN"""
#Spark Correlation and Reggresion analysis handles NaN poorly, to save development time, I'm using Pandas for this
#Convert to Pandas DF
merged_data_pd = merged_data.toPandas()
merged_data_numeric_pd = merged_data_numeric.toPandas()

correlation_matrix = merged_data_numeric_pd.corr()['AQ']
filtered_correlation = correlation_matrix[abs(correlation_matrix) > 0.4].drop('AQ')

def plotCorrelation():
    plt.figure(figsize=(12, 15))
    filtered_correlation.plot(kind='barh', color='skyblue')
    plt.yticks(range(len(filtered_correlation.index)), filtered_correlation.index, rotation=0)  # Adjust the rotation angle
    plt.xlabel('Correlation Coefficient')
    plt.title('Correlation between PM2.5 and Other Features')
    plt.tight_layout()  # Ensures that the labels fit within the figure
    plt.savefig('graphic.png')

# feature_highlight = 'School enrollment, secondary, female (% gross)'
# data_regression = merged_data_pd[['AQ', feature_highlight]].dropna()1
"""ANALYSIS END"""

"""DBMS BEGIN"""
#Writting to HBase
connection = happybase.Connection(host='localhost')
def WriteHBase(table_name, pandas_data):
    if table_name.encode() not in connection.tables():
        connection.create_table(
            table_name,
            {"data": dict(),}  # 'data' is the column family name
        )

    # Open the table
    table = connection.table(table_name)

    # Insert or update records
    for row in pandas_data.itertuples(index=False, name=None):
        row_key, value = row
        data_dict = {"data:value": str(value)}

        table.put(row_key.encode(), data_dict)

    # Close the connection
    connection.close()

#Mean of AQ by Country
table_AQ = 'AQ'
pollution_selected_mean = pollution_selected.groupBy("Country").agg(round(mean("AQ"), 2).alias("Mean_AQ"))
pollution_selected_mean_pd = pollution_selected_mean.toPandas()
# WriteHBase(table_AQ, pollution_selected_mean_pd)

#Mean of EDU by Country
table_EDU = 'EDU_Secondary_Female'
education_worldbank_selected = education_worldbank_selected.groupBy("Country Code").agg(round(mean("Secondary education, general pupils (% female)"), 2).alias("Mean_Secondary_Female"))
education_worldbank_selected_pd = education_worldbank_selected.toPandas()
WriteHBase(table_EDU, education_worldbank_selected_pd)
"""DBMS END"""
