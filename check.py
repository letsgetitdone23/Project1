import sqlite3
import pandas as pd

conn = sqlite3.connect('restaurants.db')

def q(query):
    return pd.read_sql_query(query, conn).iloc[0][0]

print('banashankari strict:', q("SELECT count(*) FROM restaurants WHERE city = 'banashankari' AND rating >= 4.0 AND avg_cost_for_two BETWEEN 780 AND 1620"))
print('bangalore strict:', q("SELECT count(*) FROM restaurants WHERE city = 'bangalore' AND rating >= 4.0 AND avg_cost_for_two BETWEEN 780 AND 1620"))
print('bengaluru relaxed:', q("SELECT count(*) FROM restaurants WHERE (city LIKE '%banashankari%' OR locality LIKE '%banashankari%') AND rating >= 4.0 AND avg_cost_for_two BETWEEN 780 AND 1620"))
print('all banashankari:', q("SELECT count(*) FROM restaurants WHERE locality LIKE '%banashankari%' OR city LIKE '%banashankari%'"))
print('all bangalore rating>=4.0:', q("SELECT count(*) FROM restaurants WHERE city = 'bangalore' AND rating >= 4.0"))
