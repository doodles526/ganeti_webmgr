import types

class CallProxy(object):
    """ Proxy for a method that will record calls to it.  To use this class
    monkey patch the original method using an instance of this class
    
    setting the enabled flag can enable/disable whether the method is actually
    executed when it is called, or just recorded.
    """
    def __init__(self, func, enabled=True, response=None, **kwargs):
        """
        :parameters:
            func: function to proxy
            enabled: whether to call the wrapped function
            kwargs: kwargs passed to all calls.  may be overwritten by kwargs
                    passed to function
        """
        self.func = func
        self.calls = []
        self.enabled = enabled
        self.kwargs = kwargs
        self.response = response
        
        if func:
            self.matching_function = self.create_matching_function(func)
    
    def assertCalled(self, testcase, *args, **kwargs):
        """
        Assertion function for checking if a callproxy was called
        """
        f = self.func
        calls = self.calls
        if args or kwargs:
            #detailed match
            for t in calls:
                args_, kwargs_ = t
                if args_==args and kwargs_==kwargs:
                    return t
            testcase.fail("exact call (%s) did not occur: %s" % (f, calls))
            
        else:
            # simple match
            testcase.assert_(calls, "%s was not called: %s" % (f, calls))
            return calls[0]

    def assertNotCalled(self, testcase, *args, **kwargs):
        """
        Assertion function for checking if callproxy was not called
        """
        f = self.func
        calls = self.calls
        if args or kwargs:
            #detailed match
            for t in calls:
                args_, kwargs_ = t
                if args_==args and kwargs_==kwargs:
                    testcase.fail("exact call (%s) was made: %s" % (f, calls))
        else:
            # simple match
            testcase.assertFalse(calls, '%s was not called' % f)
        
    def enable(self):
        self.enabled = True
    
    def disable(self):
        self.enabled = False
        
    def reset(self):
        self.calls = []
        
    def __call__ (self, *args, **kwargs):
        response = None
        kwargs_ = {}
        kwargs_.update(self.kwargs)
        kwargs_.update(kwargs)
        self.calls.append((args, kwargs_))
        
        if self.enabled:
            response = self.func(*args, **kwargs_)
        elif self.func:
            # call matching call, this ensures the args are checked even when
            # the real function isn't actually called
            #
            # pass in the instance if it is set.  if this was a bound method
            # then it will fail without self passed.
            if self.func.im_self:
                self.matching_function(self.func.im_self, *args, **kwargs)
            else:
                self.matching_function(*args, **kwargs)
        
        return self.response if self.response != None else response
        
    def create_matching_function(self, func):
        """
        constructs a function with a method signature that matches the
        function that is passed in.  The resulting function does not actually
        do anything.  It is only used for verifying arguments to the call match.
        
        The function is constructed from a combination of properties from an
        inner function and the function passed in.
        """
        def base(): pass
        
        base_code = base.__code__
        code = func.__code__
        
        name = 'MATCHING_PROXY: %s' % func.__name__
        
        new_code = types.CodeType( \
            code.co_argcount, \
            code.co_nlocals, \
            base_code.co_stacksize, \
            code.co_flags, \
            base_code.co_code, \
            base_code.co_consts, \
            base_code.co_names, \
            code.co_varnames, \
            base_code.co_filename, \
            name, \
            base_code.co_firstlineno, \
            base_code.co_lnotab)
        
        return types.FunctionType(new_code, func.func_globals, \
                                  name, func.func_defaults)

    @classmethod
    def patch(cls, instance, name, *args, **kwargs):
        """
        Helper function for patching a function on an instance.  useful since
        patching an instance requires a bit more work to ensure the proxy works
        correctly.
        
        :parameters:
            * instance: instance to patch
            * name: name of function to 
        """
        func = getattr(instance, name)
        proxy = CallProxy(func, *args, **kwargs)
        setattr(instance, name, proxy)