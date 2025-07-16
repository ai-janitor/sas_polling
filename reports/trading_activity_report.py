"""
=============================================================================
TRADING ACTIVITY REPORT GENERATOR
=============================================================================
Purpose: Generate comprehensive trading activity and performance analysis
Framework: Inherits from base_report.py
Output Formats: HTML, PDF, CSV

STRICT REQUIREMENTS:
- Load trading data from mock-data/trading_activity.csv
- Support asset class filtering
- Generate P&L analysis by trader and desk
- Include trade volume and count metrics
- Calculate trading performance ratios
- Validate input parameters

REPORT SECTIONS:
1. Trading Summary
2. P&L Analysis by Trader
3. Volume Analysis by Asset Class
4. Trade Performance Metrics
5. Top Trades (by P&L)

PARAMETERS:
- trade_date: Date for trading analysis
- asset_class: Asset class filter (all, equity, fixed_income, derivatives, forex)
- pnl_analysis: Include P&L breakdown
- trader_filter: Optional trader ID filter

OUTPUT FILES:
- trading_activity_report.html: Interactive HTML report
- trading_activity_data.csv: Raw trading data export
- trading_summary.pdf: Summary PDF report

MOCK DATA STRUCTURE:
trading_activity.csv columns:
- trade_date: Trading date
- trade_id: Unique trade identifier
- trader_id: Trader identifier
- desk: Trading desk name
- asset_class: Asset classification
- symbol: Security symbol
- side: Buy/Sell
- quantity: Trade quantity
- price: Execution price
- notional: Trade notional value
- commission: Trading commission
- pnl: Realized P&L
- trade_time: Execution timestamp
=============================================================================
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from base_report import BaseReport

class TradingActivityReport(BaseReport):
    def __init__(self):
        super().__init__()
        self.report_id = "trading_activity"
        self.report_name = "Trading Activity Report"
        
    def validate_parameters(self, params):
        """Validate input parameters for trading report"""
        errors = []
        
        if not params.get('trade_date'):
            errors.append("Trade date is required")
        else:
            try:
                trade_date = datetime.strptime(params['trade_date'], '%Y-%m-%d')
                if trade_date > datetime.now():
                    errors.append("Trade date cannot be in the future")
            except ValueError:
                errors.append("Invalid date format for trade_date")
        
        asset_class = params.get('asset_class', 'all')
        valid_classes = ['all', 'equity', 'fixed_income', 'derivatives', 'forex']
        if asset_class not in valid_classes:
            errors.append(f"Asset class must be one of: {', '.join(valid_classes)}")
        
        trader_filter = params.get('trader_filter', '')
        if trader_filter and not trader_filter.replace(' ', '').isalnum():
            errors.append("Trader filter must be alphanumeric")
        
        return errors
    
    def get_output_formats(self):
        """Return supported output formats"""
        return ['HTML', 'PDF', 'CSV']
    
    def get_estimated_duration(self):
        """Return estimated processing time in seconds"""
        return 150
    
    def load_data(self, params):
        """Load and filter trading data"""
        try:
            # Load mock trading data
            data_path = os.path.join(self.get_data_path(), 'trading_activity.csv')
            df = pd.read_csv(data_path)
            
            # Convert date and time columns
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df['trade_time'] = pd.to_datetime(df['trade_time'])
            
            # Filter by trade date
            trade_date = datetime.strptime(params['trade_date'], '%Y-%m-%d')
            filtered_df = df[df['trade_date'].dt.date == trade_date.date()]
            
            # Filter by asset class if specified
            asset_class = params.get('asset_class', 'all')
            if asset_class != 'all':
                filtered_df = filtered_df[filtered_df['asset_class'] == asset_class]
            
            # Filter by trader if specified
            trader_filter = params.get('trader_filter', '').strip()
            if trader_filter:
                filtered_df = filtered_df[filtered_df['trader_id'].str.contains(trader_filter, case=False)]
            
            return filtered_df
            
        except Exception as e:
            raise Exception(f"Failed to load trading data: {str(e)}")
    
    def calculate_trading_metrics(self, df, params):
        """Calculate trading metrics and performance indicators"""
        if df.empty:
            return {
                'total_trades': 0,
                'total_volume': 0,
                'total_pnl': 0,
                'trader_summary': pd.DataFrame(),
                'asset_class_summary': pd.DataFrame(),
                'desk_summary': pd.DataFrame(),
                'top_trades': pd.DataFrame()
            }
        
        # Overall summary metrics
        total_trades = len(df)
        total_volume = df['notional'].sum()
        total_pnl = df['pnl'].sum()
        total_commission = df['commission'].sum()
        
        # Calculate average trade size
        avg_trade_size = total_volume / total_trades if total_trades > 0 else 0
        
        # P&L analysis by trader
        trader_summary = df.groupby(['trader_id', 'desk']).agg({
            'trade_id': 'count',
            'notional': 'sum',
            'pnl': ['sum', 'mean'],
            'commission': 'sum'
        }).round(2)
        
        # Flatten column names
        trader_summary.columns = ['trade_count', 'total_notional', 'total_pnl', 'avg_pnl', 'total_commission']
        trader_summary = trader_summary.reset_index()
        
        # Calculate win rate for each trader
        trader_win_rates = df.groupby('trader_id').apply(
            lambda x: (x['pnl'] > 0).sum() / len(x) * 100 if len(x) > 0 else 0
        ).reset_index()
        trader_win_rates.columns = ['trader_id', 'win_rate']
        
        trader_summary = trader_summary.merge(trader_win_rates, on='trader_id', how='left')
        trader_summary = trader_summary.sort_values('total_pnl', ascending=False)
        
        # Asset class summary
        asset_class_summary = df.groupby('asset_class').agg({
            'trade_id': 'count',
            'notional': 'sum',
            'pnl': 'sum',
            'commission': 'sum'
        }).round(2).reset_index()
        asset_class_summary.columns = ['asset_class', 'trade_count', 'total_notional', 'total_pnl', 'total_commission']
        
        # Desk summary
        desk_summary = df.groupby('desk').agg({
            'trade_id': 'count',
            'notional': 'sum',
            'pnl': 'sum',
            'commission': 'sum'
        }).round(2).reset_index()
        desk_summary.columns = ['desk', 'trade_count', 'total_notional', 'total_pnl', 'total_commission']
        desk_summary = desk_summary.sort_values('total_pnl', ascending=False)
        
        # Top trades by P&L
        top_trades = df.nlargest(10, 'pnl')[['trade_id', 'trader_id', 'symbol', 'side', 'quantity', 'price', 'pnl', 'trade_time']]
        
        # Calculate additional metrics
        profitable_trades = len(df[df['pnl'] > 0])
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'total_volume': total_volume,
            'total_pnl': total_pnl,
            'total_commission': total_commission,
            'avg_trade_size': avg_trade_size,
            'win_rate': win_rate,
            'profitable_trades': profitable_trades,
            'trader_summary': trader_summary,
            'asset_class_summary': asset_class_summary,
            'desk_summary': desk_summary,
            'top_trades': top_trades
        }
    
    def generate_html_charts(self, metrics, params):
        """Generate Plotly charts for HTML output"""
        charts = {}
        
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            
            # P&L by Trader Chart
            if not metrics['trader_summary'].empty:
                fig_trader = go.Figure(data=[
                    go.Bar(
                        x=metrics['trader_summary']['trader_id'],
                        y=metrics['trader_summary']['total_pnl'],
                        name='P&L by Trader',
                        marker_color=['green' if x > 0 else 'red' for x in metrics['trader_summary']['total_pnl']]
                    )
                ])
                fig_trader.update_layout(
                    title="P&L by Trader",
                    xaxis_title="Trader ID",
                    yaxis_title="P&L ($)",
                    template="plotly_white"
                )
                charts['trader_pnl'] = fig_trader.to_html(include_plotlyjs='cdn', div_id="trader_pnl_chart")
            
            # Asset Class Volume Pie Chart
            if not metrics['asset_class_summary'].empty:
                fig_asset = go.Figure(data=[
                    go.Pie(
                        labels=metrics['asset_class_summary']['asset_class'],
                        values=metrics['asset_class_summary']['total_notional'],
                        hole=0.4
                    )
                ])
                fig_asset.update_layout(
                    title="Trading Volume by Asset Class",
                    template="plotly_white"
                )
                charts['asset_volume'] = fig_asset.to_html(include_plotlyjs='cdn', div_id="asset_volume_chart")
            
        except ImportError:
            # Plotly not available, skip charts
            pass
        except Exception as e:
            print(f"Warning: Failed to generate charts: {str(e)}")
        
        return charts
    
    def generate(self, params, output_path):
        """Main report generation method"""
        try:
            # Validate parameters
            validation_errors = self.validate_parameters(params)
            if validation_errors:
                raise Exception(f"Parameter validation failed: {', '.join(validation_errors)}")
            
            # Load and process data
            df = self.load_data(params)
            metrics = self.calculate_trading_metrics(df, params)
            
            # Generate outputs
            outputs = {}
            
            # HTML Report
            if 'HTML' in self.get_output_formats():
                charts = self.generate_html_charts(metrics, params)
                html_content = self.generate_html_report(metrics, params, charts)
                html_path = os.path.join(output_path, f"{self.report_id}_report.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                outputs['HTML'] = html_path
            
            # CSV Export
            if 'CSV' in self.get_output_formats():
                csv_path = os.path.join(output_path, f"{self.report_id}_data.csv")
                df.to_csv(csv_path, index=False)
                outputs['CSV'] = csv_path
            
            # PDF (placeholder)
            if 'PDF' in self.get_output_formats():
                pdf_path = os.path.join(output_path, f"{self.report_id}_summary.pdf")
                with open(pdf_path, 'w') as f:
                    f.write("PDF generation requires additional libraries")
                outputs['PDF'] = pdf_path
            
            return outputs
            
        except Exception as e:
            raise Exception(f"Trading activity report generation failed: {str(e)}")
    
    def generate_html_report(self, metrics, params, charts):
        """Generate HTML report content"""
        trade_date = params['trade_date']
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading Activity Report - {trade_date}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2563eb; color: white; padding: 20px; margin-bottom: 20px; }}
                .summary {{ background: #f8fafc; padding: 15px; margin-bottom: 20px; border-left: 4px solid #2563eb; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .chart-container {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #059669; }}
                .metric-label {{ font-size: 14px; color: #6b7280; }}
                .positive {{ color: #059669; }}
                .negative {{ color: #dc2626; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Trading Activity Report</h1>
                <p>Trade Date: {trade_date}</p>
            </div>
            
            <div class="summary">
                <h2>Trading Summary</h2>
                <div class="metric">
                    <div class="metric-value">{metrics['total_trades']:,}</div>
                    <div class="metric-label">Total Trades</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${metrics['total_volume']:,.0f}</div>
                    <div class="metric-label">Total Volume</div>
                </div>
                <div class="metric">
                    <div class="metric-value {'positive' if metrics['total_pnl'] >= 0 else 'negative'}">${metrics['total_pnl']:,.0f}</div>
                    <div class="metric-label">Total P&L</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{metrics['win_rate']:.1f}%</div>
                    <div class="metric-label">Win Rate</div>
                </div>
            </div>
        """
        
        # Add P&L analysis if enabled
        if params.get('pnl_analysis', True) and not metrics['trader_summary'].empty:
            html_template += """
            <h2>P&L Analysis by Trader</h2>
            <table>
                <thead>
                    <tr>
                        <th>Trader ID</th>
                        <th>Desk</th>
                        <th>Trades</th>
                        <th>Total Volume ($)</th>
                        <th>Total P&L ($)</th>
                        <th>Avg P&L ($)</th>
                        <th>Win Rate (%)</th>
                        <th>Commission ($)</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for _, row in metrics['trader_summary'].iterrows():
                pnl_class = 'positive' if row['total_pnl'] >= 0 else 'negative'
                html_template += f"""
                        <tr>
                            <td>{row['trader_id']}</td>
                            <td>{row['desk']}</td>
                            <td>{row['trade_count']:,}</td>
                            <td>${row['total_notional']:,.0f}</td>
                            <td class="{pnl_class}">${row['total_pnl']:,.0f}</td>
                            <td class="{pnl_class}">${row['avg_pnl']:,.0f}</td>
                            <td>{row['win_rate']:.1f}%</td>
                            <td>${row['total_commission']:,.0f}</td>
                        </tr>
                """
            
            html_template += """
                </tbody>
            </table>
            """
        
        # Add charts if available
        if charts:
            html_template += """
            <h2>Visualizations</h2>
            """
            for chart_name, chart_html in charts.items():
                html_template += f"""
                <div class="chart-container">
                    {chart_html}
                </div>
                """
        
        # Asset class summary
        if not metrics['asset_class_summary'].empty:
            html_template += """
            <h2>Volume by Asset Class</h2>
            <table>
                <thead>
                    <tr>
                        <th>Asset Class</th>
                        <th>Trades</th>
                        <th>Total Volume ($)</th>
                        <th>Total P&L ($)</th>
                        <th>Commission ($)</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for _, row in metrics['asset_class_summary'].iterrows():
                pnl_class = 'positive' if row['total_pnl'] >= 0 else 'negative'
                html_template += f"""
                        <tr>
                            <td>{row['asset_class']}</td>
                            <td>{row['trade_count']:,}</td>
                            <td>${row['total_notional']:,.0f}</td>
                            <td class="{pnl_class}">${row['total_pnl']:,.0f}</td>
                            <td>${row['total_commission']:,.0f}</td>
                        </tr>
                """
            
            html_template += """
                </tbody>
            </table>
            """
        
        # Top trades
        if not metrics['top_trades'].empty:
            html_template += """
            <h2>Top Trades by P&L</h2>
            <table>
                <thead>
                    <tr>
                        <th>Trade ID</th>
                        <th>Trader</th>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>P&L ($)</th>
                        <th>Time</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for _, row in metrics['top_trades'].iterrows():
                pnl_class = 'positive' if row['pnl'] >= 0 else 'negative'
                html_template += f"""
                        <tr>
                            <td>{row['trade_id']}</td>
                            <td>{row['trader_id']}</td>
                            <td>{row['symbol']}</td>
                            <td>{row['side']}</td>
                            <td>{row['quantity']:,}</td>
                            <td>${row['price']:.2f}</td>
                            <td class="{pnl_class}">${row['pnl']:,.0f}</td>
                            <td>{row['trade_time'].strftime('%H:%M:%S')}</td>
                        </tr>
                """
            
            html_template += """
                </tbody>
            </table>
            """
        
        html_template += """
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #6b7280;">
                <p>Generated by DataFit on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
                <p>This report contains confidential trading information.</p>
            </div>
        </body>
        </html>
        """
        
        return html_template