"""Create a local account without putting a password in a command or .env."""

from getpass import getpass

from security import add_user


if __name__ == "__main__":
    print("Create a local travel-planner account. No default passwords are provided.")
    name = input("Username (lowercase): ").strip()
    password = getpass("Password (at least 12 characters; typing is hidden): ")
    if password != getpass("Repeat password: "):
        raise SystemExit("Passwords did not match. Run this script again.")
    try:
        add_user(name, password)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print("Account created. Keep .private/users.json out of your submission.")
