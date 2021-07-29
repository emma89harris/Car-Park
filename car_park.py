class DB:
    
    total_spaces = 36
    emergency_spaces = 4
    weather = None
    
    def __init__(self, cursor):
        self._cursor = cursor
        self._availability = {
            "Disabled": 0,
            "ED / MD": 0,
            "Critical Worker / Tenure": 0,
            "Other": 15
        }
        self._fields = {
            "EmployeeID": int,
            "RegistrationNo": str,
            "Status": str,
            "EcoCar": bool,
            "Distance": int,
            "ReservedDates": str
        }

    def get_cursor(self):
        return self._cursor

    def get_availability(self):
        return self._availability

    def get_fields(self):
        return self._fields

    def get_date_today(self):
        """
        Returns today's date in the format day-month-year.

        returns: str
        """
        today = str(datetime.date.today()).split("-")
        today.reverse()
        return "-".join(today)

    def get_no_of_free_spaces(self):
        """
        Returns total number of free spaces in car park.

        returns: int
        """
        return sum(list(self._availability.values()))

    def get_single_criterion_sql(self, criteria, symbol):
        """
        Returns a single SQL criterion - e.g., Distance = 40.

        criteria: tuple of format (str, any) <=> (fieldname, fieldvalue) - e.g., ("EmployeeID", 4)
        symbol: str

        returns: str
        """
        # criteria is a single selection - a tuple with field name and value
        field, value = criteria[0], criteria[1]
        if self._fields[field] == str:
            statement = str(field) + " " + symbol + " " + "'" + str(value) + "'"
        else:
            statement = str(field) + " " + symbol + " " + str(value)
        
        return statement

    def get_whole_statement_sql(self, criteria_set, decision_word):
        """
        Returns a whole SQL statement - e.g, EmployeeID = 4 AND Distance > 20.

        criteria_set: dict with objects of the form {str: (str, any)} <=> {fieldname: (symbol, fieldvalue)} - e.g., {"EmployeeID": ("=", 4)}
        decision_word: str - e.g., "AND"; ","

        returns: str
        """
        whole_statement = ""
        fields = list(criteria_set.keys())

        for field in fields:
            symbol = criteria_set[field][0]
            value = criteria_set[field][1]

            if fields.index(field) < len(criteria_set) - 1:
                whole_statement += self.get_single_criterion_sql((field, value), symbol) + " " + decision_word + " "
            else:
                whole_statement += self.get_single_criterion_sql((field, value), symbol)

        return whole_statement

    def insert_record(self, record):
        """
        Inserts new record into database.

        record: tuple
        
        returns: None
        """
        self._cursor.execute(f"""
            INSERT INTO RegisteredEmployees (EmployeeID, RegistrationNo, Status, EcoCar, Distance, ReservedDates)
            VALUES ({record[0]}, '{record[1]}', '{record[2]}', {record[3]}, '{record[4]}', '{record[5]}')
        """)

    def delete_record(self, EmployeeID):
        """
        Deletes whole record from database.

        EmployeeID: int

        returns: None
        """
        self._cursor.execute(f"""
            DELETE FROM RegisteredEmployees
            WHERE EmployeeID = {EmployeeID}
        """)

    def update_record(self, EmployeeID, changes):
        """
        Updates record with (new) given values.

        EmployeeID: int
        changes: dict with objects of the form {str: any} <=> {fieldname: newvalue} - e.g., {"Distance": 40}

        returns: None
        """
        for field in changes:
            value = changes[field]
            changes[field] = ("=", value)

        set_statement = self.get_whole_statement_sql(changes, ",")

        print("executing statement...")
        self._cursor.execute(f"""
            UPDATE RegisteredEmployees
            SET {set_statement}
            WHERE EmployeeID = {EmployeeID}
        """)

    def get_records(self, criteria):
        """
        Returns all records with field values according to given parameters in a table format.

        criteria: dictionary of fields with corresponding values.
        {"Status": ("<>", val)}

        returns: list of tuples
        """
        statement = self.get_whole_statement_sql(criteria, "AND")

        self._cursor.execute(f"""
            SELECT *
            FROM RegisteredEmployees
            WHERE {statement}
        """)
        
        # self.print_details(self._cursor.fetchall())
        return self._cursor.fetchall()

    def edit_date(self, date, change_in_days):
        """
        Changes the date by given number of days.
        
        date: str of format "XX-XX-XXXX"
        change_in_days: int
        
        returns: str
        """
        date = [int(x) for x in date.split("-")]
        date = datetime.date(date[2], date[1], date[0])
        new_date = date + datetime.timedelta(days=change_in_days)
        return "-".join(reversed(str(new_date).split("-")))

    def days_difference(self, date1, date2):
        """
        Returns the difference (date2 - date1) in days.

        date1: str
        date2: str

        returns: int
        """
        date1 = [int(x) for x in date1.split("-")]
        date2 = [int(x) for x in date2.split("-")]
        
        date1 = datetime.date(date1[2], date1[1], date1[0])
        date2 = datetime.date(date2[2], date2[1], date2[0])

        return int(str(date2-date1).split(" ")[0])

    def reserve_space(self, date_range, EmployeeID):
        """
        Updates ReservedDates field of record with EmployeeID.

        date_range: tuple (can only be str if passing in 'always')
        EmployeeID: int

        returns: None (or -1 if unsuccessful) 
        """
        if self.get_no_of_free_spaces() == 0:
            return -1
        else:
            record = self.get_records({"EmployeeID": ("=", EmployeeID)})[0]
            status = record[2]
            if len(date_range) == 1:
                if date_range[0].lower() == "always":
                    return -1
                else:
                    new_value = date_range[0]
            else:
                if status != "Other":
                    return -1
                else:
                    new_value = date_range[0] + "--" + date_range[1]
        
        print("updating record...")
        self.update_record(EmployeeID, {"ReservedDates": new_value})
        self._availability[status] -= 1

    def opt_out(self, date_range, EmployeeID):
        """
        Updates ReservedDates field of record with EmployeeID.

        date_range: tuple (can only be str if passing in 'always')
        EmployeeID: int

        returns: None (or -1 if unsuccessful)
        """
        record = self.get_records({"EmployeeID": ("=", EmployeeID)})[0]
        status = record[2]
        if len(date_range) == 1:
            if date_range[0].lower() == "always":
                new_value = "None"
            else:
                end_reserve = self.edit_date(date_range[0], -1)
                restart_reserve = self.edit_date(date_range[0], 1)
                new_value = self.get_date_today() + "--" + end_reserve + " ; " + restart_reserve + "--" + "Always"
        else:
            end_reserve = self.edit_date(date_range[0], -1)
            restart_reserve = self.edit_date(date_range[1], 1)
            if status != "Other":
                new_value = self.get_date_today() + "--" + end_reserve + " ; " + restart_reserve + "--" + "Always"
            else:
                final_date = status.split(" ; ")[-1].split("--")[-1]
                new_value = self.get_date_today() + "--" + end_reserve + " ; " + restart_reserve + "--" + final_date
        
        self.update_record(EmployeeID, {"ReservedDates": new_value})
        self._availability[status] += 1
        
    def print_details(self, data):
        """
        Prints records in a table (a more readable format).

        data: list of tuples

        returns: None
        """
        print()
        print("EmployeeID | Registration No. | Status                   | Eco Car | Distance (km) | Reserved Dates")
        print(" "*10, "|", " "*16, "|", " "*24, "|", " "*7, "|", " "*13, "|", " "*14)
        for row in data:
            row = list(row)
            row[3] = "True" if row[3] == 1 else "False"
            print(f"{row[0]:<11}| {row[1]:<17}| {row[2]:<25}| {row[3]:<8}| {row[4]:<14}| {row[5]}")
        print()

