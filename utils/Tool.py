from types import FunctionType

TOOL_FORMAT = """{
    "tool": "tool_name",
    "tool_kwargs": {
        "arg1": "val1",
        "arg2": "val2"
    }
}
"""

class Tool:
    _box:dict[str,FunctionType] = {}
    CALL_FORMAT = TOOL_FORMAT
    
    def __init__(self, fname:str, description:str, exec:FunctionType, **params:dict[str,any]) -> None:
        self.fname       = fname
        self.description = description
        self.exec        = exec
        self.params      = params
    
    def __str__(self, level=0) -> str:
        fname       = f"**{self.fname}**"
        description = f"\n{level*'    '}- **Description:** {self.description}"
        parameters  = ""
        if len(list(self.params)) > 0:
            parameters  = f"\n{level*'    '}- **Parameters:**"
            for p_name, p_details in self.params.items():
                parameters += f"\n{level*'    '}    - **{p_name}** ({p_details['type']}{', required' if p_details['required'] else ''}): {p_details['description']}."
        return f"{fname}{description}.{parameters}"
    
        
    
    @classmethod 
    def parameter(cls, type_:str, description:str, required:bool=True):
        return {
            'type': type_,
            'description': description,
            'required':required
        }
    
    @classmethod 
    def create(cls, fname:str, description:str, exec:FunctionType=lambda x: '', **params:dict[str,any]):
        new_tool = cls(
            exec = exec,
            fname = fname,
            description = description,
            **params
        )
        cls._box[fname] = new_tool
        return new_tool
    
    
    @classmethod 
    def get(cls, fname:str) -> 'Tool':
        return cls._box.get(fname)
    
    
    @staticmethod
    def box() -> list['Tool']:
        tools_string = ""
        for i, tool in enumerate(Tool._box):
            tools_string += f"{i+1}. {Tool._box[tool].__str__(1)}\n\n"
        return tools_string.strip()
