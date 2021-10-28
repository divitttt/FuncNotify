import argparse
import subprocess

import re

from FuncNotify import *

class ParseKwargs(argparse.Action):
    """Parses for the format `arg=val` parses for either strings or bools exclusively, no ints
    """    
    translation_dict = {"true":  True,
                         "True":  True,
                         "false": False,
                         "False": False,}
    
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, dict())
        for value in values:
            if value is not None:
                key, value = value.split('=')
                value = ParseKwargs.translation_dict.get(value, value)
                
                if key in getattr(namespace, self.dest):
                    if isinstance(getattr(namespace, self.dest)[key], list):
                         getattr(namespace, self.dest)[key].append(value)
                    else:
                        getattr(namespace, self.dest)[key] = [getattr(namespace, self.dest)[key], value]
                else:
                    getattr(namespace, self.dest)[key] = value



def main():
    parsed_remain_arg = []
    def kwarg_form(arg):
        """Validate text in form "key=val" internal func to access
        parsed_remain_arg to ad to 
        """
        if not re.match('^[a-zA-Z0-9_]+(=[^\s]+)$', arg):
            parsed_remain_arg.append(arg)
            return
        return arg
    
    parser = argparse.ArgumentParser(
        description="FuncNotify - Be notified securely when your function/script completes. " \
                    "Store all your variables in a `.env` file and let us do the work for you " \
                    "To input arguments, use --kwargs followed by `{arg}=value`")
    parser.add_argument('-k', '--kwargs', nargs='*', type=kwarg_form, action=ParseKwargs)
    
    args, remaining_args = parser.parse_known_args()
    
    kwargs = {**args.kwargs} if args.kwargs else {}
    
    def sub_run(): 
        if remaining_args or parsed_remain_arg:
            return subprocess.run([*remaining_args, *parsed_remain_arg], check=True)
        else:
            print("No command specified to be executed")
    
    sub_run.__name__ = " ".join([*remaining_args, *parsed_remain_arg])
    time_func(sub_run, **kwargs)()


if __name__ == "__main__":
    """When `FuncNotify` is called from the CLI, we go to this function"""
    main() 