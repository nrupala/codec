import pytest
from pathlib import Path

from codec.modules.prompt_engineer import PromptEngineer
from codec.modules.resource_allocator import ResourceAllocator
from codec.modules.task_decomposer import TaskDecomposer
from codec.modules.scheduler import Scheduler
from codec.modules.action_definer import ActionDefiner
from codec.modules.state_manager import StateManager, CognitiveState, TaskState
from codec.modules.logger import ModuleLogger
from codec.tools.registry import registry
from codec.tools.file_ops import read_file, write_file, edit_file, list_files
from codec.tools.search import grep_search, glob_files
from codec.session.guardian import SessionGuardian
from codec.session.memory import SessionMemory
from codec.bridge.os_interface import OSInterface
from codec.bridge.code_interface import CodeInterface
import codec.tools.shell as _
import codec.tools.system_tools as _st


class TestPromptEngineer:
    def test_detect_intent_read(self):
        assert PromptEngineer().detect_intent("read src/main.py") == "read"

    def test_detect_intent_write(self):
        assert PromptEngineer().detect_intent("write a function") == "write"

    def test_detect_intent_search(self):
        assert PromptEngineer().detect_intent("search for TODO") == "search"

    def test_detect_intent_shell(self):
        assert PromptEngineer().detect_intent("run npm test") == "shell"

    def test_detect_intent_general(self):
        assert PromptEngineer().detect_intent("hello there") == "general"

    def test_system_prompt_includes_tools(self):
        pe = PromptEngineer()
        assert "read_file" in pe.system_prompt
        assert "write_file" in pe.system_prompt

    def test_extract_tool_calls(self):
        pe = PromptEngineer()
        text = 'Some text <tool_call>\n{"name":"read_file","arguments":{"path":"x.py"}}\n</tool_call> more'
        calls = pe.extract_tool_calls(text)
        assert len(calls) == 1
        assert calls[0]["name"] == "read_file"

    def test_strip_tool_calls(self):
        pe = PromptEngineer()
        text = 'Hello <tool_call>\n{"name":"x","arguments":{}}\n</tool_call> World'
        assert pe.strip_tool_calls(text) == "Hello  World"


class TestResourceAllocator:
    def test_allocate_tool(self):
        assert ResourceAllocator().allocate("read") == "tool"

    def test_allocate_llm(self):
        assert ResourceAllocator().allocate("question") == "llm"


class TestTaskDecomposer:
    def test_single_task(self):
        tasks = TaskDecomposer().decompose("read src/main.py")
        assert len(tasks) == 1

    def test_multi_task(self):
        tasks = TaskDecomposer().decompose("read x and edit y")
        assert len(tasks) >= 2


class TestActionDefiner:
    def test_define(self):
        a = ActionDefiner().define({"id": "t0", "type": "read", "description": "x"})
        assert a["type"] == "read_file"


class TestStateManager:
    def test_initial(self, tmp_path):
        sm = StateManager(str(tmp_path / ".c"))
        assert sm.cognitive_state == CognitiveState.IDLE

    def test_set_state(self, tmp_path):
        sm = StateManager(str(tmp_path / ".c"))
        sm.set_cognitive_state(CognitiveState.ANALYZING)
        assert sm.cognitive_state == CognitiveState.ANALYZING

    def test_task_lifecycle(self, tmp_path):
        sm = StateManager(str(tmp_path / ".c"))
        sm.add_task("t0", "do it")
        sm.update_task("t0", TaskState.COMPLETED, "ok")
        assert sm.tasks["t0"]["state"] == "completed"

    def test_history(self, tmp_path):
        sm = StateManager(str(tmp_path / ".c"))
        sm.add_to_history("user", "hi")
        assert len(sm.conversation_history) == 1


class TestLogger:
    def test_levels(self, tmp_path):
        ModuleLogger(str(tmp_path)).info("test")

    def test_llm_call(self, tmp_path):
        ModuleLogger(str(tmp_path)).log_llm_call("gpt4", 100, 50, 500)

    def test_tool_call(self, tmp_path):
        ModuleLogger(str(tmp_path)).log_tool_call("read", {}, 10, 5)


