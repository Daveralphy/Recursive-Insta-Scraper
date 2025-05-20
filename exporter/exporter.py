import csv

class Exporter:
    def __init__(self, filename):
        self.filename = filename
        self.fields = [
            "Username", "Full Name", "Bio", "WhatsApp Number",
            "WhatsApp Group Link", "Type", "Region",
            "Follower Count", "Profile URL", "External Link"
        ]

    def export(self, profiles):
        with open(self.filename, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fields)
            writer.writeheader()
            for profile in profiles:
                row = {
                    "Username": profile.get("Username", ""),
                    "Full Name": profile.get("Full Name", ""),
                    "Bio": profile.get("Bio", ""),
                    "WhatsApp Number": profile.get("WhatsApp Number", ""),
                    "WhatsApp Group Link": profile.get("WhatsApp Group Link", ""),
                    "Type": profile.get("Type", ""),
                    "Region": profile.get("Region", ""),
                    "Follower Count": profile.get("Follower Count", ""),
                    "Profile URL": profile.get("Profile URL", ""),
                    "External Link": profile.get("External Link", ""),
                }
                writer.writerow(row)

def export_results(profiles, filename):
    exporter = Exporter(filename)
    exporter.export(profiles)
