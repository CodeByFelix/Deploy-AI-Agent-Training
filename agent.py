from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os


class State (MessagesState):
    summary: str

def summarize_conversation (state: State) -> State:
    """
        This Function summarizes the conversation to minimize the token input to the LLM
    """

    summary = state.get('summary', '')
    messages = state['messages']

    if len(messages) > 10:
        if summary:
            summary_message = summary
        else:
            summary_message = "No summary of the conversation so far"

        msg = (
            "Taking into account the previous summary:\n"
            "{summary}\n\n"
            "Summarize the following conversation\n"
            "{conversation}"
        )

        msg = msg.format (summary=summary_message, conversation=messages)
    
        response = llm.invoke ([SystemMessage(content=summarizeMessagePrompt)] + [HumanMessage(content=msg)])
    
        delete_messages = [RemoveMessage(id=m.id) for m in state['messages'][:-2]]
        return {'summary': response.content, 'messages':delete_messages}
    

def llm_call (state:State) -> State:
    msg = state['messages']
    summary = state.get ('summary', "")
    if summary:
        system_message = SystemMessage(content=f"{sys_prompt}\n\n\nSummary of conversation ealier: {summary}")
    else:
        system_message = SystemMessage (content=sys_prompt)
    response = llm.invoke ([system_message] + msg)
    return {'messages': response}


def graphAgent ():
    builder = StateGraph (State)
    builder.add_node ('LLM Call', llm_call)
    builder.add_node ('Summarize', summarize_conversation)

    builder.add_edge (START, 'Summarize')
    builder.add_edge ('Summarize', 'LLM Call')
    builder.add_edge ('LLM Call', END)

    memory = MemorySaver ()
    graph = builder.compile (checkpointer=memory)

    return graph


def chat (query:str, thread_id:str) -> str:
    msg = HumanMessage (content=query)
    config = {'configurable':{'thread_id': thread_id}}

    response = graph.invoke (input={'messages': [msg]}, config=config)
    return response['messages'][-1].content

load_dotenv ()
llm = ChatOpenAI(model="gpt-4.1-nano", api_key=os.getenv ("OPENAI_API_KEY"))

sys_prompt = """You are an expert assistante for using VSCode.
You are to give the user guidance on using VScode.
you are to responde to message on VScode only.
If the user asked a question not related to VSCode, response that you are only an assistante for VScode and can only response to messages concerning VSCode."""

summarizeMessagePrompt = (
        "You are a helpful assistant tasked with summarizing a conversation between a user and a chatbot. "
        "Your goal is to capture the key points, important instructions, and the flow of the discussion, while maintaining the conversational tone and intent.\n\n"
        "Summarize the conversation with the following in mind:\n"
        "- Preserve the question-and-answer structure where relevant.\n"
        "- Maintain the original meaning and intent behind each user and assistant message.\n"
        "- Capture any important decisions, code snippets, steps, or tasks discussed.\n"
        "- Avoid unnecessary repetition or verbose language.\n"
        "- Make sure the summary is detailed enough that, if used later, the assistant can fully understand what has already been discussed.\n\n"
       
    )

graph = graphAgent ()