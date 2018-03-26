class NotFound(Exception):
    """ Tried to find a THING, but it wasn't found. Maybe it's just not be ready yet. """
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)