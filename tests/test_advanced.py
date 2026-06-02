import pytest
from pathlib import Path

from codec.session.diff_engine import DiffEngine
from codec.session.cost_tracker import CostTracker
from codec.session.context_manager import ContextManager, estimate_tokens
from codec.tools import git_tools
from codec.tools import differ
from codec.tools import plan_tools
from codec.tools import testing
from codec.tools import web
from codec.modules.state_manager import StateManager


class TestDiffEngine:
    def test_compute_edit_diff(self, tmp_path):
        de = DiffEngine(str(tmp_path))
        f = tmp_path / "f.txt"
        f.write_text("hello world")
        diff = de.compute_edit_diff(str(f), "hello world", "hello there")
        assert "+hello there" in diff
        assert "-hello world" in diff

    def test_compute_file_diff_new_file(self, tmp_path):
        de = DiffEngine(str(tmp_path))
        info = de.compute_file_diff_before_after("new.py", "print('hi')")
        assert info["file"] == "new.py"
        assert info["before"] == ""
        assert info["after"] == "print('hi')"

    def test_compute_file_diff_existing(self, tmp_path):
        de = DiffEngine(str(tmp_path))
        f = tmp_path / "f.py"
        f.write_text("old")
        info = de.compute_file_diff_before_after(str(f), "new")
        assert info["lines_added"] >= 1
        assert info["lines_removed"] >= 1


class TestCostTracker:
    def test_record_and_summary(self, tmp_path):
        ct = CostTracker(str(tmp_path / "costs"))
        ct.record_call("gpt-4o", 1000, 200)
        s = ct.get_summary()
        assert s["total_prompt_tokens"] == 1000
        assert s["total_completion_tokens"] == 200
        assert s["total_cost"] > 0

    def test_accumulation(self, tmp_path):
        ct = CostTracker(str(tmp_path / "costs"))
        ct.record_call("gpt-4o", 1000, 100)
        ct.record_call("gpt-4o", 500, 50)
        s = ct.get_summary()
        assert s["total_prompt_tokens"] == 1500
        assert s["total_completion_tokens"] == 150

    def test_free_model(self, tmp_path):
        ct = CostTracker(str(tmp_path / "costs"))
        ct.record_call("ollama/llama3", 1000, 500)
        s = ct.get_summary()
        assert s["total_cost"] == 0.0

    def test_persistence(self, tmp_path):
        d = tmp_path / "costs"
        ct1 = CostTracker(str(d))
        ct1.record_call("gpt-4o", 100, 20)
        ct2 = CostTracker(str(d))
        s = ct2.get_summary()
        assert s["total_prompt_tokens"] == 100


class TestContextManager:
    def test_estimate_tokens(self):
        t = estimate_tokens("hello world")
        assert t > 0

    def test_limit_default(self):
        cm = ContextManager("gpt-4o")
        assert "128,000" in cm.format_limit_info()

    def test_limit_ollama(self):
        cm = ContextManager("ollama/llama3")
        assert "8,192" in cm.format_limit_info()

    def test_would_exceed(self):
        cm = ContextManager("llama3")
        huge = "x" * 50000
        assert cm.would_exceed_limit([{"role": "user", "content": huge}], "")

    def test_get_compressed_context(self):
        cm = ContextManager("gpt-4o")
        history = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
        compressed = cm.get_compressed_context(history)
        assert len(compressed) <= 11


class TestGitTools:
    @pytest.mark.asyncio
    async def test_git_status(self, tmp_path):
        result = await git_tools.git_status(project_dir=str(tmp_path))
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_git_branch(self, tmp_path):
        result = await git_tools.git_branch(project_dir=str(tmp_path))
        assert isinstance(result, str)


