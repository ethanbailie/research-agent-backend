# Market Lens

## Overview
Market Lens is a tool designed to help entrepreneurs and business leaders validate their ideas and identify cost-saving opportunities. It performs competitive analysis and assesses automation potential using AI agents. The system compares user-provided ideas or business decks against existing market players and operations, offering actionable insights.

---

## How It Works

### Validation of Unique Ideas:
1. **Input an Idea:**
   - Enter your business idea into the search box.
2. **Web Search:**
   - Market Lens searches for major players in the domain.
3. **Market Analysis:**
   - Identifies and summarizes competitors' unique market approaches.
4. **Comparison:**
   - Compares and contrasts the input idea with the gathered market data to determine its uniqueness.
5. **Output:**
   - Displays relevant companies and a validation result for the idea.

### Operational Cost-Saving Suggestions:
1. **Input a Founder Deck:**
   - Upload a deck containing your company's operational details.
2. **AI-Powered Insights:**
   - Analyzes the operations and identifies cost-saving measures through automation.
3. **Opportunities and Validation:**
   - Provides JSON-formatted outputs highlighting specific automation opportunities and their potential cost savings.

---

## Tech Stack

### Backend:
- **Language:** Python
- **Features:**
  - Built using FastAPI for quick and scalable API development.
  - Dockerized for streamlined communication between frontend and backend.
- **Core Functionality:**
  - Handles data analysis, web searches, and automation recommendations using a modular research agent.

### Frontend:
- **Framework:** React + TypeScript + Vite
- **Features:**
  - Interactive user interface for inputting ideas and founder decks.
  - Displays summarized market analysis and automation opportunities.

---

## Code Highlights

### Prompts:
1. **Research Prompt:**
   Guides the AI agent to gather market data and summarize competitor insights.
2. **Comparison Prompt:**
   Directs the agent to identify automation opportunities and cost-saving potential, outputting JSON for easy integration.

### Key Libraries:
- **`langgraph`:** Manages stateful AI operations.
- **`langchain`:** Facilitates natural language understanding.
- **`fastapi`:** Provides a robust backend framework.
- **`TavilySearchResults`:** Conducts web searches to gather information.

### Dockerization:
The backend is Dockerized for seamless integration with the frontend and to ensure consistent runtime environments.

---

## Example API Workflow

1. **POST Request to `/research`:**
   - Input:
     ```json
     {
       "query": "Analyze cost-saving opportunities for our ride-sharing service."
     }
     ```
   - Output:
     ```json
     {
       "result": {
         "opportunities": [
           {
             "name": "Customer Support Automation",
             "description": "Use AI-driven chatbots to handle routine inquiries.",
             "unique_perspective": "Reduces support costs and improves response time."
           }
         ],
         "validation": {
           "automation_validity": "There are significant opportunities for AI automation in customer support, logistics tracking, and fleet optimization."
         }
       }
     }
     ```

---

## Getting Started

### Prerequisites:
- Docker installed locally.
- Node.js and npm for frontend development.

### Setup:

#### Backend:
1. Clone the repository and navigate to the backend directory.
2. Build and run the Docker container:
   ```bash
   docker build -t market-lens-backend .
   docker run -p 8000:8000 market-lens-backend
