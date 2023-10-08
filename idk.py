import msvcrt

while True:
    print("sad")
    if msvcrt.kbhit():
        char = msvcrt.getch().decode()
        print(f"You pressed: {char}")
