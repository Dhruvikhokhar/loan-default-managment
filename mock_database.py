from datetime import datetime
import pandas as pd

class MockDatabase:
    def __init__(self): self.records=[]
    def add_record(self, payload, result):
        self.records.append({'id':f'APP-{len(self.records)+1:04d}', 'income':int(payload['Income']), 'loan_amount':int(payload['LoanAmount']), 'credit_history':int(payload['CreditScore']), 'prediction':result['prediction'], 'probability':result['probability'], 'risk':result['risk'], 'date':datetime.now().strftime('%Y-%m-%d %H:%M')})
    def get_all_records(self): return list(self.records)
