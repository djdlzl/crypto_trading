from api.upbit_api import UpbitApi



if __name__ == "__main__":
    upbit_api = UpbitApi()
    accounts = upbit_api.get_accounts()
    print(accounts)
    