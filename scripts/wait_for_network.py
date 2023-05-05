from src.utils import connection_is_active

if not connection_is_active():
    print("No connection could be established")
    quit()
