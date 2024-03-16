import binascii
import ecdsa
import hashlib
import base58
import requests
import csv
import time
import os


def generate_bitcoin_address():
    private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    private_key_bytes = private_key.to_string()

    # Derive the public key
    public_key = private_key.get_verifying_key().to_string()

    # Create a Bitcoin address from the public key
    prefixes = {'P2PKH': b'\x00', 'P2SH': b'\x05'}
    version_byte = prefixes['P2PKH']
    ripemd160 = hashlib.new('ripemd160')
    ripemd160.update(hashlib.sha256(public_key).digest())
    checksum = hashlib.sha256(hashlib.sha256(
        version_byte + ripemd160.digest()).digest()).digest()[0:4]
    address_bytes = version_byte + ripemd160.digest() + checksum
    address = base58.b58encode(binascii.unhexlify(address_bytes.hex()))
    addr_str = address.decode()

    return private_key_bytes.hex(), public_key.hex(), addr_str


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
          "Private Key (hex)", "Public Key (hex)", "Balance (BTC)"]

# CSV file name
csv_file = "bitcoin_addresses.csv"

# Infinite loop to generate and save Bitcoin addresses
with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    # writer.writerow(fields)  # Write header row

    while True:
        private_key_hex, public_key_hex, addr_str = generate_bitcoin_address()

        # Increment the counter
        counter += 1

        # Check the balance of the address
        balance = get_btc_balance(addr_str)
        print("Bitcoin Address:", addr_str, counter)
        # If the balance is non-zero, save the address to the CSV file
        if balance is not None and float(balance) > 0:
            print(f"Bitcoin Address {counter}:", addr_str, "Balance:", balance)

            # Write to CSV file
            row = [addr_str, private_key_hex, public_key_hex, balance]
            writer.writerow(row)

        # Delay for 1 second before making the next request
        # time.sleep(1)

        # Break the loop after generating 10 addresses
        if counter >= 10:
            break


# Check if CSV file is empty
if os.stat(csv_file).st_size == 0:
    print("CSV file is empty after processing all addresses.")
else:
    print("CSV file is not empty. It contains the generated addresses and their balances.")
