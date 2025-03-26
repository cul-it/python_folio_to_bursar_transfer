from src.shared.call_functions import CallFunctions
from src.build_charges import BuildCharges
from src.build_credits import BuildCredits
from src.export import ExportData
import os
import json

connector = CallFunctions()
build_charges = BuildCharges(connector)
charge_data = build_charges.get_charges()
build_credits = BuildCredits(connector)
refund_data = build_credits.get_credits()
ExportData(connector, charge_data, refund_data)
