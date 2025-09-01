Symphony Agent Runtime - Quick Start Guide
Get up and running with Symphony's real agent calling system in 5 minutes.

🚀 Prerequisites
Python 3.8+ installed
Symphony platform available at /platform/agents/
Basic familiarity with async/await patterns
⚡ 5-Minute Quick Start
Step 1: Setup Environment
# Navigate to agent runtime directory
cd /Users/pmuniraju/play/sandbox/symphony/workspace/apps/agent-runtime

# Install dependencies and verify setup
python setup.py
This will:

✅ Install required Python packages
✅ Verify Symphony platform structure
✅ Run basic system tests
✅ Create demo launcher script
Step 2: Run Quick Demo
# Run basic functionality test
python demos/quick_start.py
Expected Output:

🎼 Symphony Agent Runtime - Quick Start
==================================================

1. 🔍 Discovering Symphony agents...
   ✅ Found 25 agents:
      🎯 Coordinators: 2
      📊 Managers: 8
      👥 Leads: 6
      ⚙️ Specialists: 9

2. 📥 Loading sample agents...
   ✅ Loaded: Business Coordinator
   ✅ Loaded: Product Manager

3. 📡 Starting message bus...
   📋 Registered: Business Coordinator
   📋 Registered: Product Manager

4. 💬 Testing direct message passing...
   📤 Sending message: Business Coordinator → Product Manager
   ✅ Message delivered in 0.043s

5. 🤝 Testing agent coordination...
   👤 Business Coordinator assigned as hub (weight: 3.0)
   👤 Product Manager assigned as spoke (weight: 2.0)
   🔄 Running hub-spoke coordination...
   ✅ Coordination completed:
      Success: True
      Duration: 2.1s
      Consensus: 0.85
      Decisions: 2

🎉 Quick Start Demo Completed Successfully!
Step 3: Try Interactive Demo
# Run full interactive demonstration
python demos/live_agent_demo.py
What You'll See:

📋 Scenario Selection: Choose from pre-built business scenarios
🤖 Real Agent Loading: Watch actual Symphony agents initialize
🗳️ Live Decision-Making: See agents make real decisions with consensus scoring
📊 Performance Metrics: View timing, participation, and coordination effectiveness
📖 Understanding the Output
Agent Discovery
✅ Found 25 agents:
   🎯 Coordinators: 2    # Strategic level (Business, Life)
   📊 Managers: 8        # Tactical level (Product, Growth, Operations)
   👥 Leads: 6          # Execution level (Engineering, Quality)
   ⚙️ Specialists: 9    # Implementation level (API, UI, Data)
Message Delivery
✅ Message delivered in 0.043s
Shows actual message routing and delivery timing
Confirms agents can communicate using Symphony protocols
Coordination Results
Success: True          # Coordination completed without errors
Duration: 2.1s         # Total coordination time
Consensus: 0.85        # Agreement level (0.0-1.0, higher is better)
Decisions: 2           # Number of decisions made during coordination
Agent Status
Business Coordinator:
   Status: idle              # Current agent state
   Messages Processed: 3     # Communication activity
   Queue Length: 0          # Pending work
🎯 What Just Happened?
Real Agent Execution
Symphony agents were loaded from their markdown identities
Each agent became a live, executable AI system with:
Personality traits from their identity files
Decision-making capabilities based on their competencies
Communication patterns matching their documented styles
Actual Message Passing
Agents sent structured messages using Symphony's communication protocols
Messages were routed through the message bus with delivery guarantees
Real-time metrics tracked delivery success and latency
Live Coordination
Multiple agents participated in coordination sessions
Decision gates processed with actual voting and consensus building
Performance was measured with timing and effectiveness metrics
🚀 Next Steps
1. Explore Interactive Demos
# Try different coordination patterns and scenarios
python demos/live_agent_demo.py
Available Scenarios:

Competitor Product Launch - Hub-spoke coordination
Market Expansion Assessment - Mesh coordination
Customer Escalation Crisis - Sequential coordination
2. Try YOLO Integration
# Execute scenarios with real agent participation
python src/integration/yolo_agent_bridge.py --scenario "competitor-response"
3. Build Custom Scenarios
from src.runtime.agent_loader import AgentLoader
from src.coordination.orchestration import CoordinationFactory

# Load your preferred agents
loader = AgentLoader()
business_coord = await loader.load_agent("business-coordinator")
product_mgr = await loader.load_agent("product-manager")

# Create custom coordination
engine, context = CoordinationFactory.create_session(
    CoordinationPattern.HUB_SPOKE,
    message_bus,
    goal="Your custom business scenario"
)
🔧 Troubleshooting Quick Issues
"No agents discovered"
# Verify Symphony platform structure
ls /Users/pmuniraju/play/sandbox/symphony/platform/agents/
Should show coordinator, manager, lead, specialist directories.

"Module not found" errors
# Reinstall dependencies
pip install -r requirements.txt
"Agent loading failed"
Check that agent identity files exist in /platform/agents/
Verify agent markdown files have proper identity sections
Performance is slow
Normal for first run (agent discovery and loading)
Subsequent runs are much faster (cached results)
📚 Learn More
Architecture Overview - Understand system design
Agent Runtime Details - Deep dive into agent execution
Coordination Patterns - Multi-agent orchestration
YOLO Integration - Scenario execution
🎪 Ready for More?
You now have Symphony's agent runtime working! The system is:

✅ Loading real Symphony agents from platform identities
✅ Executing live coordination with actual decision-making
✅ Measuring performance with concrete metrics
✅ Ready for custom scenarios and business applications

This is real agent calling - not simulation, but actual executable AI coordination based on Symphony's documented agent hierarchy.

Next: Try the Interactive Live Demo for full scenario-based agent coordination!