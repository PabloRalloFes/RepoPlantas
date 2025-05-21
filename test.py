import pymongo

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient["Repositorio_Plantas"]
etiquetas= db["Etiquetas"]
docs= db["Docs"]

'''
id_etiqueta = etiquetas.find({"clasificacion": "Virus"}, {"_id": 1})

res = []
for entrada in id_etiqueta:
    res.append(docs.find_one({"clase": entrada["_id"]},{}))

res = filter(None, res)
'''
res = docs.find({"clase": 77}, {})



print(list(res))