class AppUI(DB):

    def __init__(self, cursor):
        super().__init__(cursor)

    def choice_1(self, EmployeeID):
        """
        Executes 1. from display_menu.

        EmployeeID: int

        returns: None
        """
        print()
        record = self.get_records({"EmployeeID": ("=", EmployeeID)})[0]

        if record[2] != "Other":
            print("Your space is automatically reserved.")
        elif self.get_no_of_free_spaces() == 0:
            print("There are no more free spaces.")
        else:
            date_range = input("Enter the date (range) you would like to reserve for (format: XX-XX-XXXX--YY-YY-YYYY or just ZZ-ZZ-ZZZZ if a single day): ").split("--")
            self.reserve_space(date_range, EmployeeID)
            print("\nReserve successful. Updated record:")
        
        self.print_details(self.get_records({"EmployeeID": ("=", EmployeeID)}))

    def choice_2(self, EmployeeID):
        """
        Executes 2. from display_menu.

        EmployeeID: int

        returns: None
        """
        print()
        record = self.get_records({"EmployeeID": ("=", EmployeeID)})[0]

        if record[-1] == "None":
            print("You have no dates reserved.")
        else:
            valid = False
            while not valid:
                date_range = input("Enter the date (range) you would like open space for (format: XX-XX-XXXX--YY-YY-YYYY or just ZZ-ZZ-ZZZZ if a single day): ").split("--")
                reserved_dates = [x.split("--") for x in record[-1].split(" ; ")]
                for rang in reserved_dates:
                    if rang[0].lower() == "always":
                        valid = True
                        break
                    elif self.days_difference(rang[0], date_range[0]) >= 0 and self.days_difference(date_range[1], rang[1]) >= 0:
                        valid = True
                        break
                if valid:
                    break
                print("You do not have a reserved space in this date range. Please enter a valid date range.")
            
            self.opt_out(date_range, EmployeeID)
            print("\nOpt out successful. Updated record:")
            self.print_details(self.get_records({"EmployeeID": ("=", EmployeeID)}))
    
    def choice_3(self, EmployeeID):
        """
        Executes 3. from display_menu.

        EmployeeID: int

        returns: None
        """
        print()
        record = self.get_records({"EmployeeID": ("=", EmployeeID)})[0]
        print("Current reserved dates:", record[-1])
 
    def display_menu(self):
        """
        Displays menu.

        returns: None.
        """
        print("\nMenu:")
        print("1. Reserve a space")
        print("2. Open up your space to others")
        print("3. View your current reserved dates")
        print("4. Quit program")

    def run(self):
        """
        Runs the user interface.

        returns: None
        """
        choice = 0
        EmployeeID = int(input("Enter your ID: "))
        print()
        while choice != 4:
            self.display_menu()
            choice = int(input("Enter your choice: "))
            if choice == 1:
                self.choice_1(EmployeeID)
            elif choice == 2:
                self.choice_2(EmployeeID)
            elif choice == 3:
                self.choice_3(EmployeeID)
            elif choice == 4:
                break


