import rusty_pipes

if __name__ == '__main__':
    print("Testing subprocess launcher...")
    test1 = rusty_pipes.Open(["python3", "test_proc.py"])
    test1.wait()
    print("test1: This should come after 'Goodbye!'")

    test2 = rusty_pipes.Open(["python3", "test_proc.py"])
    test2.wait_timeout(2)
    print("test2: This should come after 'Hello!'")

    test3 = rusty_pipes.Open(["python3", "test_proc.py"])
    print(test3.exited()) # should be false 
    test3.wait()
    print(test3.exited()) # should be true
    print("test3: This should come after 'True'")
