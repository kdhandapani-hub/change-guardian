import unittest
from unittest.mock import patch, AsyncMock
from langchain_core.messages import AIMessage
from tests_agent_helpers import fixtures

class ScriptedModel:
    """Explicit test double, not an AI implementation."""
    def __init__(self):self.calls=0
    def bind_tools(self,tools):return self
    async def ainvoke(self,messages):
        self.calls+=1
        if self.calls==1:return AIMessage(content="",tool_calls=[{"name":"read_selected_test_results","args":{},"id":"test-call"}])
        return AIMessage(content="Test-double finding: selected payment check failed; positions untested. Engineer review required.")

class AgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_checkpointed_tool_loop(self):
        import tempfile
        from pathlib import Path
        from app.investigate import run_investigation
        plan,raw,build,context=fixtures()
        async def read(client,name,number):return build if name=="getBuild" else {"failed":1}
        with tempfile.TemporaryDirectory() as d, patch("app.investigate.ROOT",Path(d)),patch("app.investigate.artifacts",return_value=(plan,raw)),patch("app.investigate.read_tool",side_effect=read):
            model=ScriptedModel();result=await run_investigation(None,10,context,"test-thread",model)
            self.assertEqual(result["investigation"]["status"],"AI_COMPLETE")
            self.assertEqual(model.calls,2)
            self.assertTrue((Path(d)/"runtime/investigations.sqlite").exists())
    async def test_model_failure_retains_verdict(self):
        import tempfile
        from pathlib import Path
        from app.investigate import run_investigation
        plan,raw,build,context=fixtures()
        class Unavailable(ScriptedModel):
            async def ainvoke(self,messages):raise RuntimeError("simulated")
        async def read(client,name,number):return build if name=="getBuild" else {}
        with tempfile.TemporaryDirectory() as d,patch("app.investigate.ROOT",Path(d)),patch("app.investigate.artifacts",return_value=(plan,raw)),patch("app.investigate.read_tool",side_effect=read):
            result=await run_investigation(None,10,context,"failure-thread",Unavailable())
            self.assertEqual(result["investigation"]["status"],"AI_INCOMPLETE")
            self.assertEqual(result["selected_scope_verdict"],"CHECKS_FAILED")
