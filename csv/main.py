import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from database_model import Base, SalesData


CSV_TO_DB_COLUMNS = {
    'AcYr': 'ac_yr',
    'MMYYYY': 'mmyyyy',
    'Zone': 'zone',
    'BranchName': 'branch_name',
    'MKTType': 'mkt_type',
    'BrandName': 'brand_name',
    'SalesQty': 'sales_qty',
    'SalesAmt': 'sales_amt',
    'CNQty': 'cn_qty',
    'CNAmt': 'cn_amt',
    'ActQty': 'act_qty',
    'ActAmt': 'act_amt',
}


def _clean_text(value) -> str:
    if pd.isna(value):
        return ''
    return str(value).strip()


def _clean_number(value, default=None):
    if pd.isna(value) or value == '':
        return default
    return float(value)


def _row_key_from_values(values) -> tuple:
    return (
        _clean_text(values.get('AcYr')),
        _clean_text(values.get('MMYYYY')),
        _clean_text(values.get('Zone')).upper(),
        _clean_text(values.get('BranchName')).upper(),
        _clean_text(values.get('MKTType')).upper(),
        _clean_text(values.get('BrandName')).upper(),
        _clean_number(values.get('SalesQty'), 0) or 0,
        _clean_number(values.get('SalesAmt'), 0) or 0,
        _clean_number(values.get('CNQty'), None),
        _clean_number(values.get('CNAmt'), None),
        _clean_number(values.get('ActQty'), None),
        _clean_number(values.get('ActAmt'), None),
    )


def _row_key_from_model(record: SalesData) -> tuple:
    return (
        _clean_text(record.ac_yr),
        _clean_text(record.mmyyyy),
        _clean_text(record.zone).upper(),
        _clean_text(record.branch_name).upper(),
        _clean_text(record.mkt_type).upper(),
        _clean_text(record.brand_name).upper(),
        float(record.sales_qty or 0),
        float(record.sales_amt or 0),
        None if record.cn_qty is None else float(record.cn_qty),
        None if record.cn_amt is None else float(record.cn_amt),
        None if record.act_qty is None else float(record.act_qty),
        None if record.act_amt is None else float(record.act_amt),
    )


def load_csv_to_database(csv_file: str = "C:\\CODE\\python projects\\sir\\AI-SalesMitra\\csv\\Mfg_Sales.csv"):
    """Load CSV data into PostgreSQL database"""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Read CSV
    df = pd.read_csv(csv_file)
    
    # Clean column names (remove extra spaces)
    df.columns = df.columns.str.strip()
    
    # Map CSV columns to database columns
    db = SessionLocal()

    try:
        # Normalize CSV column name if necessary
        if 'AcYr' not in df.columns and 'ac_yr' in df.columns:
            df = df.rename(columns={'ac_yr': 'AcYr'})

        missing_columns = [column for column in CSV_TO_DB_COLUMNS if column not in df.columns]
        if missing_columns:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing_columns)}")

        existing_records = db.query(SalesData).all()
        existing_keys = {_row_key_from_model(record) for record in existing_records}

        new_records = []
        skipped_duplicates = 0
        seen_in_file = set()

        for _, row in df.iterrows():
            row_values = row.to_dict()
            row_key = _row_key_from_values(row_values)
            if row_key in existing_keys or row_key in seen_in_file:
                skipped_duplicates += 1
                continue
            seen_in_file.add(row_key)
            new_records.append(row_values)

        if not new_records:
            print(f"No new records to import. Skipped {skipped_duplicates} duplicate rows.")
            return

        # Insert only rows that are not already present. Dedupe by full row, not by year.
        for row in new_records:
            sales_record = SalesData(
                ac_yr=_clean_text(row.get('AcYr')),
                mmyyyy=_clean_text(row.get('MMYYYY')),
                zone=_clean_text(row.get('Zone')),
                branch_name=_clean_text(row.get('BranchName')),
                mkt_type=_clean_text(row.get('MKTType')),
                brand_name=_clean_text(row.get('BrandName')),
                sales_qty=_clean_number(row.get('SalesQty'), 0) or 0,
                sales_amt=_clean_number(row.get('SalesAmt'), 0) or 0,
                cn_qty=_clean_number(row.get('CNQty'), None),
                cn_amt=_clean_number(row.get('CNAmt'), None),
                act_qty=_clean_number(row.get('ActQty'), None),
                act_amt=_clean_number(row.get('ActAmt'), None),
            )
            db.add(sales_record)

        db.commit()
        years = sorted({_clean_text(row.get('AcYr')) for row in new_records if _clean_text(row.get('AcYr'))})
        print(f"Successfully loaded {len(new_records)} new records into database for years: {years}")
        if skipped_duplicates:
            print(f"Skipped {skipped_duplicates} duplicate rows.")

    except Exception as e:
        db.rollback()
        print(f"Error loading data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    load_csv_to_database()
