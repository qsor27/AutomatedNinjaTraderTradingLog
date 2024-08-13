import json
from collections import defaultdict
from enum import Enum
from datetime import datetime
import csv
import os
import pandas as pd
import re
import logging
import shutil

# Set up logging
logging.basicConfig(filename='trade_performance_generator.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Specify the directory paths
directory_path = 'data'
archive_path = os.path.join(directory_path, 'Archive')

# Load instrument multipliers
with open('instrument_multipliers.json', 'r') as f:
    instrument_multipliers = json.load(f)

class ExitType(Enum):
    STOP_LOSS = "SL"
    TAKE_PROFIT = "TP"

class EntryExit:
    relevant_columns = ['Account', 'Market pos.', 'Entry price', 'Exit price', 'Qty', 'Entry time', 'Exit time',
                        'Instrument', 'Profit', 'Commission']

    def __init__(self, account, market_position, entry_price, exit_price, qty, entry_time, exit_time, instrument, profit, commission):
        self.Account = account
        self.Market_pos = market_position
        self.Entry_price = self.parse_float(entry_price, 'Entry price')
        self.Exit_price = self.parse_float(exit_price, 'Exit price')
        self.Qty = self.parse_int(qty, 'Qty')
        self.Entry_time = entry_time
        self.Exit_time = exit_time
        self.Instrument = instrument
        self.Profit = self.parse_profit(profit)
        self.Commission = self.parse_commission(commission)
        self.Multiplier = instrument_multipliers.get(self.Instrument, 1)

    @staticmethod
    def parse_float(value, field_name):
        try:
            return float(value)
        except (ValueError, TypeError):
            logging.error(f"Error parsing {field_name}: {value}")
            return 0.0

    @staticmethod
    def parse_int(value, field_name):
        try:
            return int(value)
        except (ValueError, TypeError):
            logging.error(f"Error parsing {field_name}: {value}")
            return 0

    def parse_profit(self, profit):
        logging.debug(f"Parsing profit: {profit} (type: {type(profit)})")
        if profit is None:
            logging.warning("Profit is None, defaulting to 0.0")
            return 0.0
        if isinstance(profit, (int, float)):
            return float(profit)
        elif isinstance(profit, str):
            try:
                # Remove currency symbols and parentheses, then convert to float
                profit_str = re.sub(r'[($)]', '', profit)
                return -float(profit_str) if profit_str.startswith('-') else float(profit_str)
            except ValueError:
                logging.error(f"Error parsing profit string: {profit}")
                return 0.0
        else:
            logging.error(f"Unexpected profit type: {type(profit)}")
            return 0.0

    def parse_commission(self, commission):
        logging.debug(f"Parsing commission: {commission} (type: {type(commission)})")
        if commission is None:
            logging.warning("Commission is None, defaulting to 0.0")
            return 0.0
        if isinstance(commission, (int, float)):
            return float(commission)
        elif isinstance(commission, str):
            try:
                # Remove currency symbols and convert to float
                return float(re.sub(r'[($)]', '', commission))
            except ValueError:
                logging.error(f"Error parsing commission string: {commission}")
                return 0.0
        else:
            logging.error(f"Unexpected commission type: {type(commission)}")
            return 0.0

    def get_exit_type(self):
        if self.Profit_points > 0:
            return ExitType.TAKE_PROFIT
        else:
            return ExitType.STOP_LOSS

    @property
    def Exit(self):
        return {
            'price': self.Exit_price,
            'Qty': self.Qty,
            'Pnl_points': self.Profit_points,
            'Pnl_dollars': self.Profit_dollars,
            'Exit_time': self.Exit_time
        }

    @property
    def Profit_points(self):
        if self.Market_pos == 'Long':
            return round((self.Exit_price - self.Entry_price) * self.Qty, 2)
        return round(-(self.Exit_price - self.Entry_price) * self.Qty, 2)

    @property
    def Profit_dollars(self):
        return round(self.Profit_points * self.Multiplier, 2)

    @classmethod
    def from_csv_row(cls, csv_row):
        kwargs = {column.replace('.', '_').lower(): csv_row[column] for column in cls.relevant_columns}
        return cls(**kwargs)

    def __repr__(self):
        return f"EntryExit(Account={self.Account}, Market_pos={self.Market_pos}, Entry_price={self.Entry_price}, " \
               f"Exit_price={self.Exit_price}, Qty={self.Qty}, " \
               f"Entry_time={self.Entry_time}, Exit_time={self.Exit_time}, Instrument={self.Instrument}, " \
               f"Profit_points={self.Profit_points}, Profit_dollars={self.Profit_dollars}, Commission={self.Commission})\n"

class Trade:
    relevant_columns = EntryExit.relevant_columns

    def __init__(self, entry_exit_objects):
        if not entry_exit_objects:
            raise ValueError("Trade must have at least one EntryExit object.")

        self.Qty = sum(obj.Qty for obj in entry_exit_objects)
        self.Exits = self.get_exits(entry_exit_objects)

        reference_object = entry_exit_objects[0]
        self.Account = reference_object.Account
        self.Market_pos = reference_object.Market_pos
        self.Entry_price = reference_object.Entry_price
        self.Entry_time = reference_object.Entry_time
        self.Instrument = reference_object.Instrument
        self.Exit_time = max(obj.Exit_time for obj in entry_exit_objects)
        self.Total_commission = sum(obj.Commission for obj in entry_exit_objects)
        self._multiplier = reference_object.Multiplier

    def get_exits(self, entry_exits):
        Exits = []
        if len(entry_exits) > 1:
            for i, entry_exit in enumerate(entry_exits, 1):
                exit = entry_exit.Exit
                exit_type = entry_exit.get_exit_type().value
                Exits.append(f'{exit_type}{i}: {exit}')
        else:
            close = entry_exits[0].Exit
            exit_type = entry_exits[0].get_exit_type().value
            Exits.append(f'{exit_type}: {close}')
        return Exits

    @classmethod
    def from_entry_exit_objects(cls, entry_exit_objects):
        return cls(entry_exit_objects)

    @classmethod
    def from_csv_file(cls, csv_file_path):
        entry_exit_objects = []
        with open(csv_file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                entry_exit_objects.append(EntryExit.from_csv_row(row))
        return cls.from_entry_exit_objects(entry_exit_objects)

    def __repr__(self):
        return f"Account={self.Account}, Market_pos={self.Market_pos}, Entry_price={self.Entry_price}, " \
               f"Qty={self.Qty}, Entry_time={self.Entry_time}, Exit_time={self.Exit_time}, " \
               f"Instrument={self.Instrument}, Total_commission={self.Total_commission}, Exits={self.Exits}\n"

def create_trades(entry_exits):
    unique_sets = {}
    for entry_exit in entry_exits:
        key = (entry_exit.Entry_time, entry_exit.Entry_price, entry_exit.Instrument)
        if key not in unique_sets:
            unique_sets[key] = [entry_exit]
        else:
            exit_index = next((i for i, line in enumerate(unique_sets[key]) if line.Exit_price == entry_exit.Exit_price), -1)
            if exit_index < 0:
                unique_sets[key].append(entry_exit)
            else:
                unique_sets[key][exit_index].Qty += entry_exit.Qty
                unique_sets[key][exit_index].Commission += entry_exit.Commission
    trades = [Trade(entry_exit) for entry_exit in unique_sets.values()]
    return trades

def parse_ninjatrader_csv(directory_path):
    files = os.listdir(directory_path)
    csv_files = [file for file in files if file.endswith('.csv')]
    if not csv_files:
        logging.error(f"No CSV files found in the specified directory: {directory_path}")
        return None, None
    csv_file_path = os.path.join(directory_path, csv_files[0])
    df = pd.read_csv(csv_file_path)
    relevant_columns = ['Account', 'Market pos.', 'Entry price', 'Exit price', 'Qty', 'Profit', 'Entry time',
                        'Exit time', 'Instrument', 'Commission']
    df = df[relevant_columns]
    entryexits = []
    for _, row in df.iterrows():
        try:
            entryexit_instance = EntryExit(
                account=row['Account'],
                market_position=row['Market pos.'],
                entry_price=row['Entry price'],
                exit_price=row['Exit price'],
                qty=row['Qty'],
                entry_time=row['Entry time'],
                exit_time=row['Exit time'],
                instrument=row['Instrument'],
                profit=row['Profit'],
                commission=row['Commission']
            )
            entryexits.append(entryexit_instance)
        except Exception as e:
            logging.error(f"Error creating EntryExit instance: {e}")
            logging.error(f"Problematic row: {row}")
    return entryexits, csv_file_path

def trade_to_dict(trade):
    return {
        'Account': trade.Account,
        'Market_pos': trade.Market_pos,
        'Entry_price': trade.Entry_price,
        'Qty': trade.Qty,
        'Entry_time': trade.Entry_time,
        'Exit_time': trade.Exit_time,
        'Instrument': trade.Instrument,
        'Total_commission': trade.Total_commission,
        'Exits': trade.Exits
    }

if __name__ == "__main__":
    try:
        # Ensure archive directory exists
        if not os.path.exists(archive_path):
            os.makedirs(archive_path)
            logging.info(f"Created archive directory: {archive_path}")

        all_entry_exits, source_csv_path = parse_ninjatrader_csv(directory_path)
        if all_entry_exits is None:
            logging.error("Failed to parse NinjaTrader CSV. Exiting.")
            exit(1)

        trades = create_trades(all_entry_exits)
        print(trades)

        today = datetime.today()
        date_string = today.strftime('%m%d%Y')
        output_csv_path = date_string + "trades.csv"

        with open(output_csv_path, 'w', newline='') as csv_file:
            fieldnames = ['Account', 'Market_pos', 'Entry_price', 'Qty', 'Entry_time', 'Exit_time', 'Instrument', 'Total_commission', 'Exits']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for trade in trades:
                writer.writerow(trade_to_dict(trade))

        print(f"Trades details written to {output_csv_path}")
        logging.info(f"Script completed successfully. Output written to {output_csv_path}")

        # Move the processed CSV file to the archive directory
        if source_csv_path:
            archive_file_path = os.path.join(archive_path, os.path.basename(source_csv_path))
            shutil.move(source_csv_path, archive_file_path)
            print(f"Moved processed CSV file to {archive_file_path}")
            logging.info(f"Archived processed CSV file: {archive_file_path}")
        else:
            logging.warning("No source CSV file to archive")

    except Exception as e:
        logging.exception("An error occurred during script execution")
        print(f"An error occurred. Please check the log file for details: {e}")

os.system("python ImportIntoLog.py")