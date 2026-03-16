import streamlit as st
import json
import uuid
from datetime import datetime
from typing import Dict, Any


class TraceViewer:
    def render(self, trace_data: Dict[str, Any]):
        """Render execution trace with timeline and details"""
        
        if not trace_data or not isinstance(trace_data, dict):
            st.info("No execution trace available")
            return
        
        # Check if trace has actual data
        has_agents = trace_data.get('agents_called') and len(trace_data.get('agents_called', [])) > 0
        has_tools = trace_data.get('tools_called') and len(trace_data.get('tools_called', [])) > 0
        has_components = trace_data.get('processing_components') and len(trace_data.get('processing_components', [])) > 0
        
        if not (has_agents or has_tools or has_components):
            st.info("No execution trace data available")
            return
        
        # Debug: Show trace data structure (outside expander)
        st.markdown("#### 🔍 Debug Trace Data")
        st.json(trace_data)
        st.divider()
        
        # Timeline view
        self._render_timeline(trace_data)
        
        st.divider()
        
        # Tools executed
        self._render_tools(trace_data)
        
        st.divider()
        
        # Export option
        self._render_export(trace_data)
    
    def _render_timeline(self, trace_data: Dict[str, Any]):
        """Render execution timeline"""
        st.markdown("#### ⏱️ Execution Timeline")
        
        agents = trace_data.get('agents_called', [])
        timestamps = trace_data.get('timestamps', {})
        
        if not agents:
            st.info("No agent execution data available")
            return
        
        # Create timeline visualization
        for i, agent in enumerate(agents):
            timestamp = timestamps.get(agent, 'N/A')
            
            # Format timestamp
            try:
                if timestamp != 'N/A':
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S.%f")[:-3]
                else:
                    time_str = timestamp
            except:
                time_str = timestamp
            
            # Display step
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{i+1}. {agent.title()}**")
            with col2:
                st.caption(time_str)
    
    def _render_tools(self, trace_data: Dict[str, Any]):
        """Render tools executed"""
        st.markdown("#### 🛠️ Tools Executed")
        
        tools = trace_data.get('tools_called', [])
        
        if not tools:
            st.info("No tools were executed")
            return
        
        for i, tool in enumerate(tools):
            tool_name = tool.get('name', 'Unknown')
            success = tool.get('success', False)
            latency = tool.get('latency_ms', 0)
            params = tool.get('params', {})
            
            # Status icon
            status_icon = "✅" if success else "❌"
            
            # Tool details (no nested expander)
            st.write(f"**{status_icon} {tool_name} - {latency:.2f}ms**")
            
            # Tool details in columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Latency", f"{latency:.2f}ms")
                st.metric("Status", "Success" if success else "Failed")
            
            with col2:
                st.metric("Server", tool.get('server', 'Unknown'))
                st.metric("Agent", tool.get('agent', 'Unknown'))
            
            # Parameters section
            if params:
                st.markdown("**Parameters:**")
                st.json(params)
            
            # Separator between tools
            if i < len(tools) - 1:
                st.divider()
    
    def _render_export(self, trace_data: Dict[str, Any]):
        """Render export options"""
        st.markdown("#### 📥 Export Trace")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON export
            trace_json = json.dumps(trace_data, indent=2)
            # Generate unique key using UUID to avoid duplicates
            unique_id = str(uuid.uuid4())[:8]
            st.download_button(
                label="📄 Download JSON",
                data=trace_json,
                file_name=f"execution_trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                key=f"download_trace_{unique_id}"
            )
        
        with col2:
            # Copy to clipboard (via text area)
            if st.button("📋 Copy to Clipboard", use_container_width=True, key=f"copy_trace_{unique_id}"):
                st.code(trace_json, language="json")
