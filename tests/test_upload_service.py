import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from streamlit.testing.v1 import AppTest

from backend import upload_service
from backend import main as api
from backend.database_model import Base, User
from chatbot.rag_chatbot import SalesMitraChatbot


class UploadServiceTests(unittest.TestCase):
    def test_sales4_sidebar_upload_renders_without_streamlit_secrets(self):
        class Response:
            status_code = 200

            def __init__(self, body):
                self.body = body

            def json(self):
                return self.body

        def fake_get(url, *args, **kwargs):
            if url.endswith("/api/sales/summary"):
                return Response({"total_records": 0})
            if url.endswith("/api/sales"):
                return Response([])
            if url.endswith("/api/datasets"):
                return Response([])
            return Response({"status": "ok"})

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend" / "sales4.py"))
        app.session_state["user_logged_in"] = True
        app.session_state["user_id"] = 1
        app.session_state["user_email"] = "test@example.com"
        app.session_state["access_token"] = "test-token"
        with patch("requests.get", side_effect=fake_get):
            app.run(timeout=30)

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Choose a sales file" in str(widget.label) for widget in app.file_uploader))
        self.assertTrue(any("up to 40 MB" in widget.value for widget in app.caption))

    def test_sales4_product_cluster_uses_selected_uploaded_data(self):
        class Response:
            status_code = 200

            def __init__(self, body):
                self.body = body

            def json(self):
                return self.body

        rows = [
            {"product": "Tea", "region": "North", "branch": "Central", "sales_amount": 120},
            {"product": "Tea", "region": "South", "branch": "Harbor", "sales_amount": 80},
            {"product": "Coffee", "region": "North", "branch": "Central", "sales_amount": 200},
        ]

        def fake_get(url, *args, **kwargs):
            if url.endswith("/api/datasets"):
                return Response([{"id": 9, "name": "sales.csv", "row_count": len(rows), "columns": list(rows[0])}])
            if url.endswith("/api/datasets/9/rows"):
                return Response(rows)
            if url.endswith("/api/sales/summary"):
                return Response({"total_records": 0})
            if url.endswith("/api/sales"):
                return Response([])
            return Response({"status": "ok"})

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend" / "sales4.py"))
        app.session_state["user_logged_in"] = True
        app.session_state["user_id"] = 1
        app.session_state["user_email"] = "test@example.com"
        app.session_state["access_token"] = "test-token"
        app.session_state["active_dataset_id"] = 9
        app.session_state["page"] = "clusters"
        with patch("requests.get", side_effect=fake_get):
            app.run(timeout=30)

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any(widget.key == "sales4_cluster_product_9" for widget in app.selectbox))
        metrics = "\n".join(widget.label for widget in app.metric)
        self.assertIn("Best-selling region / place", metrics)

    def test_deployed_dashboard_shows_main_upload_and_floating_help(self):
        class Response:
            status_code = 200

            def __init__(self, body):
                self.body = body

            def json(self):
                return self.body

        def fake_get(url, *args, **kwargs):
            if url.endswith("/api/datasets") or url.endswith("/api/sales"):
                return Response([])
            if url.endswith("/api/sales/summary"):
                return Response({"total_records": 0, "total_sales": 0, "total_qty": 0, "avg_sales": 0})
            return Response({"status": "ok"})

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend" / "sample.py"))
        app.session_state["user_logged_in"] = True
        app.session_state["user_id"] = 1
        app.session_state["user_email"] = "test@example.com"
        app.session_state["access_token"] = "test-token"
        with patch("requests.get", side_effect=fake_get):
            app.run(timeout=30)

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Choose a sales file" in str(widget.label) for widget in app.file_uploader))
        self.assertTrue(any("Welcome to SalesMitra" in widget.value for widget in app.title))
        self.assertNotIn("🤖 AI Chatbot", app.radio[0].options)
        self.assertTrue(any("How may I help you?" in item.value for item in app.markdown))
        self.assertTrue(any("up to 40 MB" in item.value for item in app.caption))

    def test_upload_size_limit_is_above_10_mb(self):
        self.assertEqual(upload_service.MAX_UPLOAD_BYTES, 40 * 1024 * 1024)
        self.assertGreater(upload_service.MAX_UPLOAD_BYTES, 10 * 1024 * 1024)
        self.assertGreaterEqual(upload_service.MAX_ROWS, 54_321)

    def test_parse_csv_and_excel(self):
        csv_frame = upload_service.parse_upload("sales.csv", b"Product,Sales\nTea,12.5\nCoffee,8\n")
        self.assertEqual(list(csv_frame.columns), ["Product", "Sales"])
        self.assertEqual(len(csv_frame), 2)

        workbook = BytesIO()
        with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
            pd.DataFrame({"Product": ["Tea"], "Sales": [12.5]}).to_excel(writer, index=False)
            pd.DataFrame({"Product": ["Coffee"], "Sales": [8]}).to_excel(writer, index=False, sheet_name="Other")
        excel_frame = upload_service.parse_upload("sales.xlsx", workbook.getvalue())
        self.assertEqual(excel_frame.loc[0, "Product"], "Tea")
        self.assertEqual(float(excel_frame.loc[0, "Sales"]), 12.5)
        self.assertEqual(len(excel_frame), 2)
        self.assertIn("source_sheet", excel_frame.columns)

    def test_parse_one_column_csv_and_ignore_non_finite_totals(self):
        frame = upload_service.parse_upload("sales.csv", b"Sales\n12\n8\n")
        self.assertEqual(frame["Sales"].tolist(), [12, 8])
        stats = upload_service.dataset_summary(pd.DataFrame({"Sales": [12, float("inf"), 8]}))["numeric_stats"]
        self.assertEqual(stats["Sales"]["sum"], 20)

    def test_dataset_insight_uses_gemini_when_configured(self):
        captured = {}

        def fake_generate(prompt, **kwargs):
            captured["prompt"] = prompt
            return "Gemini sales analysis"

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}), patch.object(
            upload_service, "gemini_generate", side_effect=fake_generate
        ):
            answer = upload_service.gemini_dataset_insight(pd.DataFrame({"Revenue": [10, 20]}))

        self.assertEqual(answer, "Gemini sales analysis")
        self.assertIn('"sum": 30.0', captured["prompt"])

    def test_leaked_gemini_key_returns_rotation_instructions(self):
        class LeakedKeyResponse:
            status_code = 403

            def json(self):
                return {"error": {"message": "Your API key was reported as leaked. Please use another API key."}}

            def raise_for_status(self):
                import requests
                raise requests.HTTPError("403 Forbidden", response=self)

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}), patch.object(
            upload_service.requests, "post", return_value=LeakedKeyResponse()
        ):
            with self.assertRaises(Exception) as raised:
                upload_service.gemini_generate("test")

        self.assertIn("reported as leaked", raised.exception.detail)
        self.assertNotIn("test-key", raised.exception.detail)

    def test_platform_help_uses_grounded_gemini_rag(self):
        with patch("chatbot.rag_chatbot.gemini_rag_answer", return_value="Gemini grounded help"):
            result = SalesMitraChatbot(None, None).answer("Where do I upload sales data?")

        self.assertEqual(result["answer"], "Gemini grounded help")
        self.assertIn("Load CSV data", result["sources"])

    def test_chat_endpoint_answers_general_questions_without_database(self):
        with patch("chatbot.rag_chatbot.gemini_rag_answer", return_value="A clear answer from Gemini."), \
             patch("backend.main.get_db", side_effect=AssertionError("general help must not require the database")):
            response = TestClient(api.app).post(
                "/api/chatbot/query",
                json={"query": "What does the platform help me do?"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["answer"], "A clear answer from Gemini.")

    def test_chatbot_returns_useful_guidance_when_gemini_fails(self):
        from fastapi import HTTPException

        with patch(
            "chatbot.rag_chatbot.gemini_rag_answer",
            side_effect=HTTPException(status_code=504, detail="Gemini timed out"),
        ):
            result = SalesMitraChatbot(None, None).answer("Where do I upload sales data?")

        self.assertTrue(result["answer"].strip())
        self.assertIn("related SalesMitra guidance", result["answer"])
        self.assertIn("Upload sales data", result["answer"])

    def test_general_sales_questions_are_not_mistaken_for_database_queries(self):
        bot = SalesMitraChatbot(None, None)
        self.assertFalse(bot._asks_top_sales("What are the best strategies to improve sales?"))
        self.assertFalse(bot._asks_profit_projection("What is profit margin?"))

    def test_image_help_passes_image_to_gemini_rag(self):
        with patch("chatbot.rag_chatbot.gemini_rag_answer", return_value="I can see the upload error.") as rag:
            result = SalesMitraChatbot(None, None).answer(
                "What does this error mean?", image_bytes=b"image bytes", image_mime_type="image/jpeg"
            )

        self.assertEqual(result["intent"], "image_help")
        self.assertEqual(result["answer"], "I can see the upload error.")
        rag.assert_called_once()
        self.assertEqual(rag.call_args.kwargs["image_bytes"], b"image bytes")
        self.assertEqual(rag.call_args.kwargs["image_mime_type"], "image/jpeg")

    def test_gemini_timeout_returns_actionable_gateway_timeout(self):
        import requests
        from fastapi import HTTPException

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}), patch.object(
            upload_service.requests, "post", side_effect=requests.ReadTimeout("read timed out")
        ):
            with self.assertRaises(HTTPException) as raised:
                upload_service.gemini_generate("test")

        self.assertEqual(raised.exception.status_code, 504)
        self.assertIn("shorter question", raised.exception.detail)

    def test_upload_insight_is_rendered_on_sales_analytics_page(self):
        class Response:
            status_code = 200

            def __init__(self, body):
                self.body = body

            def json(self):
                return self.body

        def fake_get(url, *args, **kwargs):
            if url.endswith("/api/datasets") or url.endswith("/api/sales"):
                return Response([])
            if url.endswith("/api/sales/summary"):
                return Response({"total_records": 0, "total_sales": 0, "total_qty": 0, "avg_sales": 0})
            return Response({"status": "ok"})

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend" / "sample.py"))
        app.session_state["user_logged_in"] = True
        app.session_state["user_id"] = 1
        app.session_state["user_email"] = "test@example.com"
        app.session_state["access_token"] = "test-token"
        with patch("requests.get", side_effect=fake_get):
            app.run(timeout=30)
            app.radio[0].set_value("📊 Sales Analytics")
            app.session_state["last_upload_result"] = {
                "id": 1,
                "name": "sales.csv",
                "row_count": 2,
                "created": True,
                "insight": "Gemini generated a sales trend summary.",
            }
            app.run(timeout=30)

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Gemini generated a sales trend summary" in item.value for item in app.markdown))

    def test_uploaded_dataset_shows_actionable_data_quality_checks(self):
        class Response:
            status_code = 200

            def __init__(self, body):
                self.body = body

            def json(self):
                return self.body

        rows = [
            {"product": "Tea", "sales_amount": "not a number", "branch": None},
            {"product": "Tea", "sales_amount": "not a number", "branch": None},
        ]

        def fake_get(url, *args, **kwargs):
            if url.endswith("/api/datasets"):
                return Response([{"id": 7, "name": "sales.csv", "row_count": len(rows)}])
            if url.endswith("/api/datasets/7/rows"):
                return Response(rows)
            return Response([])

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend" / "sample.py"))
        app.session_state["user_logged_in"] = True
        app.session_state["user_id"] = 1
        app.session_state["user_email"] = "test@example.com"
        app.session_state["access_token"] = "test-token"
        app.session_state["active_dataset_id"] = 7
        with patch("requests.get", side_effect=fake_get):
            app.run(timeout=30)

        self.assertEqual(len(app.exception), 0)
        messages = "\n".join(widget.value for widget in app.markdown)
        self.assertIn("blank value(s)", messages)
        self.assertIn("exact duplicate row(s)", messages)
        self.assertIn("not numeric", messages)
        self.assertTrue(any(widget.label == "Open a saved analysis" for widget in app.selectbox))

    def test_latest_upload_stays_active_and_previous_analysis_reopens_its_own_data(self):
        class Response:
            status_code = 200

            def __init__(self, body):
                self.body = body

            def json(self):
                return self.body

        datasets = [
            {"id": 9, "name": "latest.csv", "row_count": 1, "columns": ["product", "sales_amount"]},
            {"id": 8, "name": "previous.csv", "row_count": 1, "columns": ["product", "sales_amount"]},
        ]
        rows_by_id = {
            9: [{"product": "Current product", "sales_amount": 900}],
            8: [{"product": "Previous product", "sales_amount": 100}],
        }

        def fake_get(url, *args, **kwargs):
            if url.endswith("/api/datasets"):
                return Response(datasets)
            if url.endswith("/api/datasets/9/rows"):
                return Response(rows_by_id[9])
            if url.endswith("/api/datasets/8/rows"):
                return Response(rows_by_id[8])
            if url.endswith("/api/sales/summary"):
                return Response({"total_records": 0})
            if url.endswith("/api/sales"):
                return Response([])
            return Response({"status": "ok"})

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend" / "sample.py"))
        app.session_state["user_logged_in"] = True
        app.session_state["user_id"] = 1
        app.session_state["user_email"] = "test@example.com"
        app.session_state["access_token"] = "test-token"
        # Simulate upload success with a stale selector value from an older file.
        app.session_state["active_dataset_id"] = 9
        app.session_state["active_dataset_selector"] = 8
        with patch("requests.get", side_effect=fake_get):
            app.run(timeout=30)
            self.assertEqual(app.session_state["active_dataset_id"], 9)
            self.assertTrue(any("latest.csv · 1 records" in item.value for item in app.caption))

            picker = next(widget for widget in app.selectbox if widget.key == "active_dataset_selector")
            picker.set_value(8)
            app.run(timeout=30)
            self.assertEqual(app.session_state["active_dataset_id"], 8)
            self.assertTrue(any("previous.csv · 1 records" in item.value for item in app.caption))

            app.radio[0].set_value("📊 Sales Analytics")
            app.run(timeout=30)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["active_dataset_id"], 8)
        self.assertTrue(any("previous.csv · 1 records" in item.value for item in app.caption))

    def test_uploaded_sales_analytics_offers_views_and_product_location_drilldown(self):
        class Response:
            status_code = 200

            def __init__(self, body):
                self.body = body

            def json(self):
                return self.body

        dates = pd.date_range("2024-01-01", periods=24, freq="MS")
        rows = [
            {
                "order_date": date.isoformat(),
                "sales_amount": float(100 + index * 7 + (index % 4) * 9),
                "quantity": 5 + index % 6,
                "product": "A" if index % 2 else "B",
                "region": "North" if index % 3 else "South",
                "branch": "Central" if index % 2 else "Riverside",
            }
            for index, date in enumerate(dates)
        ]

        def fake_get(url, *args, **kwargs):
            if url.endswith("/api/datasets"):
                return Response([{"id": 8, "name": "orders.csv", "row_count": len(rows), "columns": list(rows[0])}])
            if url.endswith("/api/datasets/8/rows"):
                return Response(rows)
            return Response([])

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend" / "sample.py"))
        app.session_state["user_logged_in"] = True
        app.session_state["user_id"] = 1
        app.session_state["user_email"] = "test@example.com"
        app.session_state["access_token"] = "test-token"
        app.session_state["active_dataset_id"] = 8
        with patch("requests.get", side_effect=fake_get):
            app.run(timeout=30)
            app.radio[0].set_value("📊 Sales Analytics")
            app.run(timeout=30)
            analysis_picker = next(widget for widget in app.selectbox if widget.key == "uploaded_analysis_8")
            self.assertIn("Product Clusters", analysis_picker.options)
            self.assertIn("ARIMA Forecast", analysis_picker.options)
            analysis_picker.set_value("Product Clusters")
            app.run(timeout=30)
            self.assertIn("Product and order clusters", "\n".join(widget.value for widget in app.subheader))
            cluster_metrics = "\n".join(widget.label for widget in app.metric)
            analysis_picker = next(widget for widget in app.selectbox if widget.key == "uploaded_analysis_8")
            analysis_picker.set_value("ARIMA Forecast")
            app.run(timeout=30)

        self.assertEqual(len(app.exception), 0)
        headings = "\n".join(widget.value for widget in app.subheader)
        self.assertIn("ARIMA sales forecast", headings)
        self.assertIn("Top-selling region / place", cluster_metrics)

    def test_uploaded_sales4_analysis_pages_all_render_on_uploaded_columns(self):
        class Response:
            status_code = 200

            def __init__(self, body):
                self.body = body

            def json(self):
                return self.body

        dates = pd.date_range("2023-01-01", periods=24, freq="MS")
        rows = [
            {
                "AcYr": f"{date.year}-{date.year + 1}",
                "MMYYYY": date.strftime("%Y-%m"),
                "ActAmt": 120 + index * 5,
                "SalesAmt": 125 + index * 5,
                "CNAmt": 4 + index % 3,
                "SalesQty": 2 + index % 5,
                "BrandName": "Tea" if index % 2 else "Coffee",
                "MKTType": "Drinks" if index % 2 else "Hot drinks",
                "Zone": "North" if index % 3 else "South",
                "BranchName": "Central" if index % 2 else "Harbor",
            }
            for index, date in enumerate(dates)
        ]

        def fake_get(url, *args, **kwargs):
            if url.endswith("/api/datasets"):
                return Response([{"id": 88, "name": "full-sales.csv", "row_count": len(rows), "columns": list(rows[0])}])
            if url.endswith("/api/datasets/88/rows"):
                return Response(rows)
            return Response([])

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend" / "sample.py"))
        app.session_state["user_logged_in"] = True
        app.session_state["user_id"] = 1
        app.session_state["user_email"] = "test@example.com"
        app.session_state["access_token"] = "test-token"
        app.session_state["active_dataset_id"] = 88
        with patch("requests.get", side_effect=fake_get):
            app.run(timeout=30)
            app.radio[0].set_value("📊 Sales Analytics")
            app.run(timeout=30)
            analysis = next(widget for widget in app.selectbox if widget.key == "uploaded_analysis_88")
            for choice in analysis.options:
                analysis = next(widget for widget in app.selectbox if widget.key == "uploaded_analysis_88")
                analysis.set_value(choice)
                app.run(timeout=30)
                self.assertEqual(len(app.exception), 0, f"{choice} failed: {app.exception}")

    def test_floating_chat_keeps_the_ai_response_visible(self):
        class GetResponse:
            status_code = 200

            def json(self):
                return []

        class ChatResponse:
            status_code = 200

            def json(self):
                return {"answer": "SalesMitra turns your sales files into summaries, charts, and forecasts."}

        def fake_get(url, *args, **kwargs):
            if url.endswith("/api/datasets"):
                return GetResponse()
            if url.endswith("/api/sales"):
                return GetResponse()
            if url.endswith("/api/sales/summary"):
                return type("SummaryResponse", (), {"status_code": 200, "json": lambda self: {"total_records": 0}})()
            return type("HealthResponse", (), {"status_code": 200, "json": lambda self: {"status": "ok"}})()

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend" / "sample.py"))
        app.session_state["user_logged_in"] = True
        app.session_state["user_id"] = 1
        app.session_state["user_email"] = "test@example.com"
        app.session_state["access_token"] = "test-token"
        with patch("requests.get", side_effect=fake_get), patch("requests.post", return_value=ChatResponse()):
            app.run(timeout=30)
            question = next(widget for widget in app.text_input if widget.key == "floating_chat_question")
            question.set_value("What does SalesMitra do?")
            app.run(timeout=30)
            send = next(widget for widget in app.button if widget.label == "Send to SalesMitra AI")
            send.click()
            app.run(timeout=30)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["chat_history"][-1]["role"], "assistant")
        self.assertIn("turns your sales files into summaries", app.session_state["chat_history"][-1]["content"])
        self.assertTrue(any("turns your sales files into summaries" in item.value for item in app.markdown))

    def test_cluster_chart_uses_fields_returned_by_backend(self):
        class Response:
            status_code = 200

            def __init__(self, body):
                self.body = body

            def json(self):
                return self.body

        sales_rows = [{
            "id": 1, "ac_yr": "2025", "mmyyyy": "2025-01", "zone": "North",
            "branch_name": "Delhi", "brand_name": "Tea", "sales_qty": 10, "sales_amt": 100,
        }]
        cluster_result = {
            "profit_margin_pct": 20,
            "clusters": [{"cluster": "High Sales", "count": 1, "total_sales": 100, "projected_next_year_profit": 20}],
            "records": [{
                "brand_name": "Tea", "zone": "North", "branch_name": "Delhi",
                "total_sales": 100, "projected_next_year_profit": 20, "cluster": "High Sales",
            }],
        }

        def fake_get(url, *args, **kwargs):
            if url.endswith("/api/datasets"):
                return Response([])
            if url.endswith("/api/sales"):
                return Response(sales_rows)
            if url.endswith("/api/analytics/product-location-clusters"):
                return Response(cluster_result)
            if url.endswith("/api/sales/summary"):
                return Response({"total_records": 1, "total_sales": 100, "total_qty": 10, "avg_sales": 100})
            return Response({"status": "ok"})

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend" / "sample.py"))
        app.session_state["user_logged_in"] = True
        app.session_state["user_id"] = 1
        app.session_state["user_email"] = "test@example.com"
        app.session_state["access_token"] = "test-token"
        with patch("requests.get", side_effect=fake_get):
            app.run(timeout=30)
            app.radio[0].set_value("📊 Sales Analytics")
            app.run(timeout=30)

        self.assertEqual(len(app.exception), 0)

    def test_pdf_table_extraction_uses_gemini_structured_rows(self):
        old_generate = upload_service.gemini_generate
        upload_service.gemini_generate = lambda prompt, **kwargs: '{"columns":["Product","Sales"],"rows":[["Tea",12.5]]}'
        try:
            pdf_frame = upload_service.parse_upload("sales.pdf", b"%PDF-test-document")
            self.assertEqual(pdf_frame.to_dict(orient="records"), [{"Product": "Tea", "Sales": 12.5}])
        finally:
            upload_service.gemini_generate = old_generate

    def test_exact_repeat_reuses_the_existing_dynamic_table(self):
        test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(test_engine)
        session = sessionmaker(bind=test_engine)()
        old_engine = upload_service.engine
        upload_service.engine = test_engine
        try:
            user = User(email="upload-test@example.com", full_name="Test", password="test")
            session.add(user)
            session.commit()
            content = b"Product,Sales\nTea,12.5\nCoffee,8\n"
            frame = upload_service.parse_upload("sales.csv", content)
            first, created = upload_service.save_dataset(session, user.id, "sales.csv", content, frame)
            second, duplicate_created = upload_service.save_dataset(session, user.id, "copy.csv", content, frame)

            dynamic_tables = [name for name in inspect(test_engine).get_table_names() if name.startswith("upload_")]
            self.assertTrue(created)
            self.assertFalse(duplicate_created)
            self.assertEqual(first.id, second.id)
            self.assertEqual(dynamic_tables, [first.table_name])
            self.assertEqual(upload_service.dataset_frame(session, first).to_dict(orient="records"),
                             [{"Product": "Tea", "Sales": "12.5"}, {"Product": "Coffee", "Sales": "8.0"}])
        finally:
            upload_service.engine = old_engine
            session.close()
            test_engine.dispose()

    def test_upload_route_reuses_duplicate_and_is_user_scoped(self):
        test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(test_engine)
        test_session_factory = sessionmaker(bind=test_engine)
        old_engine = upload_service.engine
        old_insight = api.gemini_dataset_insight
        upload_service.engine = test_engine
        api.gemini_dataset_insight = lambda frame: "Test insight"

        def override_get_db():
            session = test_session_factory()
            try:
                yield session
            finally:
                session.close()

        api.app.dependency_overrides[api.get_db] = override_get_db
        session = test_session_factory()
        user = User(email="route-test@example.com", full_name="Test", password="test")
        other_user = User(email="other-test@example.com", full_name="Other", password="test")
        session.add_all([user, other_user])
        session.commit()
        owner_headers = {"Authorization": f"Bearer {api._issue_session_token(user.id)}"}
        other_headers = {"Authorization": f"Bearer {api._issue_session_token(other_user.id)}"}
        content = b"Product,Sales\nTea,12.5\nCoffee,8\n"
        try:
            client = TestClient(api.app)
            first = client.post("/api/datasets/upload", headers=owner_headers,
                                files={"file": ("sales.csv", content, "text/csv")})
            repeated = client.post("/api/datasets/upload", headers=owner_headers,
                                   files={"file": ("copy.csv", content, "text/csv")})
            self.assertEqual(first.status_code, 200, first.text)
            self.assertTrue(first.json()["created"])
            self.assertEqual(repeated.status_code, 200, repeated.text)
            self.assertFalse(repeated.json()["created"])
            self.assertEqual(first.json()["id"], repeated.json()["id"])
            rows = client.get(f"/api/datasets/{first.json()['id']}/rows", headers=owner_headers)
            forbidden = client.get(f"/api/datasets/{first.json()['id']}/rows", headers=other_headers)
            self.assertEqual(rows.status_code, 200)
            self.assertEqual(len(rows.json()), 2)
            self.assertEqual(forbidden.status_code, 404)
        finally:
            api.app.dependency_overrides.clear()
            upload_service.engine = old_engine
            api.gemini_dataset_insight = old_insight
            session.close()
            test_engine.dispose()


if __name__ == "__main__":
    unittest.main()
