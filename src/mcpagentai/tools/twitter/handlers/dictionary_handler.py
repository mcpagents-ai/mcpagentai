import json
from typing import Dict, Any, Optional

from mcpagentai.tools.twitter.query_handler import QueryHandler
from mcpagentai.tools.dictionary_agent import DictionaryAgent

class DictionaryQueryHandler(QueryHandler):
    def __init__(self):
        self.dictionary_agent = DictionaryAgent()
    
    @property
    def query_type(self) -> str:
        return "dictionary"
    
    @property
    def available_params(self) -> Dict[str, str]:
        return {
            "word": "The word to look up the definition for"
        }
    
    def handle_query(self, params: Dict[str, Any]) -> Optional[str]:
        try:
            # Get word from params
            word = params.get("word", "").strip().lower()
            if not word:
                return None
            
            # Get definition
            definition_data = self.dictionary_agent.call_tool("define_word", {"word": word})
            if definition_data and definition_data[0].text:
                result = json.loads(definition_data[0].text)
                if "definition" in result:
                    return f"{result['word']}: {result['definition']}"
            
            return None
            
        except Exception as e:
            print(f"Error in dictionary handler: {e}")
            return None
    
    @property
    def examples(self) -> Dict[str, str]:
        return {
            "Define algorithm": {"word": "algorithm"},
            "What does serendipity mean?": {"word": "serendipity"},
            "Look up the word ephemeral": {"word": "ephemeral"},
            "Definition of paradigm": {"word": "paradigm"}
        } 