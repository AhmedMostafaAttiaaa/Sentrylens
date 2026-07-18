import pytest

from app.mcp.skills.calculator import CalculatorSkill


@pytest.mark.asyncio
async def test_calculator_basic_expression():
    skill = CalculatorSkill()
    result = await skill.run(expression="2 + 3 * 4")
    assert result["result"] == 14


@pytest.mark.asyncio
async def test_calculator_rejects_unsafe_expression():
    skill = CalculatorSkill()
    with pytest.raises(Exception):
        await skill.run(expression="__import__('os').system('echo hi')")
