from src.call_functions import CallFunctions
from src.build_charges import BuildCharges
from src.export import ExportData
import os
import json

connector = CallFunctions()
build_charges = BuildCharges(connector)
charge_data = build_charges.get_charges()
export_data = []
ExportData(connector, charge_data, export_data)
