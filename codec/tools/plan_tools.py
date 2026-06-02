_state_manager = None


def set_state_manager(sm):
    global _state_manager
    _state_manager = sm


from codec.tools.registry import register_tool


@register_tool("create_plan", "Create a structured plan with steps before starting work. Call this at the start of complex multi-step tasks.")
async def create_plan(goal: str, steps: list[str], project_dir: str = "."):
    if not _state_manager:
        return "Error: state manager not available."
    plan_steps = [{"description": s, "status": "pending", "result": None} for s in steps]
    _state_manager.set_plan(plan_steps, goal)
    result = [f"Plan created: {goal}"]
    for i, s in enumerate(steps):
        result.append(f"  Step {i+1}: {s} [pending]")
    return "\n".join(result)


@register_tool("update_plan_step", "Mark a plan step as completed or failed")
async def update_plan_step(step_index: int, status: str, result: str = "", project_dir: str = "."):
    if not _state_manager:
        return "Error: state manager not available."
    _state_manager.update_plan_step(step_index, status, result)
    return f"Step {step_index + 1} marked as {status}"


@register_tool("get_plan", "Show the current active plan and its progress")
async def get_plan(project_dir: str = "."):
    if not _state_manager:
        return "Error: state manager not available."
    summary = _state_manager.get_plan_summary()
    return summary or "No active plan."
