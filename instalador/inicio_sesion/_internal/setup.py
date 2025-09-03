from cx_Freeze import setup, Executable

setup(
    name="VmPOS",
    version="1.0",
    description="Sistema POS",
    executables=[Executable("main.py")],
)