class SecurityUI(DB):

    def __init__(self, cursor):
        super().__init__(cursor)

    def run(self):
        """
        Runs the security-checking interface.

        returns: None
        """
        # registration no. is detected by recognition software as car enters car park
        registration_no = input("\nEnter registration no. ('end' if no more cars): ")
        
        while registration_no != "end":    
            records = self.get_records({"RegistrationNo": ("=", registration_no)})
            if records[0] == []:
                print("Registration No. was not found in database.")
            else:
                for record in records:
                    if record[-1].lower() == "always":
                        print("Car has space reserved.")
                    elif record[-1].lower() == "none":
                        print("Car has no space reserved.")
                    else:
                        reserved_dates = [x.split("--") for x in record[-1].split(" ; ")]
                        for rang in reserved_dates:
                            if self.days_difference(rang[0], self.get_date_today()) >= 0 and self.days_difference(self.get_date_today(), rang[1]) >= 0:
                                print("Car has space reserved.")
                                break
                        else:
                            print("Car has no space reserved.")

            registration_no = input("\nEnter registration no. ('end' if no more cars): ")

if __name__ == "__main__":

    import pyodbc
    import datetime

    conn = pyodbc.connect(r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\Users\emma8\OneDrive\Documents\JP Morgan\employees.accdb;")
    cursor = conn.cursor()

    EI = AppUI(cursor)
    EI.run()

    SI = SecurityUI(cursor)
    SI.run()

    conn.commit()