from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from app.schemas.state import ConversationState
from app.agents.coordinator import CoordinatorAgent
from app.agents.intent import IntentAgent
from app.agents.planner import PlannerAgent
from app.agents.executor import ExecutorAgent
from app.agents.aggregator import AggregatorAgent
from app.agents.reasoning import ReasoningAgent
from app.agents.evaluation import SelfEvaluationAgent
from app.agents.tool_first_answer_agent import ToolFirstAnswerAgent
from app.memory.manager import MemoryManager
from app.language.processor import LanguageProcessor
from app.core.logging import logger
from datetime import datetime


class MultiAgentWorkflow:
    def __init__(
        self,
        coordinator: CoordinatorAgent,
        intent: IntentAgent,
        planner: PlannerAgent,
        executor: ExecutorAgent,
        aggregator: AggregatorAgent,
        reasoning: ReasoningAgent,
        evaluation: SelfEvaluationAgent,
        answer: ToolFirstAnswerAgent,
        memory_manager: MemoryManager,
        language_processor: LanguageProcessor
    ):
        self.coordinator = coordinator
        self.intent = intent
        self.planner = planner
        self.executor = executor
        self.aggregator = aggregator
        self.reasoning = reasoning
        self.evaluation = evaluation
        self.answer = answer
        self.memory_manager = memory_manager
        self.language_processor = language_processor
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(ConversationState)
        
        workflow.add_node("language_processing", self._language_processing_node)
        workflow.add_node("memory_processing", self._memory_processing_node)
        workflow.add_node("coordinator", self.coordinator.coordinate)
        workflow.add_node("intent", self.intent.classify_intent)
        workflow.add_node("planner", self.planner.create_plan)
        workflow.add_node("executor", self.executor.execute_plan)
        workflow.add_node("aggregator", self.aggregator.aggregate_results)
        workflow.add_node("reasoning", self.reasoning.reason)
        workflow.add_node("evaluation", self.evaluation.evaluate)
        workflow.add_node("answer", self.answer.answer)
        workflow.add_node("translate_output", self._translate_output_node)
        
        workflow.set_entry_point("language_processing")
        
        workflow.add_edge("language_processing", "coordinator")
        workflow.add_edge("coordinator", "memory_processing")
        workflow.add_edge("memory_processing", "intent")
        workflow.add_edge("intent", "planner")
        
        # Add conditional edge from planner - go directly to answer if clarification needed
        workflow.add_conditional_edges(
            "planner",
            self._needs_clarification,
            {
                "clarify": "answer",
                "execute": "executor"
            }
        )
        
        workflow.add_edge("executor", "aggregator")
        workflow.add_edge("aggregator", "reasoning")
        workflow.add_edge("reasoning", "evaluation")
        
        workflow.add_conditional_edges(
            "evaluation",
            self._should_retry,
            {
                "retry": "planner",
                "continue": "answer"
            }
        )
        
        workflow.add_edge("answer", "translate_output")
        workflow.add_edge("translate_output", END)
        
        return workflow.compile()
    
    async def _language_processing_node(self, state: ConversationState) -> ConversationState:
        logger.info_structured("Language processing started")
        
        # Initialize execution trace if not present
        if not state.get("execution_trace"):
            state["execution_trace"] = {
                "processing_components": [],
                "agents_called": [],
                "timestamps": {},
                "tools_called": []
            }
        
        original_query = state.get("original_query", "")
        
        processed_query, detected_lang, is_injection, injection_reason = \
            self.language_processor.process_input(original_query)
        
        if is_injection:
            logger.warning_structured(
                "Prompt injection detected",
                reason=injection_reason
            )
            state["final_answer"] = "I detected a potentially unsafe input. Please rephrase your query."
            state["errors"].append(f"Security: {injection_reason}")
            state["current_query"] = ""
            return state
        
        state["current_query"] = processed_query
        state["user_language"] = detected_lang
        
        # Add execution trace tracking
        state["execution_trace"]["processing_components"].append("language_processor")
        state["execution_trace"]["timestamps"]["language_processor"] = datetime.utcnow().isoformat()
        
        logger.info_structured(
            "Language processing completed",
            detected_language=detected_lang,
            original_length=len(original_query),
            processed_length=len(processed_query)
        )
        
        return state
    
    async def _memory_processing_node(self, state: ConversationState) -> ConversationState:
        logger.info_structured("Memory processing started")
        
        # Initialize execution trace if not present
        if not state.get("execution_trace"):
            state["execution_trace"] = {
                "processing_components": [],
                "agents_called": [],
                "timestamps": {},
                "tools_called": []
            }
        
        conversation_id = state.get("conversation_id", "")
        current_query = state.get("current_query", "")
        messages = state.get("messages", [])
        current_summary = state.get("conversation_summary")
        
        recent_messages, new_summary = await self.memory_manager.process_memory(
            conversation_id=conversation_id,
            messages=messages,
            current_summary=current_summary
        )
        
        state["recent_messages"] = recent_messages
        if new_summary:
            state["conversation_summary"] = new_summary
        
        context = await self.memory_manager.get_conversation_context(
            conversation_id=conversation_id,
            current_query=current_query,
            recent_messages=recent_messages,
            summary=new_summary
        )
        
        if not state.get("metadata"):
            state["metadata"] = {}
        state["metadata"]["conversation_context"] = context
        
        # Add execution trace tracking
        state["execution_trace"]["processing_components"].append("memory_manager")
        state["execution_trace"]["timestamps"]["memory_manager"] = datetime.utcnow().isoformat()
        
        logger.info_structured(
            "Memory processing completed",
            recent_messages_count=len(recent_messages),
            has_summary=new_summary is not None
        )
        
        return state
    
    async def _translate_output_node(self, state: ConversationState) -> ConversationState:
        logger.info_structured("Output translation started")
        
        # Initialize execution trace if not present
        if not state.get("execution_trace"):
            state["execution_trace"] = {
                "processing_components": [],
                "agents_called": [],
                "timestamps": {},
                "tools_called": []
            }
        
        final_answer = state.get("final_answer", "")
        user_language = state.get("user_language", "en")
        
        translation_performed = False
        if user_language != "en" and final_answer:
            translated_answer = self.language_processor.process_output(
                final_answer,
                user_language
            )
            state["final_answer"] = translated_answer
            translation_performed = True
            
            logger.info_structured(
                "Output translated",
                target_language=user_language,
                original_length=len(final_answer),
                translated_length=len(translated_answer)
            )
        
        # Add execution trace tracking only if translation was performed
        if translation_performed:
            state["execution_trace"]["processing_components"].append("output_translator")
            state["execution_trace"]["timestamps"]["output_translator"] = datetime.utcnow().isoformat()
        
        return state
    
    def _should_retry(self, state: ConversationState) -> Literal["retry", "continue"]:
        evaluation = state.get("metadata", {}).get("evaluation", {})
        should_retry = evaluation.get("should_retry", False)
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)
        
        # Safety check: if we've had too many retries with low confidence, stop retrying
        confidence_score = state.get("confidence_score", 0.5)
        
        if should_retry and retry_count < max_retries and confidence_score > 0.1:
            # Note: retry_count is now incremented in evaluation agent to ensure state persistence
            
            logger.info_structured(
                "Retry triggered",
                retry_count=state["retry_count"],
                max_retries=max_retries,
                reason=evaluation.get("retry_reason")
            )
            
            return "retry"
        
        return "continue"
    
    def _needs_clarification(self, state: ConversationState) -> Literal["clarify", "execute"]:
        """Check if planner detected need for clarification"""
        needs_clarification = state.get("needs_clarification", False)
        
        if needs_clarification:
            logger.info_structured(
                "Clarification needed, routing directly to answer agent",
                conversation_id=state.get("conversation_id"),
                clarification_type=state.get("missing_info", {}).get("clarification_type", "unknown")
            )
            return "clarify"
        
        return "execute"
    
    async def run(self, query: str, conversation_id: str = None) -> Dict[str, Any]:
        # Load conversation history if conversation_id exists
        messages = []
        conversation_summary = None
        intent_history = []
        tool_history = []
        
        if conversation_id:
            try:
                # Retrieve conversation history from vector store
                results = await self.memory_manager.vector_store.search(
                    conversation_id=conversation_id,
                    query="conversation history",
                    k=10
                )
                
                # Reconstruct messages from stored results
                for result in results:
                    if result.get("type") == "HumanMessage":
                        messages.append(HumanMessage(content=result.get("content", "")))
                    elif result.get("type") == "AIMessage":
                        messages.append(AIMessage(content=result.get("content", "")))
                
                # Try to get conversation summary
                summary_results = await self.memory_manager.vector_store.search(
                    conversation_id=conversation_id,
                    query="conversation summary",
                    k=1
                )
                
                if summary_results:
                    conversation_summary = summary_results[0].get("content", "")
                
            except Exception as e:
                logger.error_structured(
                    "Failed to load conversation history",
                    error=str(e),
                    conversation_id=conversation_id
                )
        
        initial_state: ConversationState = {
            "conversation_id": conversation_id or "",
            "messages": messages,
            "recent_messages": messages[-5:],  # Last 5 messages
            "conversation_summary": conversation_summary,
            "intent_history": intent_history,
            "tool_history": tool_history,
            "user_language": "en",
            "current_query": query,
            "original_query": query,
            "detected_intent": None,
            "extracted_entities": {},
            "execution_plan": [],
            "tool_results": [],
            "aggregated_data": {},
            "reasoning_output": None,
            "confidence_score": 0.0,
            "retry_count": 0,
            "max_retries": 2,
            "final_answer": None,
            "execution_trace": {},
            "errors": [],
            "metadata": {},
            "tool_cache": {}  # Cache tool results during retries
        }
        
        logger.info_structured(
            "Workflow started",
            query=query,
            conversation_id=conversation_id
        )
        
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            logger.info_structured(
                "Workflow completed",
                conversation_id=final_state.get("conversation_id"),
                confidence=final_state.get("confidence_score"),
                retry_count=final_state.get("retry_count")
            )
            
            return final_state
            
        except Exception as e:
            logger.error_structured(
                "Workflow failed",
                error=str(e),
                conversation_id=conversation_id
            )
            
            initial_state["final_answer"] = f"An error occurred: {str(e)}"
            initial_state["errors"].append(str(e))
            return initial_state
