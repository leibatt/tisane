from typing import List, Any

class InputInterface(object): 
    
    def get_input(self): 
        pass
    
    @classmethod
    def ask_inclusion_prompt(cls, subject: str) -> bool: 
        prompt = f'Would you like to include {subject}?'
        choices = f' Y or N: '

        while True: 
            ans = input(prompt + choices)

            if ans.upper() == 'Y': 
                return True
            elif ans.upper() == 'N': 
                return False
            else: 
                pass
    
    @classmethod
    def ask_multiple_choice_prompt(cls, options: List) -> Any: 
        prompt = f'These cannot be true simultaneously.'
        choices = f' Pick index (starting at 0) to select option in: {options}: '
        while True: 
            idx = int(input(prompt + choices))

            if idx in range(len(options)): 
                # only keep the constraint that is selected. 
                constraint = options[idx] 
                print(f'Ok, going to add {constraint} and remove the others.')
                return constraint
            else:
                print(f'Pick a value in range')
                pass
    
    @classmethod
    def resolve_unsat(cls, facts: List, unsat_core: List) -> List: 
        keep = cls.ask_multiple_choice_prompt(options=unsat_core)
    
        return keep