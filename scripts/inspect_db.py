import os
import importlib.util

proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def load_module_from_path(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Paths to csv modules
db_path = os.path.join(proj_root, 'csv', 'database.py')
model_path = os.path.join(proj_root, 'csv', 'database_model.py')

if not os.path.exists(db_path) or not os.path.exists(model_path):
    print('Missing csv modules at expected paths:')
    print(db_path)
    print(model_path)
    raise SystemExit(1)

dbmod = load_module_from_path(db_path, 'csv_database')
modelmod = load_module_from_path(model_path, 'csv_database_model')

SessionLocal = dbmod.SessionLocal
SalesData = modelmod.SalesData

# Query DB
from sqlalchemy import func

db = SessionLocal()
try:
    yrs = [r[0] for r in db.query(SalesData.ac_yr).distinct().all()]
    cnt = db.query(func.count(SalesData.id)).scalar()
    min_m = db.query(SalesData.mmyyyy).order_by(SalesData.mmyyyy).first()
    max_m = db.query(SalesData.mmyyyy).order_by(SalesData.mmyyyy.desc()).first()
    print('count=', cnt)
    print('distinct_ac_yr=', sorted(set(yrs)))
    print('min mmyyyy=', min_m[0] if min_m else None)
    print('max mmyyyy=', max_m[0] if max_m else None)
finally:
    db.close()
