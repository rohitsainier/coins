import hashlib
import requests
import csv
import os


def sha256(data):
    digest = hashlib.new("sha256")
    digest.update(data)
    return digest.digest()


def ripemd160(x):
    d = hashlib.new("ripemd160")
    d.update(x)
    return d.digest()


def b58(data):
    B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    if data[0] == 0:
        return "1" + b58(data[1:])

    x = sum([v * (256 ** i) for i, v in enumerate(data[::-1])])
    ret = ""
    while x > 0:
        ret = B58[x % 58] + ret
        x = x // 58

    return ret


class Point:
    def __init__(self,
                 x=0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
                 y=0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
                 p=2**256 - 2**32 - 2**9 - 2**8 - 2**7 - 2**6 - 2**4 - 1):
        self.x = x
        self.y = y
        self.p = p

    def __add__(self, other):
        return self.__radd__(other)

    def __mul__(self, other):
        return self.__rmul__(other)

    def __rmul__(self, other):
        n = self
        q = None

        for i in range(256):
            if other & (1 << i):
                q = q + n
            n = n + n

        return q

    def __radd__(self, other):
        if other is None:
            return self
        x1 = other.x
        y1 = other.y
        x2 = self.x
        y2 = self.y
        p = self.p

        if self == other:
            l = pow(2 * y2 % p, p-2, p) * (3 * x2 * x2) % p
        else:
            l = pow(x1 - x2, p-2, p) * (y1 - y2) % p

        newX = (l ** 2 - x2 - x1) % p
        newY = (l * x2 - l * newX - y2) % p

        return Point(newX, newY)

    def toBytes(self):
        x = self.x.to_bytes(32, "big")
        y = self.y.to_bytes(32, "big")
        return b"\x04" + x + y


def getPublicKey(privkey):
    SPEC256k1 = Point()
    pk = int.from_bytes(privkey, "big")
    hash160 = ripemd160(sha256((SPEC256k1 * pk).toBytes()))
    address = b"\x00" + hash160

    address = b58(address + sha256(sha256(address))[:4])
    return address


def getWif(privkey):
    wif = b"\x80" + privkey
    wif = b58(wif + sha256(sha256(wif))[:4])
    return wif


def get_btc_balance(address):
    api_url = f"https://blockchain.info/balance?active={address}"

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            balance = data[address]["final_balance"]
            return balance
        else:
            print("Error:", response.status_code)
            return None
    except Exception as e:
        print("Error occurred:", e)
        return None


# Initialize counter
counter = 0

# CSV file header
fields = ["Bitcoin Address",
          "Private Key (hex)", "Balance (BTC)"]

# CSV file name
csv_file = "bitcoin_addresses.csv"

# Infinite loop to generate and save Bitcoin addresses
with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    # writer.writerow(fields)  # Write header row

    while True:
        randomBytes = os.urandom(32)
        private_key_hex = getWif(randomBytes)
        addr_str = getPublicKey(randomBytes)

        # Increment the counter
        counter += 1

        # Check the balance of the address
        balance = get_btc_balance(addr_str)
        # print private_key_hex, public_key_hex, addr_str
        print(f"Bitcoin Address {counter}:", addr_str, "Balance:", balance,
              "Private Key:", private_key_hex)
        # If the balance is non-zero, save the address to the CSV file
        if balance is not None and float(balance) > 0:
            print(f"Bitcoin Address {counter}:", addr_str, "Balance:", balance)

            # Write to CSV file
            row = [addr_str, private_key_hex, balance]
            writer.writerow(row)

        # Break the loop after generating 10 addresses
        if counter >= 10:
            break


# Check if CSV file is empty
if os.stat(csv_file).st_size == 0:
    print("CSV file is empty after processing all addresses.")
else:
    print("CSV file is not empty. It contains the generated addresses and their balances.")
