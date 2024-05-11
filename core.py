#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Union

from langchain_core.runnables import chain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools import StructuredTool, BaseTool
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_core.agents import AgentAction, AgentFinish
from langchain_openai.chat_models import ChatOpenAI


def api(fn):
    """mock net api"""
    return fn


class Client:
    def __init__(self, prompt) -> None:
        self.tool_map = {}
        self.equipment_map = {}
        self.prompt = prompt
        self.llm = self.init_llm()

    def init_llm(self):
        tools = []
        prompt = PromptTemplate.from_template(self.prompt)
        chain = prompt | ChatOpenAI().bind_tools(tools=tools) | OpenAIToolsAgentOutputParser() | self.tool_call()
        return chain

    @api
    def connect(self, toolkit: 'ToolkitServer'):
        _tool_map = toolkit.get_tool_map()
        self.equipment_map[toolkit.name] = toolkit
        self.tool_map.update(_tool_map)

    def tool_call(self, output: Union[List[AgentAction], AgentFinish]):
        @chain
        def fn():
            if isinstance(output, AgentFinish):
                return {
                    'type': 'chat',
                    **output.return_values
                }

            toolkit_name = None
            for _e_name, toolkit in self.equipment_map.items():
                if action.tool in toolkit.feature_map:
                    e_name = _e_name
                    break
            assert toolkit_name

            for action in output:
                server: ToolkitServer = self.equipment_map[e_name]
                tool_output = server.use(action.tool_input)

            return {
                'type': 'tool',
                'toolkit': toolkit_name,
                'tool_name': action.tool,
                'tool_input': action.tool_input,
                'tool_output': tool_output
            }
        return fn

    @api
    def chat(self, msg):
        return self.llm.invoke(msg)


class ToolkitServer:
    def __init__(self, name: str, features: List['Feature']) -> None:
        self.name = name
        self.feature_map = {f.name: f for f in features}

    @api
    def get_tool_map(self):
        schemas_map = {}
        for f in self.feature_map.values():
            schemas_map[f.name] = f.schema()
        return schemas_map
    
    @api
    def use(self, tool_choice: str, tool_input: dict):
        feature = self.feature_map.get(tool_choice)
        return feature.run(tool_input)
    

class Feature(StructuredTool):
    """define detail Feature input run"""
    pass