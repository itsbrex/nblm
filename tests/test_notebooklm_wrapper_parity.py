import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import sys

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "scripts"))
sys.path.insert(0, str(repo_root))

import scripts.notebooklm_wrapper as wrapper_module


class WrapperParityTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dirs = []

    def _build_wrapper(self):
        tmp = tempfile.TemporaryDirectory()
        self._tmp_dirs.append(tmp)
        wrapper = wrapper_module.NotebookLMWrapper(auth_file=Path(tmp.name) / "auth.json")

        async def passthrough(coro_func, max_retries=1):
            return await coro_func()

        wrapper._with_retry = passthrough
        wrapper._tmp_dir = tmp
        return wrapper

    def tearDown(self):
        for tmp in self._tmp_dirs:
            tmp.cleanup()

    def test_query_with_conversation_and_sources(self):
        wrapper = self._build_wrapper()
        response = SimpleNamespace(
            answer="ok",
            references=[{"id": "r1"}],
            conversation_id="conv-1",
            turn_number=2,
            is_follow_up=True,
        )
        wrapper._client = SimpleNamespace(chat=SimpleNamespace(ask=mock.AsyncMock(return_value=response)))

        result = asyncio.run(
            wrapper.query(
                notebook_id="nb1",
                message="hello",
                source_ids=["s1"],
                conversation_id="conv-0",
            )
        )

        self.assertEqual(result["text"], "ok")
        self.assertEqual(result["conversation_id"], "conv-1")
        self.assertEqual(result["turn_number"], 2)
        self.assertTrue(result["is_follow_up"])

    def test_download_quiz_passes_output_format(self):
        wrapper = self._build_wrapper()
        download_quiz = mock.AsyncMock(return_value=Path("/tmp/quiz.md"))
        wrapper._client = SimpleNamespace(
            artifacts=SimpleNamespace(
                download_audio=mock.AsyncMock(),
                download_video=mock.AsyncMock(),
                download_slide_deck=mock.AsyncMock(),
                download_infographic=mock.AsyncMock(),
                download_report=mock.AsyncMock(),
                download_mind_map=mock.AsyncMock(),
                download_data_table=mock.AsyncMock(),
                download_quiz=download_quiz,
                download_flashcards=mock.AsyncMock(),
            )
        )

        result = asyncio.run(
            wrapper.download_artifact(
                notebook_id="nb1",
                artifact_id="a1",
                output_path="quiz.md",
                artifact_type="quiz",
                output_format="markdown",
            )
        )

        self.assertEqual(result, "/tmp/quiz.md")
        download_quiz.assert_awaited_once_with("nb1", "quiz.md", artifact_id="a1", output_format="markdown")

    def test_research_import_with_indices(self):
        wrapper = self._build_wrapper()
        poll = mock.AsyncMock(return_value={
            "status": "running",
            "sources": [{"title": "a"}, {"title": "b"}, {"title": "c"}],
        })
        import_sources = mock.AsyncMock(return_value=[{"source_id": "s2"}])
        wrapper._client = SimpleNamespace(research=SimpleNamespace(poll=poll, import_sources=import_sources))

        result = asyncio.run(
            wrapper.import_research_sources(
                notebook_id="nb1",
                task_id="task-1",
                source_indices=[1],
            )
        )

        self.assertEqual(result["imported_count"], 1)
        import_sources.assert_awaited_once_with(
            notebook_id="nb1",
            task_id="task-1",
            sources=[{"title": "b"}],
        )

    def test_export_artifact_extracts_url(self):
        wrapper = self._build_wrapper()
        export_result = {"nested": {"url": "https://docs.google.com/document/d/123"}}
        wrapper._client = SimpleNamespace(
            artifacts=SimpleNamespace(export=mock.AsyncMock(return_value=export_result))
        )

        fake_export_type = SimpleNamespace(DOCS="docs", SHEETS="sheets")
        with mock.patch("notebooklm.rpc.types.ExportType", fake_export_type):
            result = asyncio.run(
                wrapper.export_artifact(
                    notebook_id="nb1",
                    artifact_id="art1",
                    export_type="docs",
                    title="My Export",
                )
            )

        self.assertEqual(result["url"], "https://docs.google.com/document/d/123")
        self.assertEqual(result["artifact_id"], "art1")


if __name__ == "__main__":
    unittest.main()
