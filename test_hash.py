from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test():
    password = "admin12345"
    h = pwd_context.hash(password)
    print(f"Hash: {h}")
    match = pwd_context.verify(password, h)
    print(f"Match: {match}")

if __name__ == "__main__":
    test()
