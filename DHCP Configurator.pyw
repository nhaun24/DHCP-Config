import csv
import ipaddress
from msilib.schema import Icon
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import scrolledtext
import time

def upload_file():
    global csv_file_path
    filetypes = [("CSV Files", "*.csv")]
    csv_file_path = filedialog.askopenfilename(filetypes=filetypes)
    if csv_file_path:
        file_label.config(text=f"Selected File: {csv_file_path}")
    else:
        file_label.config(text="No file selected")

def generate_dhcp_config():
    if csv_file_path:
        try:
            with open(csv_file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)

                # Get the domain name input
                domain_input_value = domain_input.get()
                if domain_input_value == "Input":
                    domain = domain_entry.get()
                else:
                    domain = None

                dhcp_config_all = ""

                # Loop through the rows in the CSV file
                for row_num, row in enumerate(reader, start=1):
                    # Check the value of 'Purpose' and skip the row if it's not "Data" or "Voice"
                    purpose = row.get('Purpose')
                    if purpose not in ["Data", "Voice"]:
                        continue

                    subnet_input = row['CGN Space']
                    description = row.get('Description')
                    location = row.get('Location / Shelf')

                    # Error handling for an incorrectly written CSV file
                    if not subnet_input:
                        raise ValueError(f"Subnet missing or empty in row {row_num}: {row}")

                    if not description:
                        raise ValueError(f"Description missing or empty in row {row_num}: {row}")

                    if not location:
                        raise ValueError(f"Location missing or empty in row {row_num}: {row}")

                    # Convert the subnet input to an IPv4Network object
                    subnet = ipaddress.IPv4Network(subnet_input)

                    # Initialize an empty dictionary to store the DHCP configuration for the site
                    dhcp_config = {}

                    # Add the subnet address and netmask to the dictionary
                    dhcp_config['subnet'] = str(subnet.network_address)
                    dhcp_config['netmask'] = str(subnet.netmask)

                    # Add the default gateway and broadcast address to the dictionary
                    dhcp_config['gateway'] = str(subnet.network_address + 1)
                    dhcp_config['broadcast'] = str(subnet.broadcast_address)

                    # Add the DNS server addresses to the dictionary
                    dhcp_config['dns_servers'] = "8.8.8.8, 4.2.2.2"

                    # Add the pool name and description to the dictionary
                    dhcp_config['pool_name'] = f"{location} {description}"

                    # Use the domain name from the user input or the CSV file
                    if domain:
                        dhcp_config['domain_name'] = f'"{domain}"'
                    else:
                        dhcp_config['domain_name'] = f'"{row.get("Domain Name")}"'

                    # Generate the DHCP configuration for the site
                    ip_range = list(subnet.hosts())[1:-1]
                    start_ip, end_ip = str(ip_range[0]), str(ip_range[-1])
                    end_ip = str(end_ip[:-1])
                    end_ip += str(4)

                    dhcp_config_site = f"""
#{dhcp_config['pool_name']}
subnet {dhcp_config['subnet']} netmask {dhcp_config['netmask']} {{
  pool {{
      failover peer "failover-partner";
      range {start_ip} {end_ip};
      deny dynamic bootp clients;
  }}
  default-lease-time 86400;
  option routers {dhcp_config['gateway']};
  option broadcast-address {dhcp_config['broadcast']};
  option subnet-mask {dhcp_config['netmask']};
  option domain-name {dhcp_config['domain_name']};
  option domain-name-servers {dhcp_config['dns_servers']};
}}
"""
                    dhcp_config_all += dhcp_config_site

            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, dhcp_config_all)
            status_label.config(text="DHCP configuration generated successfully.")
        except FileNotFoundError:
            status_label.config(text=f"Error: The file '{csv_file_path}' does not exist.")
        except ValueError as ve:
            status_label.config(text=f"ValueError: {str(ve)}")
        except Exception as e:
            status_label.config(text=f"An error occurred: {str(e)}")
    else:
        status_label.config(text="No file selected.")

def export_config():
    config_text = output_text.get("1.0", tk.END)
    if config_text:
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w") as f:
                f.write(config_text)
            status_label.config(text="DHCP configuration exported successfully.")
        else:
            status_label.config(text="Export canceled.")
    else:
        status_label.config(text="No configuration to export.")

# Create the main window
window = tk.Tk()
window.title("DHCP Configuration Writer")
window.iconbitmap("ddd.ico")

# Set the background color
window.configure(bg="#333333")

# Configure styles
style = ttk.Style()
style.configure("TButton",
                foreground="black",
                background="#7D3C98",
                font=("Helvetica", 12, "bold"),
                borderwidth=2)
style.configure("TLabel",
                foreground="white",
                background="#333333",
                font=("Helvetica", 12))
style.configure("TFrame",
                background="#333333")
style.configure("TCombobox",
                font=("Helvetica", 12),
                fieldbackground="#333333",
                foreground="black")
style.configure("TEntry",
                font=("Helvetica", 12),
                fieldbackground="#333333",
                foreground="#747474"),
style.configure("TScrolledText",
                foreground="white",)

# Create a frame for file selection
file_frame = ttk.Frame(window)
file_frame.pack(pady=10)

file_button = ttk.Button(file_frame, text="Select CSV File", command=upload_file)
file_button.grid(row=0, column=0, padx=10)

file_label = ttk.Label(file_frame, text="No file selected")
file_label.grid(row=0, column=1, padx=10)

# Create a frame for domain input
domain_frame = ttk.Frame(window)
domain_frame.pack(pady=10)

domain_label = ttk.Label(domain_frame, text="Input domain name:")
domain_label.grid(row=0, column=0, padx=10)

domain_input = tk.StringVar(value="Use CSV")
domain_dropdown = ttk.Combobox(domain_frame, textvariable=domain_input, values=["Use CSV", "Input"], state="readonly")
domain_dropdown.grid(row=0, column=1, padx=10)

domain_entry = ttk.Entry(domain_frame, width=30)
domain_entry.grid(row=0, column=2, padx=10)

# Create a button to generate DHCP configuration
generate_button = ttk.Button(window, text="Generate DHCP Config", command=generate_dhcp_config)
generate_button.pack(pady=10)

# Create a button to export the DHCP configuration
export_button = ttk.Button(window, text="Export Config", command=export_config)
export_button.pack(pady=10)

# Create a status label
status_label = ttk.Label(window, text="")
status_label.pack()

# Create a frame for the output text box
output_frame = ttk.Frame(window)
output_frame.pack(pady=10)

output_label = ttk.Label(output_frame, text="DHCP Configuration:")
output_label.pack()

# Create a scrolled text box to display the DHCP configuration
output_text = scrolledtext.ScrolledText(output_frame, height=30, width=60, bg="#929292")
output_text.pack()

# Configure the foreground color of the text inside the output_text widget
output_text.config(foreground="white")

# Run the main event loop
window.mainloop()
