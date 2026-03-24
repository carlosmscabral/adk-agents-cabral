import argparse
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.agent import root_agent

def main():
    parser = argparse.ArgumentParser(description="Run the Jira Connector Agent")
    parser.add_argument("prompt", type=str, nargs="?", help="The prompt to send to the agent")
    args = parser.parse_args()

    if args.prompt:
        response = root_agent.run(args.prompt)
        print(f"Agent response:\n{response.text}")
    else:
        print("Starting interactive mode. Type 'exit' or 'quit' to end.")
        while True:
            try:
                user_input = input("\nYou: ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                if not user_input.strip():
                    continue
                
                response = root_agent.run(user_input)
                print(f"\nAgent:\n{response.text}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()
