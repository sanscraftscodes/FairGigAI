import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.ai import router as ai_router
from app.services import ai_service
from app.services.llm_explainability_service import build_prompt_payload


def make_prompt_data():
    return build_prompt_payload(
        task={"task_id": "TASK-1", "task_type": "Delivery"},
        selected_worker={
            "worker_id": "WORKER-1",
            "vehicle_type": "bike",
            "distance_km": 2.0,
            "predicted_success": 0.8,
            "efficiency": 0.7,
            "opportunity_credit": 0.5,
            "workload_pressure": 0.2,
            "current_workload_hours": 10.0,
        },
        runner_up=None,
        policy="WAFR",
        lambda_val=0.08,
    )


class AIServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        ai_service._configured_state = None
        ai_service._last_available = None

    async def test_missing_key_uses_offline_explanation(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}), patch.object(
            ai_service, "_create_gemini_model"
        ) as create_model:
            result = await ai_service.generate_agent_explanation(make_prompt_data())

        create_model.assert_not_called()
        self.assertEqual(result["provider"], "offline")
        self.assertEqual(result["mode"], "offline")
        self.assertTrue(result["fallback_used"])
        self.assertIn("WORKER-1", result["explanation_markdown"])

    async def test_gemini_success_returns_online_explanation(self):
        response = type(
            "GeminiResponse",
            (),
            {
                "text": (
                    "## 1. Executive Allocation Summary\nWorker selected.\n"
                    "## 2. Mathematical Score Decomposition\nScore details.\n"
                    "## 3. Runner-Up Comparative Analysis\nNo runner-up.\n"
                    "## 4. UN SDG 8 Alignment & Ethical Audit\nFairness details."
                )
            },
        )()
        model = type(
            "GeminiModel",
            (),
            {"generate_content_async": AsyncMock(return_value=response)},
        )()
        test_key = "test-gemini-secret"
        with patch.dict(os.environ, {"GEMINI_API_KEY": test_key}), patch.object(
            ai_service, "_create_gemini_model", return_value=model
        ) as create_model:
            result = await ai_service.generate_agent_explanation(make_prompt_data())
            status = ai_service.get_ai_status()

        create_model.assert_called_once_with(test_key)
        self.assertEqual(result["provider"], "gemini")
        self.assertEqual(result["mode"], "online")
        self.assertFalse(result["fallback_used"])
        self.assertNotIn(test_key, repr(result))
        self.assertTrue(status["available"])

    async def test_gemini_error_uses_fallback_without_leaking_error(self):
        test_key = "test-gemini-secret"
        model = type(
            "GeminiModel",
            (),
            {"generate_content_async": AsyncMock(side_effect=RuntimeError(test_key))},
        )()
        with patch.dict(os.environ, {"GEMINI_API_KEY": test_key}), patch.object(
            ai_service, "_create_gemini_model", return_value=model
        ):
            result = await ai_service.generate_agent_explanation(make_prompt_data())
            status = ai_service.get_ai_status()

            self.assertEqual(status["mode"], "fallback")
            self.assertFalse(status["available"])
            self.assertNotIn(test_key, repr(status))

        self.assertEqual(result["provider"], "offline")
        self.assertTrue(result["fallback_used"])
        self.assertNotIn(test_key, repr(result))

    async def test_gemini_timeout_uses_offline_fallback(self):
        async def delayed_response(_prompt):
            await asyncio.sleep(0.05)

        model = SimpleNamespace(generate_content_async=delayed_response)
        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "test-gemini-secret"}),
            patch.object(ai_service, "_create_gemini_model", return_value=model),
            patch.object(ai_service, "GEMINI_TIMEOUT_SECONDS", 0.001),
        ):
            result = await ai_service.generate_agent_explanation(make_prompt_data())

        self.assertEqual(result["provider"], "offline")
        self.assertTrue(result["fallback_used"])

    async def test_status_does_not_make_provider_request(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-gemini-secret"}), patch.object(
            ai_service, "_create_gemini_model"
        ) as create_model:
            status = ai_service.get_ai_status()

        create_model.assert_not_called()
        self.assertEqual(status["mode"], "configured")
        self.assertFalse(status["available"])
        self.assertTrue(status["fallback_enabled"])

    def test_ai_status_endpoint_returns_safe_status(self):
        app = FastAPI()
        app.include_router(ai_router, prefix="/api")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-gemini-secret"}):
            response = TestClient(app).get("/api/ai/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "configured")
        self.assertTrue(response.json()["fallback_enabled"])
        self.assertNotIn("test-gemini-secret", response.text)


if __name__ == "__main__":
    unittest.main()
