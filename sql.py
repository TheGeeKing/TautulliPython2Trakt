import os
import sqlite3


class SQL(sqlite3.Cursor):
    def __init__(self, db: str = "database.db", path: str = ""):
        self.con = sqlite3.connect(os.path.join(path, db), timeout=5)
        self.con.row_factory = (
            sqlite3.Row
        )  # So we can use column names as keys, cause less issues if we later add a column with index values
        sqlite3.Cursor.__init__(self, self.con)
        self.cur = self.con.cursor()

    def execute(self, command: str, *args):
        with self.con:
            if args:
                tmp = self.con.execute(command, args[0])
            else:
                tmp = self.con.execute(command)
            self.con.commit()  # sqlite3.Connection automatically commits
        # tmp = self.cur.execute(command)
        # self.con.commit()
        return tmp

    def commit(self):
        return self.con.commit()

    def add_simple(self, table: str, **kwargs) -> sqlite3.Cursor:
        """Simply add values to the table, no need to specify columns

        Args:
            table (str): the table to add to
            **kwargs: the values to add to the table

        Returns:
            Cursor: the cursor of the db
        """
        with self.con:
            # column_names = self.execute(f"PRAGMA table_info({table})").fetchall()
            tmp = self.con.execute(
                f"INSERT INTO {table} ({', '.join(kwargs)}) VALUES ({', '.join(['?'] * len(kwargs))})",
                tuple(kwargs.values()),
            )
            self.con.commit()
        return tmp

    def add(self, table: str, data: tuple[tuple[str, type]]) -> sqlite3.Cursor:
        """Insert data into the table with tuple as (column, value)

        Args:
            table (str): the table to add to
            data (tuple): ((column, value), (column, value))

        Returns:
            sqlite3.Cursor: the cursor of the db
        """
        with self.con:
            tmp = self.con.execute(
                f"INSERT INTO {table} ({', '.join([i[0] for i in data])}) VALUES ({', '.join(['?'] * len(data))})",
                tuple([i[1] for i in data]),
            )
            self.con.commit()
        return tmp

    def create_table(self, table: str, data: tuple[tuple] | str) -> sqlite3.Cursor:
        if isinstance(data, str):
            with self.con:
                if "PRIMARY KEY" not in data:
                    exec_ = f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, {data})"
                else:
                    exec_ = f"CREATE TABLE IF NOT EXISTS {table} ({data})"
                tmp = self.con.execute(exec_)
                self.con.commit()
            return tmp
        types = []
        for d in data:
            if d[1] == int:
                types.append(f"{d[0]} INTEGER")
            elif d[1] == str:
                types.append(f"{d[0]} TEXT")
            elif d[1] == float:
                types.append(f"{d[0]} REAL")
            elif d[1] == bool:
                types.append(f"{d[0]} BOOLEAN")
            else:
                # raise TypeError(f"Type {d[1]} is not supported")
                types.append(f"{d[0]} {d[1]}")
        types = ", ".join(types)
        if "PRIMARY KEY" not in types:
            exec_ = f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, {types})"
        else:
            exec_ = f"CREATE TABLE IF NOT EXISTS {table} ({types})"
        with self.con:
            self.con.execute(exec_)

    def add_safe(self, table: str, data: tuple[tuple]) -> sqlite3.Cursor:
        """If the table does not exist, create it. Insert data into the table with tuple as (column, value)

        Args:
            table (str): the table to add to
            data (tuple): ((column, value), (column, value))

        Returns:
            sqlite3.Cursor: the cursor of the db
        """
        with self.con:
            if not self.table_exists(table):
                tmp = self.create_table(table, data)
            tmp = self.add(table, data)
            self.con.commit()
        return tmp

    def table_exists(self, table: str) -> bool:
        """Check if a table exists

        Args:
            table (str): the table to check

        Returns:
            bool: if the table exists
        """
        tmp = self.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
        return bool(tmp.fetchall())

    # def insert(conn, command: str):

    #     with conn.cursor() as c:
    #         c.execute(...)
    #     conn.commit()

    # def execute_soft(self, command: str):
    #     return self.cur.execute(command)

    def executemany(self, command: str, args: list[tuple]):
        tmp = self.cur.executemany(command, args)
        self.con.commit()
        return tmp
