from genotools.targets import claude_code

ADAPTERS = {
    "claude-code": claude_code,
}


def get(agent: str):
    if agent not in ADAPTERS:
        raise KeyError(f"unknown agent: {agent} (known: {sorted(ADAPTERS)})")
    return ADAPTERS[agent]
