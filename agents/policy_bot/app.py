import policy_agent

policy_agent.policy_bot.company_name = "Google"
policy_agent.policy_bot.bot_name = "PolicyBot"
policy_agent.policy_bot._create_rag_chain()  # Recreate chain with new values

policy_agent.policy_bot.ask_question("What is the company policy on remote work?")