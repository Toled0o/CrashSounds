# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Supervisão de um processo filho e seus descendentes, sem matar outros apps."""

from __future__ import annotations

import os
import signal
import subprocess
import sys


class ChildGuard:
    def __init__(self, process: subprocess.Popen):
        self.process = process
        self.job = None
        self.kernel = None
        if sys.platform != "win32":
            return
        import ctypes
        from ctypes import wintypes

        size = ctypes.c_size_t

        class Limits(ctypes.Structure):
            _fields_ = [
                ("process_time", ctypes.c_longlong),
                ("job_time", ctypes.c_longlong),
                ("flags", wintypes.DWORD),
                ("min_ws", size),
                ("max_ws", size),
                ("active", wintypes.DWORD),
                ("affinity", size),
                ("priority", wintypes.DWORD),
                ("scheduling", wintypes.DWORD),
            ]

        class Counters(ctypes.Structure):
            _fields_ = [
                (name, ctypes.c_ulonglong)
                for name in (
                    "read_ops",
                    "write_ops",
                    "other_ops",
                    "read_bytes",
                    "write_bytes",
                    "other_bytes",
                )
            ]

        class Extended(ctypes.Structure):
            _fields_ = [
                ("limits", Limits),
                ("io", Counters),
                ("process_memory", size),
                ("job_memory", size),
                ("peak_process", size),
                ("peak_job", size),
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel.SetInformationJobObject.restype = wintypes.BOOL
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.CreateJobObjectW(None, None)
        if not handle:
            raise OSError(ctypes.get_last_error(), "Não foi possível supervisionar o download.")
        info = Extended()
        info.limits.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            kernel.CloseHandle(handle)
            raise OSError(ctypes.get_last_error(), "Falha ao configurar supervisão de download.")
        if not kernel.AssignProcessToJobObject(handle, wintypes.HANDLE(int(process._handle))):
            kernel.CloseHandle(handle)
            raise OSError(
                ctypes.get_last_error(), "Este ambiente não permite supervisionar o download."
            )
        self.kernel, self.job = kernel, handle

    def close(self):
        if self.job:
            self.kernel.CloseHandle(self.job)
            self.job = None
        elif sys.platform != "win32":
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=5)
