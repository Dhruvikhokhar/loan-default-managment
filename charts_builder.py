import plotly.express as px
import pandas as pd

class ChartsBuilder:
    def _get_layout_colors(self, theme): return {'template': 'plotly_dark' if theme == 'dark' else 'plotly_white'}
    def _chart(self, df, kind, x=None, y=None, color=None, **kwargs):
        if df is None or df.empty: df=pd.DataFrame({'prediction':['Approved','Rejected'],'count':[0,0]})
        opts=self._get_layout_colors(kwargs.pop('theme','dark'))
        if kind=='pie': fig=px.pie(df,names=x,values=y,**opts)
        elif kind=='histogram': fig=px.histogram(df,x=x,color=color,**opts)
        else: fig=px.box(df,x=x,y=y,color=color,**opts)
        return fig
    def build_approval_donut(self,d,t): return self._chart(d,'pie',x='Default',y=None,theme=t)
    def build_income_dist(self,d,t): return self._chart(d,'histogram',x='Income',theme=t)
    def build_loan_amt_dist(self,d,t): return self._chart(d,'histogram',x='LoanAmount',theme=t)
    def build_credit_vs_approval(self,d,t): return self._chart(d,'box',x='Default',y='CreditScore',theme=t)
    def build_education_vs_approval(self,d,t): return self._chart(d,'box',x='Education',y='Income',theme=t)
    def build_property_vs_approval(self,d,t): return self._chart(d,'box',x='LoanPurpose',y='LoanAmount',theme=t)
