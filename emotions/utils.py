import subprocess
from pathlib import Path
from typing import List, Set, Tuple, Union
from pydantic import BaseModel

class Shell(BaseModel):
    verbose: bool = True

    @classmethod
    def format_kwargs(cls, **kwargs) -> str:
        outputs = []
        for k, v in kwargs.items():
            k = k.replace("_", "-")
            k = f"--{k}"
            outputs.extend([k, str(v)])
        return " ".join(outputs)

    def run_command(self, command: str) -> str:
        # Continuously print outputs for long-running commands
        # Refer: https://fabianlee.org/2019/09/15/python-getting-live-output-from-subprocess-using-poll/
        print(dict(command=command))
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        outputs = []

        while True:
            if process.poll() is not None:
                break
            o = process.stdout.readline().decode()
            if o:
                outputs.append(o)
                if self.verbose:
                    print(o.strip())

        return "".join(outputs)

    def run(self, command: str, *args, **kwargs) -> str:
        args = [str(a) for a in args]
        command = " ".join([command] + args + [self.format_kwargs(**kwargs)])
        return self.run_command(command)
