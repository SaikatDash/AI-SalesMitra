import math
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session


class SalesMitraChatbot:
    """Lightweight local RAG helper for sales questions and app navigation."""

    def __init__(self, db: Session, sales_model):
        self.db = db
        self.sales_model = sales_model
        self.knowledge_base = [
            {
                "title": "Load CSV data",
                "route": "CSV Import",
                "content": (
                    "To load medicine sales data, open a terminal in the project, run cd csv, "
                    "then run python main.py. The importer reads Mfg_Sales.csv and stores new rows "
                    "in the sales_data table."
                ),
            },
            {
                "title": "Start backend API",
                "route": "Backend",
                "content": (
                    "To start the FastAPI backend, run cd backend and python main.py. "
                    "The API serves login, sales, chatbot, clustering, and summary endpoints on port 8000."
                ),
            },
            {
                "title": "Open dashboard",
                "route": "Frontend",
                "content": (
                    "To open the Streamlit dashboard, run cd frontend and streamlit run sample.py. "
                    "After login, the dashboard shows sales charts, ARIMA forecast, and profit analysis."
                ),
            },
            {
                "title": "Sales analytics",
                "route": "Dashboard",
                "content": (
                    "Use the dashboard filters for zone, branch, brand, year, month, and quarter. "
                    "Charts compare zone sales, brand sales, active amount, quantity, and forecasted profit."
                ),
            },
            {
                "title": "Clustering endpoint",
                "route": "API",
                "content": (
                    "Use GET /api/analytics/product-location-clusters to find product-location combinations "
                    "with high sales and projected next-year profit."
                ),
            },
            {
                "title": "Dashboard home page",
                "route": "Dashboard",
                "content": (
                    "The home dashboard gives a quick business overview. It shows total sales, units sold, "
                    "average order value, record count, sales by zone, and top products. Use it first when "
                    "you want a fast summary before opening deeper analysis pages from the sidebar."
                ),
            },
            {
                "title": "Quarter vs Year option",
                "route": "Quarter vs Year",
                "content": (
                    "Quarter vs Year compares actual sales for a selected quarter across selected financial "
                    "years. Choose a quarter, select up to three financial years, then read the bar chart and "
                    "table to identify which year performed best for that quarter."
                ),
            },
            {
                "title": "Business Metrics option",
                "route": "Business Metrics",
                "content": (
                    "Business Metrics analyzes one financial year at a time. Select the financial year to "
                    "review sales, actual amount, credit notes, growth patterns, and month-wise performance. "
                    "Use this page when you need a broad year-level business health check."
                ),
            },
            {
                "title": "Branch Analysis option",
                "route": "Branch Analysis",
                "content": (
                    "Branch Analysis focuses on one branch for a selected financial year. Select a branch and "
                    "months to view month-wise branch sales, actual business, credit notes, and total sales. "
                    "Use it to understand which months helped or hurt a branch."
                ),
            },
            {
                "title": "Product Insights option",
                "route": "Product Insights",
                "content": (
                    "Product Insights studies product category performance. Select a financial year, product "
                    "category, months, and chart type. The page can show month-wise or yearly category sales "
                    "and export the detailed grid for reporting."
                ),
            },
            {
                "title": "Credit Notes option",
                "route": "Credit Notes",
                "content": (
                    "Credit Notes shows financial-year credit note analysis. Select up to three financial "
                    "years and use cumulative view when you want running totals. This helps identify returns, "
                    "deductions, or adjustments that reduce actual business."
                ),
            },
            {
                "title": "Branch Compare option",
                "route": "Branch Compare",
                "content": (
                    "Branch Compare compares one selected branch across multiple financial years. It shows "
                    "actual branch sales, branch credit note analysis, and total branch sales, with optional "
                    "cumulative view. Use it to see whether a branch is improving year over year."
                ),
            },
            {
                "title": "Category Compare option",
                "route": "Category Compare",
                "content": (
                    "Category Compare compares a product category within a selected branch across financial "
                    "years and months. Choose branch, years, product category, months, month-wise or yearly "
                    "analysis, cumulative view, and metric type to compare sales behavior in detail."
                ),
            },
            {
                "title": "Product Clusters option",
                "route": "Product Clusters",
                "content": (
                    "Product Clusters finds product-location combinations with strong sales. Set the expected "
                    "profit margin percentage, then review best product, best location, total sales, projected "
                    "next-year profit, product-location ranking, and Low, Medium, High sales cluster summary."
                ),
            },
            {
                "title": "ARIMA forecast option",
                "route": "ARIMA Forecast",
                "content": (
                    "ARIMA Forecast predicts future sales from historical sales. Open ARIMA Forecast in the "
                    "sidebar. The page checks stationarity, fits ARIMA(2,1,2), backtests the last 30 periods, "
                    "forecasts the next 48 weeks, shows RMSE and MAE errors, and estimates profit or loss "
                    "using the selected profit margin."
                ),
            },
            {
                "title": "What is ARIMA model",
                "route": "ARIMA Forecast",
                "content": (
                    "ARIMA means AutoRegressive Integrated Moving Average. AR uses past values, I means "
                    "differencing to make the trend stable, and MA uses past forecast errors. In this app "
                    "ARIMA(2,1,2) means p=2 past values, d=1 differencing step, and q=2 moving-average error "
                    "terms. It is useful for non-seasonal sales forecasting."
                ),
            },
            {
                "title": "What is SARIMA model",
                "route": "Forecasting",
                "content": (
                    "SARIMA means Seasonal ARIMA. It extends ARIMA by adding seasonal terms: SARIMA"
                    "(p,d,q)(P,D,Q,s). The first part models normal trend behavior, and the second part models "
                    "seasonal behavior. The s value is the seasonal cycle length, for example 12 for monthly "
                    "yearly seasonality or 52 for weekly yearly seasonality. Use SARIMA when sales repeat "
                    "seasonally, such as monthly medicine demand cycles."
                ),
            },
            {
                "title": "How to use forecasting results",
                "route": "ARIMA Forecast",
                "content": (
                    "To use forecasting results, first check stationarity and model errors. Lower RMSE and MAE "
                    "mean the model is closer to actual values. Review the complete forecast chart to compare "
                    "history, backtest, and future forecast. Then adjust Expected Profit Margin to estimate "
                    "future profit from forecasted sales."
                ),
            },
            {
                "title": "Stationarity test explained",
                "route": "ARIMA Forecast",
                "content": (
                    "The Augmented Dickey-Fuller stationarity test checks whether the sales pattern is stable "
                    "enough for ARIMA. A low p-value usually means the series is stationary. If it is not "
                    "stationary, differencing is used so the model learns changes instead of raw trending values."
                ),
            },
            {
                "title": "RMSE MAE and MAPE explained",
                "route": "ARIMA Forecast",
                "content": (
                    "RMSE, MAE, and MAPE are forecast error metrics. MAE is the average absolute error. RMSE "
                    "penalizes large mistakes more strongly. MAPE shows error as a percentage when actual "
                    "values are non-zero. Lower values generally mean better forecast quality."
                ),
            },
            {
                "title": "ACF PACF diagnostics explained",
                "route": "ARIMA Forecast",
                "content": (
                    "ACF and PACF plots help decide ARIMA parameters. ACF shows how current sales relate to "
                    "past lagged sales. PACF shows direct lag relationships after removing intermediate lags. "
                    "These plots help choose p and q values for forecasting models."
                ),
            },
            {
                "title": "Seasonal decomposition explained",
                "route": "ARIMA Forecast",
                "content": (
                    "Seasonal decomposition splits a time series into trend, seasonal pattern, and residual "
                    "noise. Trend shows long-term direction, seasonality shows repeating cycles, and residual "
                    "shows unexplained movement. If strong seasonality appears, SARIMA may be more suitable "
                    "than plain ARIMA."
                ),
            },
            {
                "title": "Export tables and reports",
                "route": "Dashboard",
                "content": (
                    "Most analysis pages show a detailed data grid with export controls. After applying filters, "
                    "review the table, use cumulative view if needed, and export the grid when you need to "
                    "share the result in reports or presentations."
                ),
            },
            {
                "title": "Suggested chatbot questions",
                "route": "Chatbot Guide",
                "content": (
                    "You can ask questions like: What is SARIMA? How does ARIMA Forecast work? How does every "
                    "sidebar option work? Which product has highest sales? Predict next-year profit. How do I "
                    "use Product Clusters? What do RMSE and MAE mean? How do I compare branches? How do I export "
                    "a report? How do I load CSV data? How do I start the backend and frontend?"
                ),
            },
        ]

    def answer(self, query: str) -> Dict[str, Any]:
        normalized = query.lower().strip()
        if not normalized:
            return self._question_guide_answer()

        if self._asks_question_guide(normalized):
            return self._question_guide_answer()

        if self._asks_all_options(normalized):
            return self._all_options_answer()

        if self._is_navigation_question(normalized):
            return self._navigation_answer(normalized)

        if self._asks_top_sales(normalized):
            return self._top_sales_answer()

        if self._asks_profit_projection(normalized):
            return self._profit_projection_answer()

        docs = self._retrieve(normalized)
        return {
            "answer": self._compose_rag_answer(query, docs),
            "intent": "rag_help",
            "sources": [doc["title"] for doc in docs],
            "navigation": [{"label": doc["route"], "detail": doc["content"]} for doc in docs[:3]],
        }

    def _retrieve(self, query: str, limit: int = 3) -> List[Dict[str, str]]:
        query_terms = Counter(self._tokens(query))
        scored = []
        for doc in self.knowledge_base:
            doc_terms = Counter(self._tokens(f"{doc['title']} {doc['route']} {doc['content']}"))
            score = sum(query_terms[token] * doc_terms[token] for token in query_terms)
            if score:
                scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        if not scored:
            return self.knowledge_base[:limit]
        return [doc for _, doc in scored[:limit]]

    def _compose_rag_answer(self, query: str, docs: List[Dict[str, str]]) -> str:
        points = [f"- {doc['title']}: {doc['content']}" for doc in docs[:3]]
        return "Based on the project knowledge I found:\n" + "\n".join(points)

    def _navigation_answer(self, query: str) -> Dict[str, Any]:
        docs = self._retrieve(query)
        steps = [f"{index}. {doc['content']}" for index, doc in enumerate(docs, start=1)]
        return {
            "answer": "Here is the best path:\n" + "\n".join(steps),
            "intent": "navigation",
            "sources": [doc["title"] for doc in docs],
            "navigation": [{"label": doc["route"], "detail": doc["content"]} for doc in docs],
        }

    def _all_options_answer(self) -> Dict[str, Any]:
        option_titles = {
            "Quarter vs Year option",
            "Business Metrics option",
            "Branch Analysis option",
            "Product Insights option",
            "Credit Notes option",
            "Branch Compare option",
            "Category Compare option",
            "Product Clusters option",
            "ARIMA forecast option",
        }
        docs = [doc for doc in self.knowledge_base if doc["title"] in option_titles]
        lines = [f"- {doc['route']}: {doc['content']}" for doc in docs]
        return {
            "answer": "Here is how each dashboard option works:\n" + "\n".join(lines),
            "intent": "all_options_help",
            "sources": [doc["title"] for doc in docs],
            "navigation": [{"label": doc["route"], "detail": doc["content"]} for doc in docs],
        }

    def _question_guide_answer(self) -> Dict[str, Any]:
        questions = [
            "What is SARIMA model?",
            "How does ARIMA Forecast work?",
            "How does every sidebar option work?",
            "Which product has highest sales?",
            "Predict next-year profit.",
            "How do I use Product Clusters?",
            "What do RMSE, MAE, and MAPE mean?",
            "How do I compare branches?",
            "How do I export a report?",
            "How do I load CSV data or start the backend?",
        ]
        return {
            "answer": "You can ask me questions like:\n" + "\n".join(f"- {question}" for question in questions),
            "intent": "question_guide",
            "sources": ["Suggested chatbot questions"],
            "navigation": [
                {
                    "label": "Chatbot Guide",
                    "detail": "Try asking about forecasting, dashboard options, sales insights, setup steps, or report exports.",
                }
            ],
        }

    def _top_sales_answer(self) -> Dict[str, Any]:
        SalesData = self.sales_model
        row = (
            self.db.query(
                SalesData.brand_name.label("brand_name"),
                SalesData.zone.label("zone"),
                SalesData.branch_name.label("branch_name"),
                func.sum(SalesData.sales_amt).label("total_sales"),
                func.sum(SalesData.sales_qty).label("total_qty"),
            )
            .group_by(SalesData.brand_name, SalesData.zone, SalesData.branch_name)
            .order_by(func.sum(SalesData.sales_amt).desc())
            .first()
        )
        if not row:
            return {
                "answer": "No sales data is available yet. Load the CSV first with cd csv and python main.py.",
                "intent": "top_sales",
                "sources": ["sales_data"],
                "navigation": [],
            }

        return {
            "answer": (
                f"The highest sales combination is {row.brand_name} in {row.branch_name}, {row.zone}. "
                f"Total sales amount is {float(row.total_sales or 0):,.2f} and quantity is "
                f"{float(row.total_qty or 0):,.2f}."
            ),
            "intent": "top_sales",
            "sources": ["sales_data"],
            "navigation": [{"label": "Dashboard", "detail": "Open the sales dashboard and filter by this brand/location."}],
            "data": {
                "brand_name": row.brand_name,
                "zone": row.zone,
                "branch_name": row.branch_name,
                "total_sales": float(row.total_sales or 0),
                "total_qty": float(row.total_qty or 0),
            },
        }

    def _profit_projection_answer(self) -> Dict[str, Any]:
        SalesData = self.sales_model
        rows = (
            self.db.query(
                SalesData.ac_yr.label("ac_yr"),
                func.sum(SalesData.act_amt).label("actual_sales"),
            )
            .group_by(SalesData.ac_yr)
            .order_by(SalesData.ac_yr)
            .all()
        )
        annual = [(row.ac_yr, float(row.actual_sales or 0)) for row in rows if row.ac_yr]
        if not annual:
            return {
                "answer": "I cannot project profit yet because no annual sales data is available.",
                "intent": "profit_projection",
                "sources": ["sales_data"],
                "navigation": [],
            }
        forecast = _forecast_next_value([value for _, value in annual])
        projected_profit = forecast * 0.20
        return {
            "answer": (
                f"Using the available yearly trend and a default 20% margin, next-year sales are projected "
                f"around {forecast:,.2f}, with estimated profit around {projected_profit:,.2f}."
            ),
            "intent": "profit_projection",
            "sources": ["sales_data"],
            "navigation": [{"label": "ARIMA Forecast", "detail": "Open the dashboard forecast section for visual profit analysis."}],
            "data": {
                "history": [{"ac_yr": ac_yr, "actual_sales": value} for ac_yr, value in annual],
                "projected_sales": forecast,
                "projected_profit": projected_profit,
                "profit_margin_pct": 20,
            },
        }

    @staticmethod
    def _tokens(text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    @staticmethod
    def _is_navigation_question(query: str) -> bool:
        words = {"open", "go", "navigate", "guide", "step", "steps", "where", "how", "run", "start"}
        return any(word in query for word in words)

    @staticmethod
    def _asks_all_options(query: str) -> bool:
        all_words = {"all", "every", "each"}
        option_words = {"option", "options", "menu", "menus", "sidebar", "page", "pages"}
        return any(word in query for word in all_words) and any(word in query for word in option_words)

    @staticmethod
    def _asks_question_guide(query: str) -> bool:
        guide_phrases = [
            "what can i ask",
            "what should i ask",
            "question guide",
            "sample question",
            "sample questions",
            "suggest question",
            "suggest questions",
            "help me ask",
            "guide me",
        ]
        return any(phrase in query for phrase in guide_phrases)

    @staticmethod
    def _asks_top_sales(query: str) -> bool:
        return any(word in query for word in ["highest", "top", "best"]) and "sales" in query

    @staticmethod
    def _asks_profit_projection(query: str) -> bool:
        return any(word in query for word in ["profit", "forecast", "predict", "projection", "next year"])


def product_location_cluster_analysis(db: Session, sales_model, profit_margin_pct: float = 20.0) -> Dict[str, Any]:
    SalesData = sales_model
    rows = (
        db.query(
            SalesData.brand_name.label("brand_name"),
            SalesData.zone.label("zone"),
            SalesData.branch_name.label("branch_name"),
            SalesData.ac_yr.label("ac_yr"),
            func.sum(SalesData.sales_amt).label("sales_amt"),
            func.sum(SalesData.sales_qty).label("sales_qty"),
            func.sum(SalesData.act_amt).label("act_amt"),
        )
        .group_by(SalesData.brand_name, SalesData.zone, SalesData.branch_name, SalesData.ac_yr)
        .all()
    )

    grouped: Dict[tuple, Dict[str, Any]] = {}
    for row in rows:
        key = (row.brand_name or "Unknown", row.zone or "Unknown", row.branch_name or "Unknown")
        item = grouped.setdefault(
            key,
            {
                "brand_name": key[0],
                "zone": key[1],
                "branch_name": key[2],
                "yearly_sales": [],
                "total_sales": 0.0,
                "total_qty": 0.0,
                "total_actual_sales": 0.0,
            },
        )
        sales_amt = float(row.sales_amt or 0)
        act_amt = float(row.act_amt if row.act_amt is not None else sales_amt)
        item["yearly_sales"].append({"ac_yr": row.ac_yr, "sales": act_amt})
        item["total_sales"] += sales_amt
        item["total_qty"] += float(row.sales_qty or 0)
        item["total_actual_sales"] += act_amt

    items = []
    for item in grouped.values():
        yearly = sorted(item["yearly_sales"], key=lambda value: value["ac_yr"] or "")
        projected_sales = _forecast_next_value([point["sales"] for point in yearly])
        item["yearly_sales"] = yearly
        item["projected_next_year_sales"] = projected_sales
        item["projected_next_year_profit"] = projected_sales * (profit_margin_pct / 100)
        items.append(item)

    if not items:
        return {
            "profit_margin_pct": profit_margin_pct,
            "best_product_location": None,
            "clusters": [],
            "records": [],
        }

    totals = sorted(item["total_sales"] for item in items)
    low_cut = _percentile(totals, 0.33)
    high_cut = _percentile(totals, 0.66)
    clusters = {"Low Sales": [], "Medium Sales": [], "High Sales": []}
    for item in items:
        if item["total_sales"] >= high_cut:
            cluster = "High Sales"
        elif item["total_sales"] >= low_cut:
            cluster = "Medium Sales"
        else:
            cluster = "Low Sales"
        item["cluster"] = cluster
        clusters[cluster].append(item)

    best = max(items, key=lambda value: value["total_sales"])
    cluster_summary = []
    for name, records in clusters.items():
        cluster_summary.append(
            {
                "cluster": name,
                "count": len(records),
                "total_sales": sum(record["total_sales"] for record in records),
                "projected_next_year_profit": sum(record["projected_next_year_profit"] for record in records),
            }
        )

    return {
        "profit_margin_pct": profit_margin_pct,
        "best_product_location": best,
        "clusters": cluster_summary,
        "records": sorted(items, key=lambda value: value["total_sales"], reverse=True),
        "generated_at": datetime.utcnow().isoformat(),
    }


def _forecast_next_value(values: List[float]) -> float:
    clean_values = [float(value or 0) for value in values]
    if not clean_values:
        return 0.0
    if len(clean_values) == 1:
        return max(clean_values[-1], 0.0)

    first = clean_values[0]
    last = clean_values[-1]
    if first > 0 and last > 0:
        years = max(len(clean_values) - 1, 1)
        growth = math.pow(last / first, 1 / years) - 1
    else:
        previous = clean_values[-2]
        growth = ((last - previous) / previous) if previous else 0.0
    growth = max(min(growth, 0.50), -0.50)
    return max(last * (1 + growth), 0.0)


def _percentile(values: List[float], percentile: float) -> float:
    if not values:
        return 0.0
    index = min(max(int(round((len(values) - 1) * percentile)), 0), len(values) - 1)
    return values[index]
