
import cProfile, pstats, os
def func_std_string(func_name): # match what old profile produced
    if func_name[:2] == ('~', 0):
        # special case for built-in functions
        name = func_name[2]
        if name.startswith('<') and name.endswith('>'):
            return '{%s}' % name[1:-1]
        else:
            return name
    else:
        return "%s:%d(%s)" % func_name

def f8(x):
    return "%8.3f" % x

class CustomPstats(pstats.Stats):
    def __init__(self, *args, **kwds):
        pstats.Stats.__init__(self, *args, **kwds)
        
    def write_stats(self, *amount):
        msg = ''
        for filename in self.files:
            msg +=  str(filename) + '\n'
        #if self.files: msg += str(self.stream) + '\n'
        indent = ' ' * 8
        for func in self.top_level:
            msg +=   str(indent)+ str(func_get_function_name(func))+"\n"

        msg += str(indent) + str(self.total_calls)+ "function calls" + '\n'
        if self.total_calls != self.prim_calls:
            msg +=  "(%d primitive calls)" % self.prim_calls + '\n'
        msg +=  "in %.3f CPU seconds" % self.total_tt + '\n'
        #msg +=  str(self.stream) + '\n'
       
        width = self.max_name_len
        if self.fcn_list:
            list = self.fcn_list[:]
            temp_msg = "   Ordered by: " + self.sort_type + '\n'
        else:
            list = self.stats.keys()
            temp_msg = "   Random listing order was used\n"

        for selection in amount:
            list, temp_msg = self.eval_print_amount(selection, list, temp_msg)

        count = len(list)

        if not list:
            width, list = 0, list
        else:
            msg +=   str(temp_msg) + '\n'
            if count < len(self.stats):
                width = 0
                for func in list:
                    if  len(func_std_string(func)) > width:
                        width = len(func_std_string(func))
       
            width, list = width+2, list
        if list:
            msg += '   ncalls  tottime  percall  cumtime  percall'
            msg +=  ' filename:lineno(function)' + "\n"
            for func in list:
                cc, nc, tt, ct, callers = self.stats[func]
                c = str(nc)
                if nc != cc:
                    c = c + '/' + str(cc)
                msg +=  str( c.rjust(9)) 
                msg +=  str(f8(tt)) 
                if nc == 0:
                    msg += str(' '*8) 
                else:
                    msg +=  str(f8(tt/nc)) 
                msg += str(f8(ct)) 
                if cc == 0:
                    msg += str( ' '*80) 
                else:
                    msg += str(f8(ct/cc)) 
                msg +=  " " + str(func_std_string(func)) + '\n'
            msg += str(self.stream) + '\n'
            #msg += str(self.stream) + '\n'
        return self, msg
            
def profile( fn, name='profile.txt',*args, **kw):
    import cProfile, pstats, os
    global call_result
    def call():
        global call_result
        call_result = fn(*args, **kw)
    cProfile.runctx('call()', dict(call=call), {}, 'profile.txt')
    stats = CustomPstats('profile.txt')
    #sort by cumlative time
    stats.sort_stats('time')
    stats.print_stats(50)
    """
        filename = 'profile_cum_' + name
        _, msg = stats.write_stats(50)
        f = file(filename, 'wb')
        f.write(msg)
        f.close()
        #sort by time
        stats.sort_stats('time')
        _, msg = stats.write_stats(50)
        filename = 'profile_time_' + name
        f = file(filename, 'wb')
        f.write(msg)
        f.close()
        # sort by number of calls
        stats.sort_stats('call')
        _, msg = stats.write_stats(50)
        filename = 'profile_call_' + name
        f = file(filename, 'wb')
        f.write(msg)
        f.close()
        os.unlink('profile.txt')
    """
    return call_result

