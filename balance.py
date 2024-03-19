import requests
import csv
import os
from generate import getWif, getPublicKey


def get_btc_balance(address):
    api_url = f"https://blockchain.info/multiaddr?active={address}"

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            addresses_data = data.get("addresses", [])
            for address in addresses_data:
                btc_address = address["address"]
                balance = address["final_balance"]
                if balance > 0:
                    print(f"Address: {btc_address}, Balance: {balance}")
                    # update btc_address_list.csv with balance which already contain address and private key in csv
                    with open("btc_address_list.csv", "r") as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                        for row in rows:
                            if row[0] == btc_address:
                                row[2] = balance
                                break

                    with open("btc_address_list.csv", "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerows(rows)
                else:
                    print(f"Address: {btc_address}, Balance: 0")
        else:
            print("Error:", response.status_code)
            return None
    except Exception as e:
        print("Error occurred:", e)
        return None


def generate_addresses():
    combined_addresses = ""
    fields = ["Bitcoin Address", "Private Key (hex)", "Balance (BTC)"]

    # check if file already exists or not, if exist append the new data
    with open("btc_address_list.csv", "a", newline="") as f:
        writer = csv.writer(f)
        # if the file is empty, write the header
        if f.tell() == 0:
            writer.writerow(fields)
        # run loop 200 times
        for i in range(200):
            randomBytes = os.urandom(32)
            private_key_hex = getWif(randomBytes)
            addr_str = getPublicKey(randomBytes)
            writer.writerow([addr_str, private_key_hex, 0])
            combined_addresses += addr_str + "|"

    return combined_addresses


if __name__ == "__main__":
    while True:
        combined_addresses = generate_addresses()
        get_btc_balance(combined_addresses)
