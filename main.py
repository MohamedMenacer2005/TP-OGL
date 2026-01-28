import argparse
import sys
import os
from dotenv import load_dotenv
from src.utils.logger import log_experiment, ActionType
from src.agents.base_agent import SimpleAnalyzer

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="TP-OGL: AI Agent Refactoring Swarm")
    parser.add_argument("--target_dir", type=str, required=True, 
                       help="Path to code directory to analyze")
    parser.add_argument("--model", type=str, default="gemini-1.5-flash",
                       help="LLM model to use (default: gemini-1.5-flash)")
    args = parser.parse_args()

    if not os.path.exists(args.target_dir):
        print(f"❌ Directory not found: {args.target_dir}")
        sys.exit(1)

    print(f"🚀 Starting TP-OGL on: {args.target_dir}")
    print(f"📊 Model: {args.model}")
    
    # Log startup
    log_experiment(
        agent_name="System",
        model_used=args.model,
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": "Initialize experiment",
            "output_response": f"Starting on {args.target_dir}"
        },
        status="SUCCESS"
    )

    # Phase 1: Execute simple analyzer for testing
    try:
        analyzer = SimpleAnalyzer(agent_name="SimpleAnalyzer", model=args.model)
        results = analyzer.execute(args.target_dir)
        
        print(f"✅ Analysis complete: {results['files_analyzed']} files analyzed")
        print(f"📁 Results: {results}")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        log_experiment(
            agent_name="System",
            model_used=args.model,
            action=ActionType.DEBUG,
            details={
                "input_prompt": f"Execute SimpleAnalyzer on {args.target_dir}",
                "output_response": f"Error: {str(e)}"
            },
            status="FAILURE"
        )
        sys.exit(1)

    print("✅ MISSION_COMPLETE")


if __name__ == "__main__":
    main()