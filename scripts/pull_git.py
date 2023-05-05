from decouple import config
from src.utils import connection_is_active
import git

if not connection_is_active():
    print("No connection could be established")
    quit()

g = git.cmd.Git(config("PROJECT_DIR"))
print(g.pull())
