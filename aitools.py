def get_conversation_summary(conversation_str: str, summary_agent) -> str:
    from core.logging import logging
    if len(conversation_str) < 1: return "NO_SPECIFIC_TASK"
    summary:str = summary_agent.simple_chat(conversation_str).split("\n")[0].strip()
    logging.info("\n----------get_conversation_summary called----------")
    logging.debug(summary)
    return summary
