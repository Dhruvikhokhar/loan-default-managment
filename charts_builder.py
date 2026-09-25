import plotly.express as px
import pandas as pd

class ChartsBuilder:
    def _get_layout_colors(self, theme):
        is_dark = theme == 'dark'
        return {
            'template': 'plotly_dark' if is_dark else 'plotly_white',
            'color_discrete_sequence': ['#60a5fa', '#34d399', '#fbbf24', '#f87171', '#a78bfa'],
        }

    def _apply_theme(self, fig, theme):
        is_dark = theme == 'dark'
        text_color = '#f8fafc' if is_dark else '#0f172a'
        grid_color = '#334155' if is_dark else '#e2e8f0'
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Plus Jakarta Sans', 'color': text_color, 'size': 12},
            legend={'font': {'color': text_color}},
        )
        fig.update_xaxes(color=text_color, gridcolor=grid_color, linecolor=grid_color)
        fig.update_yaxes(color=text_color, gridcolor=grid_color, linecolor=grid_color)
        return fig

    def _chart(self, df, kind, x=None, y=None, color=None, **kwargs):
        if df is None or df.empty: df=pd.DataFrame({'prediction':['Approved','Rejected'],'count':[0,0]})
        theme = kwargs.pop('theme', 'dark')
        opts=self._get_layout_colors(theme)
        if kind=='pie': fig=px.pie(df,names=x,values=y,**opts)
        elif kind=='histogram': fig=px.histogram(df,x=x,color=color,**opts)
        else: fig=px.box(df,x=x,y=y,color=color,**opts)
        return self._apply_theme(fig, theme)
    def build_approval_donut(self,d,t): return self._chart(d,'pie',x='Default',y=None,theme=t)
    def build_income_dist(self,d,t): return self._chart(d,'histogram',x='Income',theme=t)
    def build_loan_amt_dist(self,d,t): return self._chart(d,'histogram',x='LoanAmount',theme=t)
    def build_credit_vs_approval(self,d,t): return self._chart(d,'box',x='Default',y='CreditScore',theme=t)
    def build_education_vs_approval(self,d,t): return self._chart(d,'box',x='Education',y='Income',theme=t)
    def build_property_vs_approval(self,d,t): return self._chart(d,'box',x='LoanPurpose',y='LoanAmount',theme=t)
