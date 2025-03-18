class BankNode:
    def __init__(self, name):
        self.name = name
        self.net_amount = 0
        self.types = set()
        self.next = None

class BankLinkedList:
    def __init__(self):
        self.head = None

    def append(self, bank):
        if not self.head:
            self.head = bank
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = bank

    def find_index(self, name):
        current = self.head
        index = 0
        while current:
            if current.name == name:
                return index
            index += 1
            current = current.next
        return -1

    def get_by_index(self, index):
        current = self.head
        i = 0
        while current:
            if i == index:
                return current
            i += 1
            current = current.next
        return None

    def get_list(self):
        current = self.head
        banks = []
        while current:
            banks.append(current)
            current = current.next
        return banks

    def __len__(self):
        current = self.head
        count = 0
        while current:
            count += 1
            current = current.next
        return count

def get_min_index(banks):
    min_amount = float('inf')
    min_index = -1
    current = banks.head
    index = 0
    while current:
        if current.net_amount < min_amount and current.net_amount != 0:
            min_index = index
            min_amount = current.net_amount
        index += 1
        current = current.next
    return min_index

def get_simple_max_index(banks):
    max_amount = float('-inf')
    max_index = -1
    current = banks.head
    index = 0
    while current:
        if current.net_amount > max_amount and current.net_amount != 0:
            max_index = index
            max_amount = current.net_amount
        index += 1
        current = current.next
    return max_index

def get_max_index(banks, min_index):
    min_bank = banks.get_by_index(min_index)
    max_amount = float('-inf')
    max_index = -1
    matching_type = None

    index = 0
    current = banks.head
    while current:
        if current.net_amount > 0:
            common_types = min_bank.types.intersection(current.types)
            if common_types:
                if current.net_amount > max_amount:
                    max_amount = current.net_amount
                    max_index = index
                    matching_type = next(iter(common_types))
        index += 1
        current = current.next
    return max_index, matching_type

def print_ans(ans_graph, banks):
    print("\nThe transactions for minimum cash flow are as follows:\n")
    for i in range(len(banks)):
        for j in range(len(banks)):
            if ans_graph[i][j][0] != 0:
                print(f"{banks[i].name} pays Rs {ans_graph[i][j][0]} to {banks[j].name} via {ans_graph[i][j][1]}")

def minimize_cash_flow(num_banks, banks, transactions):
    graph = [[0] * num_banks for _ in range(num_banks)]
    bank_list = banks.get_list()

    # Calculate net amount for each bank
    for debtor, creditor, amount in transactions:
        graph[debtor][creditor] += amount

    for i in range(num_banks):
        amount = sum(graph[j][i] for j in range(num_banks)) - sum(graph[i][j] for j in range(num_banks))
        bank_list[i].net_amount = amount

    ans_graph = [[(0, "") for _ in range(num_banks)] for _ in range(num_banks)]

    while any(bank.net_amount != 0 for bank in bank_list):
        min_index = get_min_index(banks)
        max_index, matching_type = get_max_index(banks, min_index)

        if max_index == -1:
            simple_max_index = get_simple_max_index(banks)
            min_bank = banks.get_by_index(min_index)
            max_bank = banks.get_by_index(simple_max_index)

            transaction_amount = abs(min_bank.net_amount)
            ans_graph[min_index][simple_max_index] = (transaction_amount, next(iter(max_bank.types)))
            max_bank.net_amount += min_bank.net_amount
            min_bank.net_amount = 0
        else:
            min_bank = banks.get_by_index(min_index)
            max_bank = banks.get_by_index(max_index)

            transaction_amount = min(abs(min_bank.net_amount), max_bank.net_amount)
            ans_graph[min_index][max_index] = (transaction_amount, matching_type)
            min_bank.net_amount += transaction_amount
            max_bank.net_amount -= transaction_amount

    print_ans(ans_graph, bank_list)
def main():
    print("\n\t\t\t\t********************* Welcome to CASH FLOW MINIMIZER SYSTEM ***********************\n")

    while True:
        print("Menu:")
        print("1. Enter number of banks")
        print("2. Enter bank details")
        print("3. Enter transactions")
        print("4. Minimize cash flow")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            num_banks = int(input("Enter the number of banks: "))
        elif choice == "2":
            banks = BankLinkedList()
            for _ in range(num_banks):
                bank_name, num_types, *types = input("Enter bank name, number of types, and types (separated by spaces): ").split()
                bank = BankNode(bank_name)
                bank.types.update(types)
                banks.append(bank)
        elif choice == "3":
            num_transactions = int(input("Enter the number of transactions: "))
            transactions = []
            for _ in range(num_transactions):
                debtor_name, creditor_name, amount = input("Enter debtor name, creditor name, and amount (separated by spaces): ").split()
                amount = int(amount)
                debtor_index = banks.find_index(debtor_name)
                creditor_index = banks.find_index(creditor_name)
                transactions.append((debtor_index, creditor_index, amount))
        elif choice == "4":
            minimize_cash_flow(num_banks, banks, transactions)
        elif choice == "5":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()