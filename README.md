# fledge-north-mssql


Fledge North Plugin to store data into a MSSQL database. The data is stored in one table, one row per reading. The structure of the table has to be the following: ID | Date | Asset | Content. See Database Setup for the SQL statements to create the table.

### Installation 

1. Install ODBC Driver + Headers: [Link to Installation Guide](https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15)
2. Install MSSQL Python Client: ``pip install pyodbc`` or run ``python3 -m pip install -r requirements.txt``
3. copy ``mssql_north`` directory to ``FLEDGE_HOME_DIR/python/fledge/plugins/north/``
4. Test the installation by sending a GET request to ``http://FLEDGE_HOME_URL/fledge/plugins/installed?type=north``. The response is a JSON listing all installed north plugins and should look like: 
```json 
{
    "plugins": [
        {
            "name": "mssql_north",
            "type": "north",
            "description": "MSSQL North Plugin",
            "version": "1.0",
            "installedDirectory": "north/mssql_north",
            "packageName": "fledge-north-mssql-north"
        },...
    ]
}
```

### Database Setup

```sql
CREATE TABLE Table1 (Id int IDENTITY(1,1) NOT NULL,
                     Date datetimeoffset(7),
                     Asset NVARCHAR(100),
                     Content TEXT);
INSERT INTO Table1(date, asset, content) VALUES ('2021-10-18 11:21:02.312547716+02:00', 'test', '{a: 200}');
```

[Link to MSSQL Date Types](https://docs.microsoft.com/en-us/sql/t-sql/functions/date-and-time-data-types-and-functions-transact-sql?view=sql-server-ver15)