class TestPlanTools:
    def test_set_plan(self, tmp_path):
        sm = StateManager(str(tmp_path / "sess"))
        plan_tools.set_state_manager(sm)
        steps = [{"description": "step 1", "status": "pending", "result": None},
                 {"description": "step 2", "status": "pending", "result": None}]
        sm.set_plan(steps, "test goal")
        summary = sm.get_plan_summary()
        assert "test goal" in summary
        assert "step 1" in summary
        assert "step 2" in summary

    def test_update_plan_step(self, tmp_path):
        sm = StateManager(str(tmp_path / "sess"))
        plan_tools.set_state_manager(sm)
        steps = [{"description": "s1", "status": "pending", "result": None}]
        sm.set_plan(steps, "g")
        sm.update_plan_step(0, "completed", "done")
        assert sm.active_plan[0]["status"] == "completed"
        assert sm.active_plan[0]["result"] == "done"

    @pytest.mark.asyncio
    async def test_create_plan_tool(self, tmp_path):
        sm = StateManager(str(tmp_path / "sess"))
        plan_tools.set_state_manager(sm)
        result = await plan_tools.create_plan("goal", ["a", "b"], project_dir=str(tmp_path))
        assert "Plan created" in result
        assert sm.plan_goal == "goal"
        assert len(sm.active_plan) == 2

    @pytest.mark.asyncio
    async def test_get_plan_tool(self, tmp_path):
        sm = StateManager(str(tmp_path / "sess"))
        plan_tools.set_state_manager(sm)
        r = await plan_tools.get_plan(project_dir=str(tmp_path))
        assert r == "No active plan."

    @pytest.mark.asyncio
    async def test_update_plan_step_tool(self, tmp_path):
        sm = StateManager(str(tmp_path / "sess"))
        plan_tools.set_state_manager(sm)
        sm.set_plan([{"description": "x", "status": "pending", "result": None}], "g")
        r = await plan_tools.update_plan_step(0, "completed", "ok", project_dir=str(tmp_path))
        assert "marked as completed" in r


class TestTestingTools:
    @pytest.mark.asyncio
    async def test_detect_test_command(self, tmp_path):
        result = await testing.detect_test_command(project_dir=str(tmp_path))
        assert "No test command" in result

    @pytest.mark.asyncio
    async def test_detect_test_command_python(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.pytest]")
        result = await testing.detect_test_command(project_dir=str(tmp_path))
        assert "pytest" in result

    @pytest.mark.asyncio
    async def test_run_tests_no_command(self, tmp_path):
        result = await testing.run_tests(project_dir=str(tmp_path))
        assert "No test command" in result

    @pytest.mark.asyncio
    async def test_run_tests_with_command(self, tmp_path):
        result = await testing.run_tests(command="echo test_ok", project_dir=str(tmp_path))
        assert "test_ok" in result


class TestWebTools:
    @pytest.mark.asyncio
    async def test_web_fetch_bad_url(self):
        result = await web.web_fetch("http://nonexistent.invalid", timeout=2)
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_web_search_bad_query(self):
        result = await web.web_search("xyznonexistent_12345_test")
        assert isinstance(result, str)


class TestStateManagerPlan:
    def test_plan_persistence(self, tmp_path):
        d = tmp_path / "sess"
        sm1 = StateManager(str(d))
        sm1.set_plan([{"description": "persist", "status": "pending", "result": None}], "test")
        sm2 = StateManager(str(d))
        assert sm2.plan_goal == "test"
        assert len(sm2.active_plan) == 1

    def test_get_plan_summary_empty(self, tmp_path):
        sm = StateManager(str(tmp_path / "sess"))
        assert sm.get_plan_summary() == ""

    def test_clear_history_clears_plan(self, tmp_path):
        sm = StateManager(str(tmp_path / "sess"))
        sm.set_plan([{"description": "x", "status": "pending", "result": None}], "g")
        sm.clear_history()
        assert sm.active_plan == []
        assert sm.plan_goal == ""

    def test_update_plan_step_invalid_index(self, tmp_path):
        sm = StateManager(str(tmp_path / "sess"))
        sm.set_plan([{"description": "x", "status": "pending", "result": None}], "g")
        sm.update_plan_step(5, "completed")
        assert sm.active_plan[0]["status"] == "pending"


class TestDiffer:
    @pytest.mark.asyncio
    async def test_diff_file(self, tmp_path):
        result = await differ.diff_file("test.py", "new content", project_dir=str(tmp_path))
        assert "test.py" in result or "(new file)" in result or "(no changes)" in result

    @pytest.mark.asyncio
    async def test_edit_with_diff_no_change(self, tmp_path):
        f = tmp_path / "t.txt"
        f.write_text("same")
        result = await differ.edit_file_with_diff("t.txt", "same", "different", project_dir=str(tmp_path))
        assert "Edited" in result or "Skipped" in result
