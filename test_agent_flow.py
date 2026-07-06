"""
Test script to verify MedoraAI agent execution flow.
Run: python test_agent_flow.py
"""

import asyncio
from app.graphs.agent_graph import build_graph


async def test_agent_flow():
    """Test the complete multi-agent flow"""
    
    print("\n" + "=" * 70)
    print("🏥 MedoraAI - Agent Execution Flow Test")
    print("=" * 70)
    
    graph = build_graph()
    
    # Test cases
    test_cases = [
        {
            "name": "Doctor Search",
            "query": "Find a cardiologist in Colombo",
            "expected_agent": "appointment_agent"
        },
        {
            "name": "Medical Question",
            "query": "What does high cholesterol mean?",
            "expected_agent": "direct_answer_agent"
        },
        {
            "name": "Emergency",
            "query": "I'm having severe chest pain",
            "expected_agent": "emergency_agent"
        },
        {
            "name": "Pharmacy",
            "query": "Where can I find Aspirin in Colombo?",
            "expected_agent": "pharmacy_agent"
        }
    ]
    
    # Initial state
    base_state = {
        "query": "",
        "response": "",
        "specialty": None,
        "location": None,
        "needs_user_input": False,
        "followup_question": None,
        "doctor_results": [],
        "routes": [],
        "execution_trace": [],
        "retrieved_docs": [],
        "rag_result": "",
        "memory_result": "",
        "web_result": "",
        "symptoms": [],
        "current_goal": "",
        "urgency": "",
        "report_uploaded": False,
        "medicine_request": False,
        "appointment_request": False,
        "emergency_flag": False,
        "doctor_recommendation": "",
        "pharmacy_recommendation": "",
        "appointment_recommendation": "",
        "patient_analysis": "",
        "iteration_count": 0,
        "final_answer": "",
        "agent_results": [],
        "decision_scores": {},
        "clarification_done": False,
        "user_context": {},
        "metadata": {},
        "chat_history": [],
        "final_response": "",
        "route": None,
        "next_task": None,
        "pending_tasks": [],
        "completed_tasks": [],
        "tool_result": "",
        "chat_result": "",
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'─' * 70}")
        print(f"Test {i}: {test_case['name']}")
        print(f"{'─' * 70}")
        
        state = {**base_state, "query": test_case["query"]}
        print(f"\n📝 Input Query: {state['query']}")
        print(f"✓ Expected Primary Agent: {test_case['expected_agent']}")
        
        try:
            print(f"\n⏳ Invoking graph...")
            result = await graph.ainvoke(state)
            
            # Display results
            print(f"\n✓ Execution completed successfully!")
            
            if result.get("execution_trace"):
                print(f"\n📋 Execution Trace:")
                trace = " → ".join(result["execution_trace"])
                print(f"   {trace}")
            
            if result.get("decision_scores"):
                print(f"\n📊 Decision Scores:")
                scores = result["decision_scores"]
                # Sort by score
                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                for agent, score in sorted_scores:
                    bar = "█" * (score // 2)
                    print(f"   {agent:20s}: {score:2d}/10 {bar}")
            
            print(f"\n🤖 Agent Response:")
            response = result.get("response", "")
            if response:
                print(f"   {response[:200]}..." if len(response) > 200 else f"   {response}")
            else:
                print("   (No response)")
            
            # Verify expected agent was called
            trace = result.get("execution_trace", [])
            if any(test_case["expected_agent"] in str(t) for t in trace):
                print(f"\n✅ SUCCESS: {test_case['expected_agent']} was invoked as expected!")
            else:
                print(f"\n⚠️  WARNING: Expected {test_case['expected_agent']} but trace shows: {trace}")
                
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n\n{'=' * 70}")
    print("✅ All tests completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_agent_flow())
