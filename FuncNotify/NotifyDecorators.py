import time
import warnings
from collections import deque
from dotenv import dotenv_values

from .NotifyMethods import *

NOTIFY_TYPE=None
ENV_DICT=None

# Main decorator 
def time_func(func=None, NotifyMethod: str=None, use_env: bool=False, env_path: str=".env", 
              update_env: bool=False, multi_target: list=None, multi_env: list=None, *dec_args, **dec_kwargs): 
    """Decorator for how to handle a notify function. Allows for additional arguments in the decorator
    and support for args like emails/api keys. Is able to handle errors.

    Args:
        func (function, optional): In case you want to use time_func as a decorator without argumetns, 
        NotifyMethod (str, optional): Specifies the type of method used to notify user, selected 
        from NotifyType. Defaults to None.
        use_env (str, optional): Loads .env file envionment variables. Defaults to False
        env_path (str, optional): path to .env file. Defaults to ".env".
        update_env (bool, optional): whether to update the .env file to current. Always updatess on 
        initialization. Defaults to False.
        
        multi_target (str, optional): path to .env file. Defaults to ".env".
        multi_env (list[str], optional): whether to update the .env file to current. Always updatess on 
        initialization. Defaults to False.

        

    Returns:
        function: decorator function for timing
    """    
    notify_obj_list=[]
    
    global NOTIFY_TYPE
    global ENV_DICT
    
    if NOTIFY_TYPE is None:
        NOTIFY_TYPE = NotifyMethods.get_cls_registry()
    
    if update_env or ENV_DICT is None:
        ENV_DICT={**os.environ, **dotenv_values(env_path)} if use_env else {} 
        
    if multi_env and multi_target: 
        raise Exception("variables are exclusive") # TODO write custom exceptions and make the flow more robust
    elif multi_target :
        for target in multi_target:
            notify_obj_list.append(
                NOTIFY_TYPE.get(target.get('NotifyMethod', NotifyMethod), 
                                default_notify)(environ=ENV_DICT,
                                                **target,
                                                *dec_args, 
                                                **dec_kwargs)
                                )
    elif multi_env:
         for env in multi_env:
            spec_dict = {**ENV_DICT, **dotenv_values(env)}
            notify_obj_list.append(
                NOTIFY_TYPE.get(NotifyMethod if NotifyMethod else spec_dict.get("DEFAULTNOTIFY", "NotFound"), 
                                default_notify)(environ=spec_dict,
                                                *dec_args, 
                                                **dec_kwargs)
                                )
    else:
        notify_obj_list.append(
            NOTIFY_TYPE.get(NotifyMethod if NotifyMethod else ENV_DICT.get("DEFAULTNOTIFY", "NotFound"), 
                            default_notify)(environ=ENV_DICT,
                                            *dec_args, 
                                            **dec_kwargs)
                            )
    
    def time_function(func_inner):
        """Inner wrapped function, used for timing and control, necessary to give the
        decorator additional arguments that can be passed in

        Args:
            func_inner (function): passes function and arguments down below to the final timer
        """         
        def timer(*func_args, **func_kwargs):
            """Takes arguments from main function and passes it down

            Returns:
                Object: returns func's output
            """           
            return timer_base(func_inner, notify_obj_list, *func_args, **func_kwargs)
        return timer

    if callable(func): # Checks time_func was used as a decorator (@time_func vs @time_func(NotifyMethod="Slack"))
        return time_function(func)

    return time_function


def timer_base(func, NotifyObjList: list, *args, **kwargs): 
    """ Timer base, depending on the type of object of NotifyObj, it will notify the 
    user of the method and time the function. Errors are raised in the same method
    Leverages a factory that created the object and utilizes the abstract methodss

    Args:
        func (function): Any function
        NotifyObjList (list[NotifyMethods]): Object from abstract class that indicates how the user is nootified

    Raises:
        ex (Exception): Any Exception can be excepted then raised, this ensures exceptions aren't 
        interuptted but the user is notified

    Returns:
        Object: Returns whatever the function returns
    """    
    try:
        deque(map(lambda NotifyObj: NotifyObj.send_start_MSG(func), NotifyObjList), maxlen=0) # sends message on each item in list
        start = time.time()                                                                   # without using too much memor
        
        result = func(*args, **kwargs)
        
        end = time.time()
        deque(map(lambda NotifyObj: NotifyObj.send_end_MSG(func, end-start), NotifyObjList), maxlen=0)
    
    except Exception as ex: 
        deque(map(lambda NotifyObj: NotifyObj.send_start_MSG(func, ex), NotifyObjList), maxlen=0)
        raise ex

    return result

def default_notify(*args, **kwargs):
    warnings.warn(f"Invalid NotifyMethod type specified, will use `PrintMethod`, \
                    select a type within this criteria: {NOTIFY_TYPE.keys()}")
    return NOTIFY_TYPE["Print"](*args, **kwargs)
