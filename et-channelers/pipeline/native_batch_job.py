"""Windows Job Object for one owned child tree; no process discovery or launch."""
import ctypes as c
from ctypes import wintypes as w
import time


class BasicLimit(c.Structure):
    _fields_ = [('user', c.c_longlong), ('job', c.c_longlong), ('flags', w.DWORD),
                ('min_ws', c.c_size_t), ('max_ws', c.c_size_t), ('active_limit', w.DWORD),
                ('affinity', c.c_size_t), ('priority', w.DWORD), ('scheduling', w.DWORD)]


class Io(c.Structure):
    _fields_ = [(name, c.c_ulonglong) for name in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]


class Extended(c.Structure):
    _fields_ = [('basic', BasicLimit), ('io', Io), ('process_mem', c.c_size_t), ('job_mem', c.c_size_t),
                ('peak_process_mem', c.c_size_t), ('peak_job_mem', c.c_size_t)]


class Accounting(c.Structure):
    _fields_ = [(name, c.c_longlong) for name in ('user','kernel','period_user','period_kernel')] + [
        (name, w.DWORD) for name in ('page_faults','processes','active','terminated')]


class OwnedJob:
    def __init__(self):
        self.kernel = c.WinDLL('kernel32', use_last_error=True)
        definitions = {'CreateJobObjectW': ([c.c_void_p,w.LPCWSTR],w.HANDLE),
            'SetInformationJobObject': ([w.HANDLE,c.c_int,c.c_void_p,w.DWORD],w.BOOL),
            'AssignProcessToJobObject': ([w.HANDLE,w.HANDLE],w.BOOL),
            'QueryInformationJobObject': ([w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.c_void_p],w.BOOL),
            'TerminateJobObject': ([w.HANDLE,w.UINT],w.BOOL), 'CloseHandle': ([w.HANDLE],w.BOOL)}
        for name,(args,result) in definitions.items():
            fn=getattr(self.kernel,name); fn.argtypes=args; fn.restype=result
        self.handle=self.kernel.CreateJobObjectW(None,None)
        if not self.handle: raise RuntimeError('job_create_failed')
        limits=Extended(); limits.basic.flags=0x2000  # KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle,9,c.byref(limits),c.sizeof(limits)):
            self.close(); raise RuntimeError('job_limits_failed')

    def attach(self, process):
        if not self.kernel.AssignProcessToJobObject(self.handle,w.HANDLE(int(process._handle))):
            raise RuntimeError('job_assign_failed')

    def stop_and_verify(self):
        if not self.kernel.TerminateJobObject(self.handle,3): raise RuntimeError('job_stop_failed')
        end=time.monotonic()+5
        while time.monotonic()<end:
            stats=Accounting()
            if not self.kernel.QueryInformationJobObject(self.handle,1,c.byref(stats),c.sizeof(stats),None):
                raise RuntimeError('job_query_failed')
            if stats.active==0: return True
            time.sleep(.05)
        return False

    def close(self):
        if self.handle: self.kernel.CloseHandle(self.handle); self.handle=None
