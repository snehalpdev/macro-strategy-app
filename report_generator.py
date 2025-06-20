import pdfkit
import base64
import matplotlib.pyplot as plt
from datetime import datetime
import os

def save_equity_chart(df):
    plt.figure(figsize=(10, 4))
    plt.plot(df["timestamp"], df["strategy_equity"], label="Strategy", color="#00cc88", linewidth=2)
    plt.plot(df["timestamp"], df["buy_hold"], label="Buy & Hold", color="#888", linestyle="--")
    plt.title("Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    chart_path = "equity_chart.png"
    plt.savefig(chart_path)
    plt.close()
    return chart_path

def create_report_html(metrics, latest_signal, recent_signals, chart_path):
    logo_section = '<img src="logo.png" width="120"/>' if os.path.exists("logo.png") else ""

    html = f"""
    <html><head><style>
        body {{ font-family: 'Segoe UI', sans-serif; color: #333; margin: 40px; }}
        h1, h2 {{ color: #00cc88; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background: #f5f5f5; }}
        ul {{ line-height: 1.6; }}
    </style></head><body>
        {logo_section}
        <h1>Macro Strategy Report</h1>
        <p><em>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}</em></p>
        <hr/>

        <h2>📌 Latest Signal</h2>
        <ul>
            <li><strong>Ticker:</strong> {latest_signal['ticker']}</li>
            <li><strong>Signal:</strong> {latest_signal['signal']} ({latest_signal['regime']})</li>
            <li><strong>Confidence:</strong> {latest_signal['confidence']:.2f}%</li>
            <li><strong>Timestamp:</strong> {latest_signal['timestamp']}</li>
        </ul>

        <h2>🧮 Performance Metrics</h2>
        <ul>
            {''.join(f"<li><strong>{k}:</strong> {v}</li>" for k, v in metrics.items())}
        </ul>

        <h2>📈 Equity Curve</h2>
        <img src="{chart_path}" width="650"/>

        <h2>🕒 Recent Signals</h2>
        {recent_signals.to_html(index=False)}
    </body></html>
    """
    return html

def generate_pdf_report(metrics, latest_signal, recent_signals, df):
    chart_path = save_equity_chart(df)
    html = create_report_html(metrics, latest_signal, recent_signals, chart_path)
    pdfkit.from_string(html, "macro_strategy_report.pdf")
    return "macro_strategy_report.pdf"

def streamlit_download_button(filename):
    with open(filename, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📥 Download Strategy Report</a>'