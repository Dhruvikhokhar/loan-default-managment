import joblib
from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder

MODEL_PATH = Path(__file__).with_name('loan_model.joblib')

class APIService:
    """Train/cache the random-forest model and serve UI predictions."""
    def __init__(self):
        self.model = None
        self.features = None

    def _load_model(self):
        if self.model is not None:
            return
        
        # Load pre-trained model artifact if available
        if MODEL_PATH.exists():
            try:
                data_dict = joblib.load(MODEL_PATH)
                self.model = data_dict['model']
                self.features = data_dict['features']
                return
            except Exception:
                pass

        path = Path(__file__).with_name('Loan_default.csv')
        if not path.exists():
            for name in ["Loan_default (1).csv", "Loan_default.csv"]:
                src = Path(__file__).with_name(name)
                if src.exists():
                    path = src
                    break
        if not path.exists():
            raise FileNotFoundError('Loan_default.csv is missing. Place the dataset beside frontend and restart the app.')
        
        data = pd.read_csv(path)
        if 'Default' not in data:
            raise ValueError('Loan_default.csv must contain the Default target column.')
        X = data.drop(columns=[c for c in ('Default', 'LoanID') if c in data.columns])
        y = data['Default']
        numeric = X.select_dtypes(include='number').columns.tolist()
        categorical = [c for c in X.columns if c not in numeric]
        prep = ColumnTransformer([
            ('numeric', MinMaxScaler(), numeric),
            ('categorical', OneHotEncoder(drop='first', handle_unknown='ignore'), categorical)
        ])
        self.model = Pipeline([
            ('features', prep),
            ('classifier', RandomForestClassifier(n_estimators=30, max_depth=10, random_state=42, n_jobs=-1))
        ])
        self.model.fit(X, y)
        self.features = X.columns.tolist()
        try:
            joblib.dump({'model': self.model, 'features': self.features}, MODEL_PATH, compress=3)
        except Exception:
            pass

    def call_predict(self, payload, demo_mode=None):
        if demo_mode == 'error':
            raise RuntimeError('Demo connection error selected.')
        if demo_mode in ('approved', 'rejected'):
            approved = demo_mode == 'approved'
            return {'prediction': 'Approved' if approved else 'Rejected', 'probability': .87 if approved else .22, 'risk': 'Low' if approved else 'High', 'explanation': []}
        self._load_model()
        frame = pd.DataFrame([{name: payload[name] for name in self.features}], columns=self.features)
        classifier = self.model.named_steps['classifier']
        p_default = float(self.model.predict_proba(frame)[0][list(classifier.classes_).index(1)])
        approved = p_default < .5
        return {'prediction': 'Approved' if approved else 'Rejected', 'probability': 1-p_default, 'risk': 'Low' if p_default < .2 else ('Medium' if p_default < .5 else 'High'), 'explanation': []}

