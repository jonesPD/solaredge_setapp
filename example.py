#!/usr/bin/env python3

import solaredge_setapp

import argparse
import datetime
import json
import requests


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument("address", type=str, help="hostname or ip address")
    parserargs = argparser.parse_args()

    address = parserargs.address

    data = {}
    web_services = [
        # name, endpoint_url, module_class, enabled, data_name
        ("WebAppConfigs", "web/v1/app_configs", solaredge_setapp.app_configs.WebAppConfigs(), False, "appconfigs"),
        ("Communication", "web/v1/communication", solaredge_setapp.communication.Communication(), False, "communication"),
        ("Information", "web/v1/information", solaredge_setapp.information.Information(), False, "information"),
        ("Maintenance", "web/v1/maintenance", solaredge_setapp.maintenance.Maintenance(), True, "maintenance"),
        ("Power Control", "web/v1/power_control", solaredge_setapp.power_control.PowerControl(), False, "power_control"),
        ("Language & Region", "web/v1/region", solaredge_setapp.region.Region(), False, "region"),
        ("Status", "web/v1/status", solaredge_setapp.status.Status(), True, "status")
    ]
    
    for name, endpoint_url, module_class, enabled, data_name in web_services:
        if enabled:
            endpoint_request = requests.get("http://{address}/{endpoint_url}".format(
                address=parserargs.address,
                endpoint_url=endpoint_url
            ))

            if endpoint_request.status_code != 200:
                raise Exception("Unable to load '{name}' at {url}".format(
                    name=name,
                    url=endpoint_url
                ))

            data[data_name] = module_class.parse_protobuf(endpoint_request.content)

    if "status" in data:

        print("\n\t{serial}\t{status}\t{temperature}°C".format(
            serial=data["status"]["serial"],
            status=data["status"]["status"],
            temperature=data["status"]["inverters"][0]["temperature"]["value"]
        ))
        print("\n\t{power_ac:7.2f}W\t{production_today:.2f}kWh ∑ {production_total:.2f}kWh".format(
            power_ac=data["status"]["power_ac"],
            production_today=(data["status"]["energy"]["day"]/1000),
            production_total=(data["status"]["energy"]["total"]/1000)
        ))
        print("\n\t⏦ {voltage_ac:.2f}V @ {frequency:.2f}Hz".format(
            voltage_ac=data["status"]["voltage_ac"],
            frequency=data["status"]["frequency"],
        ))

        print("\t⎓ {voltage_dc:.2f}V".format(
            voltage_dc=data["status"]["inverters"][0]["voltage_dc"],
        ))

    if "maintenance" in data:
        pos = []
        parsed = []

        for inverter in data["maintenance"]["inverters"]:
            if not inverter["serial"]:
                continue

            print("\n\tPower optimizers ({online}/{total})".format(
                    online=inverter["optimizers_status"]["online"],
                    total=inverter["optimizers_status"]["total"]
                ))
            
            for po in inverter["optimizers"]:
                print("\n\t{serial}\t{last_report}".format(
                    serial=po["serial"],
                    last_report=datetime.datetime.fromtimestamp(po["timestamp"]).strftime("%Y-%m-%d %H:%M:%S") if po["online"] else "Offline",
                ), end="")

                if po["online"]:
                    print("\t{temperature:2.0f}°C\t{module_voltage:4.1f}V\t{module_current:4.1f}A\t{po_voltage:4.1f}V\t{po_power:3.0f}W".format(
                        temperature=po["temperature"],
                        module_voltage=po["module_voltage"],
                        module_current=po["module_current"],
                        po_voltage=po["po_voltage"],
                        po_power=(po["module_voltage"] * po["module_current"])
                    ), end="")