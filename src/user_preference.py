
from util import *
from pyspark.sql import *
from pyspark.sql.types import *
from pyspark.mllib.linalg import *
from pyspark.mllib.classification import *
from pyspark.mllib.regression import *
from pyspark.ml.feature import *
import numpy as NP

sc, sqlContext = init_spark(verbose_logging='INFO', show_progress=False)
sc.addPyFile('util.py')

page_views_count = sqlContext.read.parquet('page_views_count')
doc_vecs_concat = sqlContext.read.parquet('doc_vecs_concat')

page_views_count = page_views_count.select('uuid', 'document_id', 'count')
pvvecs = (page_views_count.join(doc_vecs_concat, on='document_id')
          .drop('document_id'))
pvvecs = pvvecs.rdd.repartition(600)

def mapper1(r):
    uuid = r['uuid']
    doc_vec = r['document_vec']
    doc_vec_mult = sparse_vector_nmul(doc_vec, r['count'])
    return (uuid, (doc_vec_mult, r['count']))

def reducer1(r1, r2):
    # r: (uuid, (doc_vec_mult, count))
    # -> (uuid, (doc_vec_multA + doc_vec_multB, countA + countB))
    return (sparse_vector_add(r1[0], r2[0]), r1[1] + r2[1])

def mapper2(r):
    # r: (uuid, (doc_vec_mult_sum, count_sum))
    # -> (uuid, doc_vec_mult_sum / count_sum)
    doc_avg_vec = sparse_vector_nmul(r[1][0], 1. / r[1][1])
    return Row(uuid=r[0], uuid_vec=doc_avg_vec)

pvvecs_map1 = pvvecs.map(mapper1)
pvvecs_reduce1 = pvvecs_map1.reduceByKey(reducer1)
user_profile = pvvecs_reduce1.map(mapper2).toDF()

user_profile.write.parquet('user_profile')
