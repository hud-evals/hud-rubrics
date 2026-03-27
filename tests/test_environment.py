"""Tests for the SEC EDGAR rubrics environment."""


class TestCore:
    def test_health(self, client):
        assert client.get("/health").status_code == 200

    def test_setup_resets_state(self, client):
        # Submit an answer to create state
        client.post("/answer", json={"final_answer": "test answer"})
        # Reset via setup
        client.post("/setup")
        # Verify state was cleared by checking evaluate returns no answer
        data = client.post("/evaluate", json={"rubric": [{"requirement": "x", "weight": 1}]}).json()
        assert "No answer submitted" in data["content"]


class TestAnswerAndEvaluate:
    def test_submit_answer(self, client):
        resp = client.post("/answer", json={"final_answer": "Revenue was $394B"})
        assert resp.status_code == 200

    def test_evaluate_without_answer(self, client):
        data = client.post("/evaluate", json={"rubric": [{"requirement": "x", "weight": 1}]}).json()
        assert data["reward"] == 0.0
        assert data["done"] is False
        assert "No answer submitted" in data["content"]


class TestEdgar:
    def test_search_company(self, client):
        data = client.post("/search_company", json={"query": "AAPL"}).json()
        assert len(data) > 0
        assert data[0]["ticker"] == "AAPL"

    def test_get_filings(self, client):
        data = client.post("/get_filings", json={"ticker": "AAPL", "limit": 5}).json()
        assert len(data) > 0
        assert "form_type" in data[0]
        assert "filing_date" in data[0]


class TestWebTools:
    def test_web_search(self, client):
        resp = client.post("/web_search", json={"query": "Apple revenue 2024", "max_results": 1})
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) > 0

    def test_web_fetch(self, client):
        resp = client.post("/web_fetch", json={"url": "https://www.sec.gov"})
        assert resp.status_code == 200
        result = resp.json()
        assert "content" in result
