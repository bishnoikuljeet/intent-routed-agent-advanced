import streamlit as st
from services.example_queries_service import ExampleQueriesService


class HelpPanel:
    def __init__(self):
        self.example_service = ExampleQueriesService()
    
    def render(self):
        """Render help and documentation panel"""
        
        st.markdown("# 📚 Help & Documentation")
        
        # Quick Start
        with st.expander("🚀 Quick Start Guide", expanded=False):
            st.markdown("""
            ### Getting Started
            
            1. **Create a Session**: Click "🆕 New Session" in the sidebar
            2. **Ask a Question**: Type your query in the input box
            3. **Suggestions Button**: Type at least 2 characters, then click "💡 Suggestions"
            4. **View Results**: See the answer and execution trace
            5. **Manage Sessions**: Switch between sessions or delete old ones
            
            ### Example Queries
            
            - "What is the current latency for the payment service?"
            - "Show me the error rate for auth_service"
            - "Is 150ms greater than our 100ms latency threshold?"
            - "What services are in our microservices architecture?"
            """)
        
        # Features
        with st.expander("✨ Key Features"):
            st.markdown("""
            ### Session Management
            - Create multiple sessions for different conversations
            - Switch between sessions seamlessly
            - Search sessions by content
            - Delete old sessions
            
            ### Smart Autocomplete
            - Get relevant suggestions when you click the Suggestions button
            - Browse by category (Observability, Knowledge, Utility, etc.)
            - See which tools will be used
            
            ### Execution Traces
            - View detailed execution timeline
            - See which agents were called
            - Check tool execution details
            - Export traces as JSON
            
            ### Real-time Processing
            - Progress indicators during query processing
            - Confidence scores for answers
            - Intent classification results
            """)
        
        # Example Queries Section
        self._render_example_queries()
        
        # Tool Categories
        with st.expander("🛠️ Available Tools"):
            st.markdown("""
            ### Observability Server
            - Service metrics (latency, error rate, throughput)
            - Alert management
            - Log aggregation
            - SLO tracking
            - Capacity planning
            - Incident management
            
            ### Knowledge Server
            - Semantic search over documentation
            - Document versioning
            - Change tracking
            - Recommendation engine
            - Knowledge graph queries
            
            ### Utility Server
            - Value comparisons
            - Percentage calculations
            - Statistical summaries
            - Trend analysis
            - Anomaly detection
            - Data validation
            
            ### System Server
            - Tool registry lookup
            - Agent health checks
            - Workflow status
            - Performance profiling
            
            ### Language Server
            - Language detection
            - Text translation
            - Typo correction
            - Text normalization
            
            ### Database Server
            - **get_order_details**: Retrieve complete order information by order number
            - **search_customers**: Search customers by name, territory, or type
            - **get_sales_summary**: Get sales totals and metrics for date ranges
            - **get_customer_orders**: Retrieve all orders for a specific customer
            - **get_low_stock_items**: Find inventory items below reorder threshold
            - **search_inventory**: Search products by SKU, name, or category
            - **query_database**: Execute dynamic SQL queries with natural language (schema-aware)
            """)
        
        # Troubleshooting
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            ### Common Issues
            
            **Backend Connection Failed**
            - Check if backend is running on port 8001
            - Verify `BACKEND_URL` in configuration
            - Check network connectivity
            
            **Query Takes Too Long**
            - Complex queries may take 5-10 seconds
            - Check backend logs for errors
            - Try simplifying the query
            
            **Session Not Loading**
            - Verify session ID is valid
            - Check if session was deleted
            - Try creating a new session
            """)
        
        # API Documentation
        with st.expander("📖 API Reference"):
            st.markdown("""
            ### Backend Endpoints
            
            - `POST /api/v1/query` - Process a query
            - `POST /api/v1/sessions` - Create new session
            - `GET /api/v1/sessions` - List all sessions
            - `GET /api/v1/sessions/{id}` - Get session details
            - `DELETE /api/v1/sessions/{id}` - Delete session
            - `GET /api/v1/tools` - List available tools
            - `GET /api/v1/servers` - List MCP servers
            - `GET /api/v1/health` - Health check
            """)
        
        # About
        with st.expander("ℹ️ About"):
            st.markdown("""
            ### Intent-Routed Agent Platform
            
            **Version:** 1.0.0  
            **Framework:** Streamlit + FastAPI  
            **AI Engine:** Azure OpenAI GPT-4o-mini  
            **Architecture:** Multi-agent with MCP tool ecosystem
            
            **Features:**
            - LLM-powered intent classification
            - Dynamic tool selection
            - Multi-agent workflow orchestration
            - Execution trace visualization
            - Session management
            
            **Tech Stack:**
            - Frontend: Streamlit
            - Backend: FastAPI, LangGraph, LangChain
            - Vector Store: FAISS
            - Embeddings: Azure OpenAI
            - Tools: MCP (Model Context Protocol)
            """)
    
    def _render_example_queries(self):
        """Render the example queries section with copy functionality"""
        
        # Get all queries grouped by category
        categories = self.example_service.get_queries_by_category()
        total_queries = self.example_service.get_query_count()
        
        with st.expander("💡 Example Queries", expanded=False):
            st.markdown(f"""
            ### 📊 Query Library ({total_queries} total queries)
            
            Browse through example queries organized by server category. Each query includes:
            - **Query Text**: The exact query to use
            - **Intent**: The detected intent type
            - **Expected Tool**: The tool that will be used
            - **Copy Button**: Click to copy the query to clipboard
            
            ---
            """)
            
            # Category tabs
            category_tabs = st.tabs(list(categories.keys()))
            
            for i, (category_name, queries) in enumerate(categories.items()):
                with category_tabs[i]:
                    if not queries:
                        st.info(f"No queries found for {category_name}")
                        continue
                    
                    st.markdown(f"### {category_name} ({len(queries)} queries)")
                    
                    # Display each query with copy functionality
                    for j, query_data in enumerate(queries):
                        self._render_query_card(query_data, j)
                    
                    # Category summary
                    unique_tools = set(q['tool'] for q in queries)
                    unique_intents = set(q['intent'] for q in queries)
                    
                    st.markdown(f"""
                    ---
                    **Category Summary:**
                    - **Tools Used:** {', '.join(sorted(unique_tools))}
                    - **Intent Types:** {', '.join(sorted(unique_intents))}
                    """)
    
    def _render_query_card(self, query_data: dict, index: int):
        """Render a single query card"""
        
        # Query text with syntax highlighting
        query_text = query_data['query']
        
        # Create a code block
        st.code(query_text, language='text', wrap_lines=True)
        
        # Show metadata in a single line
        expected = query_data['expected']
        if len(expected) > 100:
            expected = expected[:97] + "..."
        st.markdown(f"🎯 **Intent:** `{query_data['intent']}` | 🔧 **Tool:** `{query_data['tool']}` | 📋 **Expected:** {expected}")
        
        # Add some spacing
        st.markdown("---")
    
    def _get_copy_javascript(self, text: str) -> str:
        """Generate JavaScript code to copy text to clipboard"""
        return f"""
        <script>
        navigator.clipboard.writeText(`{text}`).then(function() {{
            console.log('Text copied to clipboard');
        }}).catch(function(err) {{
            console.error('Failed to copy text: ', err);
        }});
        </script>
        """