@pytest.mark.asyncio
class TestTools:
    async def test_read_write(self, tmp_path):
        await write_file("f.txt", "hello", project_dir=str(tmp_path))
        r = await read_file("f.txt", project_dir=str(tmp_path))
        assert "hello" in r

    async def test_edit(self, tmp_path):
        await write_file("f.txt", "aa bb", project_dir=str(tmp_path))
        await edit_file("f.txt", "aa", "xx", project_dir=str(tmp_path))
        r = await read_file("f.txt", project_dir=str(tmp_path))
        assert "xx bb" in r

    async def test_list(self, tmp_path):
        (tmp_path / "a.py").write_text("")
        (tmp_path / "b.py").write_text("")
        r = await list_files(pattern="*.py", project_dir=str(tmp_path))
        assert "a.py" in r

    async def test_grep(self, tmp_path):
        (tmp_path / "x.py").write_text("def foo(): pass")
        r = await grep_search("foo", project_dir=str(tmp_path))
        assert "x.py" in r

    async def test_glob(self, tmp_path):
        (tmp_path / "d.json").write_text("{}")
        r = await glob_files("*.json", project_dir=str(tmp_path))
        assert "d.json" in r

    async def test_project_summary(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def f(): pass")
        from codec.tools.system_tools import project_summary
        r = await project_summary(project_dir=str(tmp_path))
        assert "python" in r

    async def test_detect_language(self):
        from codec.tools.system_tools import detect_language
        r = await detect_language("test.py", project_dir=".")
        assert r == "python"

    async def test_registry_complete(self):
        tools = registry.list_tools()
        for required in ["read_file", "write_file", "edit_file",
                         "run_shell", "grep_search", "glob_files",
                         "project_summary", "detect_language",
                         "web_search", "create_plan", "run_tests"]:
            assert required in tools, f"Missing tool: {required}"
        assert len(tools) >= 22


class TestScheduler:
    @pytest.mark.asyncio
    async def test_single(self):
        async def ex(t):
            return {"id": t["id"]}
        r = await Scheduler().execute([{"id": "t0", "sequence": 0, "dependencies": []}], ex)
        assert len(r) == 1


class TestSessionGuardian:
    def test_allow_command(self):
        g = SessionGuardian(".")
        assert g.allow_command("rm -rf /") is not None
        assert g.allow_command("echo hello") is None
        assert g.allow_command("sudo rm") is not None

    def test_contain_path(self, tmp_path):
        g = SessionGuardian(str(tmp_path))
        result = g.contain_path("test.txt")
        assert "test.txt" in result

    def test_is_path_allowed(self, tmp_path):
        g = SessionGuardian(str(tmp_path))
        assert g.is_path_allowed(".")
        assert g.is_path_allowed(str(tmp_path))

    def test_blocked_patterns(self):
        g = SessionGuardian(".")
        for cmd in ["rm -rf /", "sudo apt", "mkfs.ext4 /dev/sda", "dd if=/dev/zero of=/tmp"]:
            assert g.allow_command(cmd) is not None, f"Should block: {cmd}"


class TestSessionMemory:
    def test_remember_recall(self, tmp_path):
        m = SessionMemory(str(tmp_path / "mem"))
        m.remember("key1", "value1")
        assert m.recall("key1") == "value1"

    def test_forget(self, tmp_path):
        m = SessionMemory(str(tmp_path / "mem"))
        m.remember("x", "y")
        m.forget("x")
        assert m.recall("x") is None

    def test_ttl_expiry(self, tmp_path):
        import time
        m = SessionMemory(str(tmp_path / "mem"))
        m.remember("ephemeral", "data", ttl=1)
        assert m.recall("ephemeral") == "data"

    def test_episodes(self, tmp_path):
        m = SessionMemory(str(tmp_path / "mem"))
        m.record_episode("user", "hello world")
        m.record_episode("assistant", "hi there")
        assert len(m.recent_episodes()) == 2

    def test_search_episodes(self, tmp_path):
        m = SessionMemory(str(tmp_path / "mem"))
        m.record_episode("user", "fix the bug in parser")
        results = m.search_episodes("parser")
        assert len(results) == 1


class TestOSInterface:
    def test_info(self, tmp_path):
        osi = OSInterface(str(tmp_path))
        info = osi.info()
        assert "platform" in info
        assert "project_dir" in info

    def test_detect_project_type(self, tmp_path):
        osi = OSInterface(str(tmp_path))
        assert osi.detect_project_type()["type"] == "unknown"
        (tmp_path / "package.json").write_text('{"name":"test"}')
        assert osi.detect_project_type()["type"] == "node"

    def test_get_files_by_extension(self, tmp_path):
        (tmp_path / "a.py").write_text("")
        (tmp_path / "b.py").write_text("")
        osi = OSInterface(str(tmp_path))
        files = osi.get_files_by_extension("py")
        assert len(files) == 2


class TestCodeInterface:
    def test_detect_language(self, tmp_path):
        ci = CodeInterface(str(tmp_path))
        assert ci.detect_language("main.py") == "python"
        assert ci.detect_language("app.ts") == "typescript"
        assert ci.detect_language("Dockerfile") == "dockerfile"

    def test_count_lines(self, tmp_path):
        f = tmp_path / "f.py"
        f.write_text("# comment\ndef foo():\n    pass")
        ci = CodeInterface(str(tmp_path))
        c = ci.count_lines(str(f))
        assert c["total"] == 3
        assert c["code"] == 2
        assert c["comment"] == 1

    def test_find_functions(self, tmp_path):
        f = tmp_path / "f.py"
        f.write_text("def hello():\n    pass\nclass Foo:\n    pass")
        ci = CodeInterface(str(tmp_path))
        funcs = ci.find_functions(str(f))
        names = {fn["name"] for fn in funcs}
        assert "hello" in names
        assert "Foo" in names

    def test_find_imports(self, tmp_path):
        f = tmp_path / "f.py"
        f.write_text("import os\nfrom pathlib import Path\n")
        ci = CodeInterface(str(tmp_path))
        imports = ci.find_imports(str(f))
        assert "os" in imports

    def test_summarize_project(self, tmp_path):
        (tmp_path / "main.py").write_text("x=1\n")
        (tmp_path / "utils.py").write_text("y=2\n")
        ci = CodeInterface(str(tmp_path))
        s = ci.summarize_project()
        assert s["total_files"] == 2
