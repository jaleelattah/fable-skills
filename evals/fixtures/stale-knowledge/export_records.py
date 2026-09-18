import json


def main():
    print(json.dumps(list(range(300))[:100]))


if __name__ == "__main__":
    main()
