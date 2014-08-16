import pandas as pd


def query_to_df(query):
    """
    Function to execute query and return DataFrame.
    """
    df = pd.DataFrame(query.all())
    df.columns = [x['name'] for x in query.column_descriptions]
    return df