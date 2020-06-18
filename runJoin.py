
import json
from pandas.io.json import json_normalize
import pandas as pd
from IPython.display import display, HTML
from elasticsearch import Elasticsearch
import elasticsearch.helpers






def left_join(left_table_name, left_table_join_key, right_table_name, right_table_join_key, is_right_side_null):

	connect_elastic()

	df_only_left_part=data_only_in_big_table(left_table_name, left_table_join_key)

	df_inner_join_part=inner_join(left_table_name, left_table_join_key, right_table_name, right_table_join_key)

	for column_name in list(df_inner_join_part.columns.values):
		if column_name not in list(df_only_left_part.columns.values):
			df_only_left_part[column_name]=NULL

	return df_only_left_part.concat(df_inner_join_part)


def inner_join(left_table_name, left_table_join_key, right_table_name, right_table_join_key):
	es = Elasticsearch('127.0.0.1',
        http_auth=('my_username', 'my_password'),
        port=9200)

	body_join_potential={"query": "aggs": {
      categories: {            
        filter: {bool:{ should:[{bool:{must:[{"term": {"table_name": "big_table"}},{"term": {"join_field_name": "big_table_join_field"}}]}},
        {bool:{must:[{"term": {"table_name": "small_table"}},{"term": {"join_field_name": "small_table_join_field"}}]}}]}} ,
        aggs: {
          inner_join: {
            terms: {field: 'value', "min_doc_count": 2}
          }
        }
      }
    }}
	results_join_potential = elasticsearch.helpers.scan(es, query=body_join_potential, index="join_keys_index")
	df_join_potential = pd.DataFrame.from_dict([document['_source'] for document in results_join_potential])

	list_of_join_values=list:(df_join_potential['value'])
	
	body_big_table={"query" : {
        "terms" : {
            "big_table_join_field" : [ list_of_join_values]
        }
    }
	results_big_table_data = elasticsearch.helpers.scan(es, query=body_big_table, index="join_keys_index")
	df_big_table = pd.DataFrame.from_dict([document['_source'] for document in results_big_table_data])


	body_small_table={"query" : {
        "terms" : {
            "small_table_join_field" : [ list_of_join_values]
        }
    }
	results_samll_table_data = elasticsearch.helpers.scan(es, query=body_small_table, index="join_keys_index")
	df_samll_table = pd.DataFrame.from_dict([document['_source'] for document in results_samll_table_data])

	final_result=results_big_table_data.set_index('big_table_join_field').join(results_small_table_data.set_index('small_table_join_field'))


def connect_elastic():
	es = Elasticsearch('127.0.0.1',
    http_auth=('my_username', 'my_password'),
    port=9200)

def data_only_in_big_table(left_table_name, left_table_join_key):
	body_join_potential={"query": "aggs": {
      categories: {            
        filter: {bool:{ must:[{bool:{must:[{"term": {"table_name": "big_table"}},{"term": {"join_field_name": "big_table_join_field"}}]}},
        {bool:{must:[bool:{must_not:{"term": {"table_name": "small_table"}},must_not:{"term": {"join_field_name": "small_table_join_field"}}}]}}]}} ,
        aggs: {
          inner_join: {
            terms: {field: 'value', "min_doc_count": 1}
          }
        }
      }
    }}
	results_join_potential = elasticsearch.helpers.scan(es, query=body_join_potential, index="join_keys_index")
	df_join_potential = pd.DataFrame.from_dict([document['_source'] for document in results_join_potential])

	list_of_join_values=list:(df_join_potential['value'])
	
	body_big_table={"query" : {
        "terms" : {
            "big_table_join_field" : [ list_of_join_values]
        }
    }
	results_big_table_data = elasticsearch.helpers.scan(es, query=body_big_table, index="join_keys_index")
	df_big_table = pd.DataFrame.from_dict([document['_source'] for document in results_big_table_data])
	return df_big_table


def write_output(df):
	compression_opts = dict(method='zip',archive_name='myfilepath.csv')  
	df.to_csv('myfilepath.csv', index=False,  compression=compression_opts)
