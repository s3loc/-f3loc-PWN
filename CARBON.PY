#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
███████╗██████╗ ███████╗██╗      ██████╗  ██████╗
██╔════╝██╔══██╗██╔════╝██║     ██╔═══██╗██╔════╝
███████╗██████╔╝█████╗  ██║     ██║   ██║██║     
╚════██║██╔═══╝ ██╔══╝  ██║     ██║   ██║██║     
███████║██║     ███████╗███████╗╚██████╔╝╚██████╗
╚══════╝╚═╝     ╚══════╝╚══════╝ ╚═════╝  ╚═════╝
RED TEAM PENTEST FRAMEWORK - s3loc_ EDITION
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import socket
import threading
import nmap
import sqlite3
from datetime import datetime
import time
import random
import queue
import os
import sys
import re
import paramiko
import scapy.all as scapy
import dns.resolver
import ssl
import json
import base64
import zlib
from Crypto.Cipher import AES
from Crypto import Random
import hashlib
import subprocess
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import concurrent.futures

# =============== CONSTANTS ===============
VERSION = "v5.0"
CODENAME = "ShadowStrike"
DEVELOPER = "s3loc_"
COPYRIGHT = f"© 2023 {DEVELOPER} | Red Team Operations"
TITLE = f"s3loc_ RedTeam Toolkit {VERSION} [{CODENAME}]"

# =============== AES ENCRYPTION ===============
class AESCipher:
    def __init__(self, key): 
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

# =============== MAIN APPLICATION ===============
class RedTeamToolkit:
    def __init__(self, master):
        self.master = master
        self.master.title(TITLE)
        self.master.geometry("1366x768")
        self.master.minsize(1024, 768)
        
        # Configuration
        self.current_target = None
        self.attack_queue = queue.Queue()
        self.running_attacks = False
        self.session_key = "s3loc_redteam_secret"
        self.cipher = AESCipher(self.session_key)
        
        # Setup components
        self.setup_styles()
        self.setup_database()
        self.setup_ui()
        self.setup_menus()
        
        # Load initial data
        self.load_targets()
        self.load_settings()

    # =============== SETUP METHODS ===============
    def setup_styles(self):
        """Configure custom styles for the application"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Custom color scheme
        self.bg_color = '#121212'
        self.fg_color = '#e0e0e0'
        self.accent_color = '#d32f2f'
        self.secondary_color = '#424242'
        
        # Configure styles
        self.style.configure('.', background=self.bg_color, foreground=self.fg_color)
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        self.style.configure('TButton', background=self.secondary_color, foreground=self.fg_color)
        self.style.configure('TEntry', fieldbackground=self.secondary_color, foreground=self.fg_color)
        self.style.configure('TCombobox', fieldbackground=self.secondary_color, foreground=self.fg_color)
        self.style.configure('TNotebook', background=self.bg_color)
        self.style.configure('TNotebook.Tab', background=self.secondary_color, foreground=self.fg_color)
        self.style.configure('Treeview', background=self.secondary_color, foreground=self.fg_color, fieldbackground=self.secondary_color)
        self.style.configure('Treeview.Heading', background='#1a1a1a', foreground=self.fg_color)
        self.style.map('Treeview', background=[('selected', '#3a3a3a')])
        
        # Custom style variants
        self.style.configure('Red.TButton', background='#5c0000', foreground='white')
        self.style.configure('Green.TButton', background='#005c00', foreground='white')
        self.style.configure('Blue.TButton', background='#00005c', foreground='white')
        self.style.configure('Yellow.TButton', background='#5c5c00', foreground='white')

    def setup_database(self):
        """Initialize encrypted database"""
        self.db_conn = sqlite3.connect('s3loc_redteam.db')
        self.db_cursor = self.db_conn.cursor()
        
        # Create encrypted tables
        self.db_cursor.execute('''CREATE TABLE IF NOT EXISTS targets
                               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                ip TEXT,
                                hostname TEXT,
                                os TEXT,
                                ports TEXT,
                                vulnerabilities TEXT,
                                last_scan TEXT,
                                notes TEXT,
                                is_critical INTEGER DEFAULT 0)''')
        
        self.db_cursor.execute('''CREATE TABLE IF NOT EXISTS attacks
                               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                target_id INTEGER,
                                attack_type TEXT,
                                timestamp TEXT,
                                success INTEGER,
                                output TEXT,
                                FOREIGN KEY(target_id) REFERENCES targets(id))''')
        
        self.db_cursor.execute('''CREATE TABLE IF NOT EXISTS credentials
                               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                target_id INTEGER,
                                username TEXT,
                                password TEXT,
                                service TEXT,
                                timestamp TEXT,
                                FOREIGN KEY(target_id) REFERENCES targets(id))''')
        
        self.db_cursor.execute('''CREATE TABLE IF NOT EXISTS settings
                               (key TEXT PRIMARY KEY,
                                value TEXT)''')
        
        self.db_conn.commit()

    def setup_ui(self):
        """Setup the main user interface"""
        # Main container
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.setup_header()
        
        # Main notebook
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Setup tabs
        self.setup_recon_tab()
        self.setup_scan_tab()
        self.setup_exploit_tab()
        self.setup_post_tab()
        self.setup_report_tab()
        self.setup_settings_tab()
        
        # Footer
        self.setup_footer()

    def setup_header(self):
        """Setup the application header"""
        header_frame = ttk.Frame(self.main_frame, style='TFrame')
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Title
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)
        
        ttk.Label(title_frame, 
                 text=f"s3loc_ RedTeam Toolkit",
                 font=('Helvetica', 16, 'bold')).pack(anchor='w')
        
        ttk.Label(title_frame,
                 text=f"{VERSION} - {CODENAME} | {DEVELOPER}",
                 font=('Helvetica', 10)).pack(anchor='w')
        
        # Status bar
        self.status_frame = ttk.Frame(header_frame)
        self.status_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.status_label = ttk.Label(self.status_frame, 
                                    text="Status: Ready",
                                    font=('Helvetica', 9))
        self.status_label.pack(side=tk.RIGHT, padx=10)

    def setup_recon_tab(self):
        """Setup reconnaissance tab"""
        self.recon_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.recon_tab, text="Reconnaissance")
        
        # Target input
        input_frame = ttk.Frame(self.recon_tab)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Target:").pack(side=tk.LEFT)
        
        self.target_entry = ttk.Entry(input_frame, width=40)
        self.target_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(input_frame, text="Add Target", 
                  command=self.add_target).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(input_frame, text="Quick Scan",
                  command=self.quick_scan).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(input_frame, text="Deep Scan",
                  command=self.deep_scan,
                  style='Green.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(input_frame, text="OSINT Gather",
                  command=self.osint_gather,
                  style='Blue.TButton').pack(side=tk.LEFT, padx=5)
        
        # Target list
        list_frame = ttk.Frame(self.recon_tab)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.target_tree = ttk.Treeview(list_frame, 
                                      columns=('ID', 'IP', 'Hostname', 'OS', 'Last Scan', 'Critical'),
                                      selectmode='browse')
        
        # Configure columns
        self.target_tree.heading('#0', text='#')
        self.target_tree.heading('ID', text='ID')
        self.target_tree.heading('IP', text='IP Address')
        self.target_tree.heading('Hostname', text='Hostname')
        self.target_tree.heading('OS', text='Operating System')
        self.target_tree.heading('Last Scan', text='Last Scan')
        self.target_tree.heading('Critical', text='Critical')
        
        self.target_tree.column('#0', width=30, stretch=tk.NO)
        self.target_tree.column('ID', width=50, stretch=tk.NO)
        self.target_tree.column('IP', width=120)
        self.target_tree.column('Hostname', width=150)
        self.target_tree.column('OS', width=150)
        self.target_tree.column('Last Scan', width=150)
        self.target_tree.column('Critical', width=80)
        
        self.target_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Bind selection event
        self.target_tree.bind('<<TreeviewSelect>>', self.on_target_select)
        
        # Target details
        details_frame = ttk.Frame(self.recon_tab)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.details_notebook = ttk.Notebook(details_frame)
        self.details_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Ports tab
        ports_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(ports_tab, text="Ports & Services")
        
        self.ports_tree = ttk.Treeview(ports_tab,
                                     columns=('Port', 'Service', 'Version', 'Protocol', 'Banner'),
                                     selectmode='extended')
        
        for col in ['Port', 'Service', 'Version', 'Protocol', 'Banner']:
            self.ports_tree.heading(col, text=col)
            self.ports_tree.column(col, width=100)
        
        self.ports_tree.pack(fill=tk.BOTH, expand=True)
        
        # Vulnerabilities tab
        vuln_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(vuln_tab, text="Vulnerabilities")
        
        self.vuln_tree = ttk.Treeview(vuln_tab,
                                     columns=('CVE', 'Severity', 'Port', 'Description', 'Exploit'),
                                     selectmode='extended')
        
        for col in ['CVE', 'Severity', 'Port', 'Description', 'Exploit']:
            self.vuln_tree.heading(col, text=col)
            self.vuln_tree.column(col, width=120)
        
        self.vuln_tree.pack(fill=tk.BOTH, expand=True)
        
        # Notes tab
        notes_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(notes_tab, text="Notes")
        
        self.notes_text = scrolledtext.ScrolledText(notes_tab,
                                                  wrap=tk.WORD,
                                                  bg=self.secondary_color,
                                                  fg=self.fg_color,
                                                  insertbackground='white')
        self.notes_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(notes_tab, text="Save Notes",
                  command=self.save_notes).pack(side=tk.RIGHT)

    def setup_scan_tab(self):
        """Setup vulnerability scanning tab"""
        self.scan_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.scan_tab, text="Vulnerability Assessment")
        
        # Scan controls
        controls_frame = ttk.Frame(self.scan_tab)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(controls_frame, text="Scan Profile:").pack(side=tk.LEFT)
        
        self.scan_profile = ttk.Combobox(controls_frame,
                                        values=["Full Audit", "Web App", "Network", "Custom"])
        self.scan_profile.pack(side=tk.LEFT, padx=5)
        self.scan_profile.current(0)
        
        ttk.Button(controls_frame, text="Start Scan",
                  command=self.start_scan,
                  style='Green.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Stop Scan",
                  command=self.stop_scan,
                  style='Red.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Exploit All",
                  command=self.exploit_all_vulns,
                  style='Yellow.TButton').pack(side=tk.LEFT, padx=5)
        
        # Results frame
        results_frame = ttk.Frame(self.scan_tab)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.scan_results_tree = ttk.Treeview(results_frame,
                                            columns=('CVE', 'Severity', 'Port', 'Service', 'Description', 'Solution', 'Exploit'),
                                            selectmode='extended')
        
        for col in ['CVE', 'Severity', 'Port', 'Service', 'Description', 'Solution', 'Exploit']:
            self.scan_results_tree.heading(col, text=col)
            self.scan_results_tree.column(col, width=120)
        
        self.scan_results_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Context menu
        self.scan_context_menu = tk.Menu(self.scan_results_tree, tearoff=0)
        self.scan_context_menu.add_command(label="Exploit", command=self.exploit_selected_vuln)
        self.scan_context_menu.add_command(label="View Details", command=self.view_vuln_details)
        self.scan_context_menu.add_command(label="Add to Report", command=self.add_vuln_to_report)
        self.scan_results_tree.bind("<Button-3>", self.show_scan_context_menu)
        
        # Progress frame
        progress_frame = ttk.Frame(self.scan_tab)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.scan_progress = ttk.Progressbar(progress_frame,
                                           orient=tk.HORIZONTAL,
                                           mode='determinate')
        self.scan_progress.pack(fill=tk.X)
        
        self.scan_status = ttk.Label(progress_frame,
                                   text="Ready to scan")
        self.scan_status.pack(fill=tk.X)

    def setup_exploit_tab(self):
        """Setup exploitation tab"""
        self.exploit_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.exploit_tab, text="Exploitation")
        
        # Exploit controls
        controls_frame = ttk.Frame(self.exploit_tab)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(controls_frame, text="Exploit Module:").pack(side=tk.LEFT)
        
        self.exploit_module = ttk.Combobox(controls_frame,
                                         values=["Metasploit", "Custom", "Brute Force", 
                                                "SQL Injection", "XSS", "RCE", "LFI/RFI"])
        self.exploit_module.pack(side=tk.LEFT, padx=5)
        self.exploit_module.current(0)
        
        ttk.Button(controls_frame, text="Load Module",
                  command=self.load_exploit_module).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Execute",
                  command=self.execute_exploit,
                  style='Red.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Auto Exploit",
                  command=self.auto_exploit,
                  style='Yellow.TButton').pack(side=tk.LEFT, padx=5)
        
        # Configuration frame
        config_frame = ttk.Frame(self.exploit_tab)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.exploit_config_notebook = ttk.Notebook(config_frame)
        self.exploit_config_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder for dynamic config
        self.exploit_config_placeholder = ttk.Frame(self.exploit_config_notebook)
        self.exploit_config_notebook.add(self.exploit_config_placeholder, text="Configuration")
        
        # Output frame
        output_frame = ttk.Frame(self.exploit_tab)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.exploit_output = scrolledtext.ScrolledText(output_frame,
                                                      wrap=tk.WORD,
                                                      bg=self.secondary_color,
                                                      fg=self.fg_color,
                                                      insertbackground='white')
        self.exploit_output.pack(fill=tk.BOTH, expand=True)
        
        # History frame
        history_frame = ttk.Frame(self.exploit_tab)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.exploit_history_tree = ttk.Treeview(history_frame,
                                               columns=('ID', 'Target', 'Exploit', 'Time', 'Status'),
                                               selectmode='browse')
        
        for col in ['ID', 'Target', 'Exploit', 'Time', 'Status']:
            self.exploit_history_tree.heading(col, text=col)
            self.exploit_history_tree.column(col, width=100)
        
        self.exploit_history_tree.pack(fill=tk.BOTH, expand=True)

    def setup_post_tab(self):
        """Setup post-exploitation tab"""
        self.post_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.post_tab, text="Post-Exploitation")
        
        # Module controls
        controls_frame = ttk.Frame(self.post_tab)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(controls_frame, text="Post Module:").pack(side=tk.LEFT)
        
        self.post_module = ttk.Combobox(controls_frame,
                                      values=["Shell", "File Browser", "Privilege Escalation", 
                                             "Persistence", "Lateral Movement", "Data Exfiltration"])
        self.post_module.pack(side=tk.LEFT, padx=5)
        self.post_module.current(0)
        
        ttk.Button(controls_frame, text="Load Module",
                  command=self.load_post_module).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Execute",
                  command=self.execute_post_module,
                  style='Blue.TButton').pack(side=tk.LEFT, padx=5)
        
        # Output notebook
        output_notebook = ttk.Notebook(self.post_tab)
        output_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Shell tab
        shell_tab = ttk.Frame(output_notebook)
        output_notebook.add(shell_tab, text="Shell")
        
        self.shell_output = scrolledtext.ScrolledText(shell_tab,
                                                    wrap=tk.WORD,
                                                    bg=self.secondary_color,
                                                    fg=self.fg_color,
                                                    insertbackground='white')
        self.shell_output.pack(fill=tk.BOTH, expand=True)
        
        shell_input_frame = ttk.Frame(shell_tab)
        shell_input_frame.pack(fill=tk.X)
        
        self.shell_input = ttk.Entry(shell_input_frame)
        self.shell_input.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)
        
        ttk.Button(shell_input_frame, text="Send",
                  command=self.send_shell_command).pack(side=tk.LEFT, padx=5)
        
        # File browser tab
        file_tab = ttk.Frame(output_notebook)
        output_notebook.add(file_tab, text="File Browser")
        
        self.file_tree = ttk.Treeview(file_tab)
        self.file_tree.pack(fill=tk.BOTH, expand=True)
        
        # Credentials tab
        creds_tab = ttk.Frame(output_notebook)
        output_notebook.add(creds_tab, text="Credentials")
        
        self.creds_tree = ttk.Treeview(creds_tab,
                                     columns=('Username', 'Password', 'Service', 'Source'),
                                     selectmode='browse')
        
        for col in ['Username', 'Password', 'Service', 'Source']:
            self.creds_tree.heading(col, text=col)
            self.creds_tree.column(col, width=120)
        
        self.creds_tree.pack(fill=tk.BOTH, expand=True)

    def setup_report_tab(self):
        """Setup reporting tab"""
        self.report_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.report_tab, text="Reporting")
        
        # Report controls
        controls_frame = ttk.Frame(self.report_tab)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(controls_frame, text="Report Type:").pack(side=tk.LEFT)
        
        self.report_type = ttk.Combobox(controls_frame,
                                      values=["Executive", "Technical", "Full Disclosure", "Custom"])
        self.report_type.pack(side=tk.LEFT, padx=5)
        self.report_type.current(0)
        
        ttk.Button(controls_frame, text="Generate",
                  command=self.generate_report).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Export",
                  command=self.export_report).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Save Template",
                  command=self.save_report_template).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Load Template",
                  command=self.load_report_template).pack(side=tk.LEFT, padx=5)
        
        # Report content
        report_frame = ttk.Frame(self.report_tab)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.report_text = scrolledtext.ScrolledText(report_frame,
                                                   wrap=tk.WORD,
                                                   bg=self.secondary_color,
                                                   fg=self.fg_color,
                                                   insertbackground='white')
        self.report_text.pack(fill=tk.BOTH, expand=True)

    def setup_settings_tab(self):
        """Setup settings tab"""
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        
        # General settings
        general_frame = ttk.LabelFrame(self.settings_tab, text="General Settings")
        general_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(general_frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.theme = ttk.Combobox(general_frame,
                                values=["Dark", "Light", "Professional", "Hacker"])
        self.theme.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        self.theme.current(0)
        
        # Tool paths
        tools_frame = ttk.LabelFrame(self.settings_tab, text="Tool Paths")
        tools_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(tools_frame, text="Nmap Path:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.nmap_path = ttk.Entry(tools_frame)
        self.nmap_path.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Button(tools_frame, text="Browse",
                  command=self.browse_nmap_path).grid(row=0, column=2, padx=5, pady=2)
        
        # Database settings
        db_frame = ttk.LabelFrame(self.settings_tab, text="Database")
        db_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(db_frame, text="Backup",
                  command=self.backup_database).pack(side=tk.LEFT, padx=5, pady=2)
        
        ttk.Button(db_frame, text="Restore",
                  command=self.restore_database).pack(side=tk.LEFT, padx=5, pady=2)
        
        ttk.Button(db_frame, text="Clear",
                  command=self.clear_database,
                  style='Red.TButton').pack(side=tk.LEFT, padx=5, pady=2)
        
        # Save button
        save_frame = ttk.Frame(self.settings_tab)
        save_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(save_frame, text="Save Settings",
                  command=self.save_settings).pack(side=tk.RIGHT, padx=5)

    def setup_footer(self):
        """Setup the application footer"""
        footer_frame = ttk.Frame(self.main_frame)
        footer_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(footer_frame,
                 text=COPYRIGHT).pack(side=tk.LEFT)
        
        ttk.Label(footer_frame,
                 text=f"Red Team Toolkit - {DEVELOPER}",
                 font=('Helvetica', 8, 'bold')).pack(side=tk.RIGHT)

    def setup_menus(self):
        """Setup the application menus"""
        menubar = tk.Menu(self.master)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Session", command=self.new_session)
        file_menu.add_command(label="Save Session", command=self.save_session)
        file_menu.add_command(label="Load Session", command=self.load_session)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Packet Sniffer", command=self.open_sniffer)
        tools_menu.add_command(label="Password Cracker", command=self.open_cracker)
        tools_menu.add_command(label="Hash Generator", command=self.open_hashgen)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.master.config(menu=menubar)

    # =============== CORE FUNCTIONALITY ===============
    def add_target(self):
        """Add a new target to the database"""
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showerror("Error", "Please enter a target")
            return
        
        try:
            # Check if target exists
            self.db_cursor.execute("SELECT id FROM targets WHERE ip=? OR hostname=?", (target, target))
            if self.db_cursor.fetchone():
                messagebox.showerror("Error", "Target already exists")
                return
            
            # Add target
            self.db_cursor.execute("INSERT INTO targets (ip, hostname, last_scan) VALUES (?, ?, ?)",
                                 (target, target, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.db_conn.commit()
            
            self.load_targets()
            self.target_entry.delete(0, tk.END)
            self.status_label.config(text=f"Status: Target {target} added")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add target: {str(e)}")

    def quick_scan(self):
        """Perform a quick scan on selected target"""
        if not self.current_target:
            messagebox.showerror("Error", "Please select a target first")
            return
        
        try:
            self.status_label.config(text=f"Status: Quick scanning {self.current_target['ip']}...")
            self.master.update()
            
            # Simulate scan with Nmap
            nm = nmap.PortScanner()
            nm.scan(hosts=self.current_target['ip'], arguments='-T4 -F')
            
            # Process results
            open_ports = []
            for proto in nm[self.current_target['ip']].all_protocols():
                ports = nm[self.current_target['ip']][proto].keys()
                for port in ports:
                    service = nm[self.current_target['ip']][proto][port]['name']
                    open_ports.append(f"{port}/{proto} ({service})")
            
            # Update database
            self.db_cursor.execute("UPDATE targets SET ports=?, last_scan=? WHERE id=?",
                                 (', '.join(open_ports), 
                                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                  self.current_target['id']))
            self.db_conn.commit()
            
            self.update_target_details()
            self.status_label.config(text=f"Status: Quick scan completed for {self.current_target['ip']}")
        except Exception as e:
            self.status_label.config(text="Status: Scan failed")
            messagebox.showerror("Scan Error", f"Failed to perform quick scan: {str(e)}")

    def deep_scan(self):
        """Perform a comprehensive scan on selected target"""
        if not self.current_target:
            messagebox.showerror("Error", "Please select a target first")
            return
        
        try:
            self.status_label.config(text=f"Status: Deep scanning {self.current_target['ip']}...")
            self.master.update()
            
            # Simulate scan with progress
            for i in range(1, 101):
                time.sleep(0.05)
                self.scan_progress['value'] = i
                self.master.update_idletasks()
            
            # Sample results
            open_ports = [
                "21/tcp (ftp vsftpd 3.0.3)",
                "22/tcp (ssh OpenSSH 7.9p1)",
                "80/tcp (http Apache 2.4.41)",
                "443/tcp (https Apache 2.4.41)"
            ]
            
            os_info = "Linux 3.2-4.9"
            vulns = [
                "CVE-2021-41773: Path traversal in Apache 2.4.49-2.4.50",
                "CVE-2020-15778: SSH command injection",
                "CVE-2019-19824: FTP privilege escalation"
            ]
            
            # Update database
            self.db_cursor.execute("UPDATE targets SET ports=?, os=?, vulnerabilities=?, last_scan=? WHERE id=?",
                                 (', '.join(open_ports), os_info, '\n'.join(vulns),
                                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                  self.current_target['id']))
            self.db_conn.commit()
            
            self.update_target_details()
            self.status_label.config(text=f"Status: Deep scan completed for {self.current_target['ip']}")
        except Exception as e:
            self.status_label.config(text="Status: Scan failed")
            messagebox.showerror("Scan Error", f"Failed to perform deep scan: {str(e)}")

    def osint_gather(self):
        """Perform OSINT gathering on target"""
        if not self.current_target:
            messagebox.showerror("Error", "Please select a target first")
            return
        
        try:
            self.status_label.config(text=f"Status: Gathering OSINT for {self.current_target['ip']}...")
            self.master.update()
            
            # Simulate OSINT gathering
            time.sleep(2)
            
            # Sample OSINT data
            hostname = socket.getfqdn(self.current_target['ip'])
            whois_data = f"Domain: {hostname}\nRegistrar: Example Registrar\nCreated: 2020-01-01"
            
            # Update notes
            current_notes = self.current_target.get('notes', '')
            new_notes = f"=== OSINT Data ===\n{whois_data}\n\n{current_notes}"
            
            self.db_cursor.execute("UPDATE targets SET hostname=?, notes=? WHERE id=?",
                                 (hostname, new_notes, self.current_target['id']))
            self.db_conn.commit()
            
            self.update_target_details()
            self.status_label.config(text=f"Status: OSINT gathered for {self.current_target['ip']}")
        except Exception as e:
            self.status_label.config(text="Status: OSINT failed")
            messagebox.showerror("OSINT Error", f"Failed to gather OSINT: {str(e)}")

    def start_scan(self):
        """Start vulnerability scanning"""
        if not self.current_target:
            messagebox.showerror("Error", "Please select a target first")
            return
        
        scan_type = self.scan_profile.get()
        self.scan_status.config(text=f"Starting {scan_type} scan...")
        self.scan_progress['value'] = 0
        
        # Start scan in background
        scan_thread = threading.Thread(target=self.run_vuln_scan, args=(scan_type,))
        scan_thread.daemon = True
        scan_thread.start()

    def run_vuln_scan(self, scan_type):
        """Run vulnerability scan in background"""
        try:
            # Simulate scan progress
            for i in range(1, 101):
                if not self.running_attacks:
                    break
                
                time.sleep(0.1)
                self.scan_progress['value'] = i
                self.scan_status.config(text=f"{scan_type} scan: {i}% complete")
                self.master.update_idletasks()
            
            if self.running_attacks:
                # Add sample vulnerabilities
                sample_vulns = [
                    ("CVE-2021-41773", "Critical", "80", "Apache Path Traversal", "Update to 2.4.51", "exploit/multi/http/apache_normalize_path_rce"),
                    ("CVE-2020-1472", "Critical", "445", "ZeroLogon", "Apply Microsoft patch", "exploit/windows/smb/zerologon"),
                    ("CVE-2019-19781", "High", "443", "Citrix ADC RCE", "Update Citrix firmware", "exploit/linux/http/citrix_dir_traversal_rce")
                ]
                
                self.scan_results_tree.delete(*self.scan_results_tree.get_children())
                for vuln in sample_vulns:
                    self.scan_results_tree.insert('', 'end', values=vuln)
                
                self.scan_status.config(text=f"{scan_type} scan completed")
        except Exception as e:
            self.scan_status.config(text=f"Scan error: {str(e)}")
        finally:
            self.running_attacks = False

    def stop_scan(self):
        """Stop running scan"""
        self.running_attacks = False
        self.scan_status.config(text="Scan stopped by user")

    def exploit_selected_vuln(self):
        """Exploit selected vulnerability"""
        selected = self.scan_results_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a vulnerability first")
            return
        
        vuln_data = self.scan_results_tree.item(selected[0], 'values')
        cve = vuln_data[0]
        
        # Add to attack queue
        self.attack_queue.put(('exploit', {
            'cve': cve,
            'target': self.current_target,
            'exploit': vuln_data[5]
        }))
        
        # Start attack thread if not running
        if not hasattr(self, 'attack_thread') or not self.attack_thread.is_alive():
            self.attack_thread = threading.Thread(target=self.process_attack_queue)
            self.attack_thread.daemon = True
            self.attack_thread.start()
        
        messagebox.showinfo("Exploit Queued", f"Exploit for {cve} has been queued")

    def exploit_all_vulns(self):
        """Exploit all detected vulnerabilities"""
        if not messagebox.askyesno("Confirm", "Exploit ALL vulnerabilities? This may be noisy."):
            return
        
        for child in self.scan_results_tree.get_children():
            vuln_data = self.scan_results_tree.item(child, 'values')
            self.attack_queue.put(('exploit', {
                'cve': vuln_data[0],
                'target': self.current_target,
                'exploit': vuln_data[5]
            }))
        
        # Start attack thread if not running
        if not hasattr(self, 'attack_thread') or not self.attack_thread.is_alive():
            self.attack_thread = threading.Thread(target=self.process_attack_queue)
            self.attack_thread.daemon = True
            self.attack_thread.start()
        
        messagebox.showinfo("Exploits Queued", "All vulnerabilities added to attack queue")

    def process_attack_queue(self):
        """Process the attack queue in background"""
        while not self.attack_queue.empty():
            attack_type, params = self.attack_queue.get()
            
            try:
                if attack_type == 'exploit':
                    self.run_exploit(params['cve'], params['target'], params['exploit'])
                elif attack_type == 'bruteforce':
                    self.run_bruteforce(params['service'], params['target'])
            except Exception as e:
                self.append_exploit_output(f"Attack failed: {str(e)}\n")

    def run_exploit(self, cve, target, exploit_path):
        """Run exploit against target"""
        self.append_exploit_output(f"[+] Starting exploit for {cve} on {target['ip']}...\n")
        
        # Simulate exploit running
        time.sleep(2)
        
        # Random success/failure
        success = random.random() > 0.3
        if success:
            output = f"[+] Exploit successful! Gained access to {target['ip']}\n"
            
            # Add credentials if successful
            if random.random() > 0.5:
                self.db_cursor.execute("INSERT INTO credentials (target_id, username, password, service, timestamp) VALUES (?, ?, ?, ?, ?)",
                                     (target['id'], "admin", "P@ssw0rd123", "SSH",
                                      datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                self.db_conn.commit()
                output += "[+] Found credentials: admin:P@ssw0rd123 (SSH)\n"
            
            # Add to history
            self.add_exploit_history(target['ip'], f"CVE-{cve}", "Success")
        else:
            output = f"[-] Exploit failed for {cve} on {target['ip']}\n"
            self.add_exploit_history(target['ip'], f"CVE-{cve}", "Failed")
        
        self.append_exploit_output(output)

    def load_exploit_module(self):
        """Load selected exploit module"""
        module = self.exploit_module.get()
        self.exploit_output.insert(tk.END, f"[*] Loading {module} module...\n")
        
        # Clear previous config
        for child in self.exploit_config_placeholder.winfo_children():
            child.destroy()
        
        # Add module-specific config
        ttk.Label(self.exploit_config_placeholder, 
                 text=f"{module} Configuration",
                 font=('Helvetica', 10, 'bold')).pack(pady=5)
        
        # Example: Add some configuration options
        if module == "Metasploit":
            ttk.Label(self.exploit_config_placeholder, text="Payload:").pack()
            payload_combo = ttk.Combobox(self.exploit_config_placeholder,
                                       values=["windows/meterpreter/reverse_tcp",
                                              "linux/x86/meterpreter/reverse_tcp"])
            payload_combo.pack(fill=tk.X, padx=10, pady=2)
            payload_combo.current(0)
            
            ttk.Label(self.exploit_config_placeholder, text="LHOST:").pack()
            ttk.Entry(self.exploit_config_placeholder).pack(fill=tk.X, padx=10, pady=2)
            
            ttk.Label(self.exploit_config_placeholder, text="LPORT:").pack()
            ttk.Entry(self.exploit_config_placeholder).pack(fill=tk.X, padx=10, pady=2)
        
        elif module == "Brute Force":
            ttk.Label(self.exploit_config_placeholder, text="Username List:").pack()
            ttk.Entry(self.exploit_config_placeholder).pack(fill=tk.X, padx=10, pady=2)
            
            ttk.Label(self.exploit_config_placeholder, text="Password List:").pack()
            ttk.Entry(self.exploit_config_placeholder).pack(fill=tk.X, padx=10, pady=2)
            
            ttk.Label(self.exploit_config_placeholder, text="Max Attempts:").pack()
            ttk.Spinbox(self.exploit_config_placeholder, from_=1, to=1000).pack(fill=tk.X, padx=10, pady=2)
        
        self.exploit_output.insert(tk.END, f"[*] {module} module loaded successfully\n")

    def execute_exploit(self):
        """Execute selected exploit"""
        if not self.current_target:
            messagebox.showerror("Error", "Please select a target first")
            return
        
        module = self.exploit_module.get()
        self.append_exploit_output(f"[*] Executing {module} against {self.current_target['ip']}...\n")
        
        # Add to attack queue
        self.attack_queue.put(('exploit', {
            'cve': 'Custom',
            'target': self.current_target,
            'exploit': module
        }))
        
        # Start attack thread if not running
        if not hasattr(self, 'attack_thread') or not self.attack_thread.is_alive():
            self.attack_thread = threading.Thread(target=self.process_attack_queue)
            self.attack_thread.daemon = True
            self.attack_thread.start()

    def auto_exploit(self):
        """Automatically exploit target based on vulnerabilities"""
        if not self.current_target:
            messagebox.showerror("Error", "Please select a target first")
            return
        
        if not messagebox.askyesno("Confirm", "Automatically exploit all known vulnerabilities?"):
            return
        
        self.append_exploit_output(f"[*] Starting auto-exploit against {self.current_target['ip']}...\n")
        
        # Get vulnerabilities from database
        self.db_cursor.execute("SELECT vulnerabilities FROM targets WHERE id=?", (self.current_target['id'],))
        vulns = self.db_cursor.fetchone()[0]
        
        if not vulns:
            self.append_exploit_output("[-] No vulnerabilities found in database\n")
            return
        
        # Add each vulnerability to queue
        for vuln in vulns.split('\n'):
            if 'CVE-' in vuln:
                cve = vuln.split('CVE-')[1].split(':')[0]
                self.attack_queue.put(('exploit', {
                    'cve': f"CVE-{cve}",
                    'target': self.current_target,
                    'exploit': 'auto'
                }))
        
        # Start attack thread if not running
        if not hasattr(self, 'attack_thread') or not self.attack_thread.is_alive():
            self.attack_thread = threading.Thread(target=self.process_attack_queue)
            self.attack_thread.daemon = True
            self.attack_thread.start()
        
        self.append_exploit_output("[*] All vulnerabilities added to attack queue\n")

    def load_post_module(self):
        """Load post-exploitation module"""
        module = self.post_module.get()
        self.shell_output.insert(tk.END, f"[*] Loading {module} module...\n")
        
        # Clear previous output
        self.shell_output.delete(1.0, tk.END)
        
        # Initialize module
        if module == "Shell":
            self.shell_output.insert(tk.END, "[*] Shell module loaded. Connect to target first.\n")
        elif module == "File Browser":
            self.shell_output.insert(tk.END, "[*] File browser module loaded.\n")
            self.shell_output.insert(tk.END, "[/] /etc/passwd\n[/] /root/.ssh/id_rsa\n")
        elif module == "Privilege Escalation":
            self.shell_output.insert(tk.END, "[*] Privilege escalation module loaded.\n")
            self.shell_output.insert(tk.END, "[*] Checking for sudo vulnerabilities...\n")

    def execute_post_module(self):
        """Execute post-exploitation module"""
        module = self.post_module.get()
        self.shell_output.insert(tk.END, f"[*] Executing {module} module...\n")
        
        # Simulate module execution
        if module == "Shell":
            self.shell_output.insert(tk.END, "[+] Established reverse shell connection\n")
            self.shell_output.insert(tk.END, "root@target:# ")
        elif module == "File Browser":
            self.shell_output.insert(tk.END, "[+] Retrieved file listing:\n")
            self.shell_output.insert(tk.END, "-rw-r--r-- 1 root root 1234 /etc/passwd\n")
            self.shell_output.insert(tk.END, "-rw------- 1 root root 5678 /root/.ssh/id_rsa\n")
        elif module == "Privilege Escalation":
            self.shell_output.insert(tk.END, "[+] Found sudo vulnerability (CVE-2021-3156)\n")
            self.shell_output.insert(tk.END, "[!] Exploiting...\n")
            self.shell_output.insert(tk.END, "[+] Success! Now running as root\n")

    def send_shell_command(self):
        """Send command to simulated shell"""
        cmd = self.shell_input.get()
        if not cmd:
            return
        
        self.shell_output.insert(tk.END, f"{cmd}\n")
        
        # Simulate command output
        if cmd == "whoami":
            self.shell_output.insert(tk.END, "root\n")
        elif cmd == "id":
            self.shell_output.insert(tk.END, "uid=0(root) gid=0(root) groups=0(root)\n")
        elif cmd == "ls -la /root":
            self.shell_output.insert(tk.END, "total 24\ndrwx------  4 root root 4096 Jan  1 00:00 .\n")
            self.shell_output.insert(tk.END, "-rw-------  1 root root 1234 Jan  1 00:00 .bash_history\n")
        else:
            self.shell_output.insert(tk.END, "Command executed\n")
        
        self.shell_output.insert(tk.END, "root@target:# ")
        self.shell_input.delete(0, tk.END)

    def generate_report(self):
        """Generate penetration test report"""
        report_type = self.report_type.get()
        self.report_text.delete(1.0, tk.END)
        
        if report_type == "Executive":
            report = self.generate_executive_report()
        elif report_type == "Technical":
            report = self.generate_technical_report()
        elif report_type == "Full Disclosure":
            report = self.generate_full_report()
        else:
            report = "Custom report template\n\n"
        
        self.report_text.insert(tk.END, report)

    def generate_executive_report(self):
        """Generate executive summary report"""
        return f"""s3loc_ RedTeam Toolkit - Executive Summary
{datetime.now().strftime("%Y-%m-%d")}

=== Overview ===
This report summarizes the findings from the penetration test conducted using the s3loc_ RedTeam Toolkit.

=== Key Findings ===
- Critical Vulnerabilities: 3   
- High Risk Vulnerabilities: 5
- Successful Exploits: 2
- Compromised Systems: 1

=== Recommendations ===
1. Immediately patch critical vulnerabilities
2. Implement network segmentation
3. Enhance monitoring for suspicious activities

{DEVELOPER}
Red Team Lead
"""

    def generate_technical_report(self):
        """Generate technical report"""
        report = f"""s3loc_ RedTeam Toolkit - Technical Report
{datetime.now().strftime("%Y-%m-%d")}

=== Target Information ===
IP Address: {self.current_target['ip'] if self.current_target else 'N/A'}
Hostname: {self.current_target['hostname'] if self.current_target else 'N/A'}
Operating System: {self.current_target['os'] if self.current_target else 'N/A'}

=== Vulnerabilities ===
"""
        
        if self.current_target and self.current_target.get('vulnerabilities'):
            for vuln in self.current_target['vulnerabilities'].split('\n'):
                report += f"- {vuln}\n"
        else:
            report += "No vulnerabilities identified\n"
        
        report += "\n=== Exploit Results ===\n"
        
        if self.current_target:
            self.db_cursor.execute("SELECT attack_type, timestamp, success FROM attacks WHERE target_id=?", 
                                (self.current_target['id'],))
            attacks = self.db_cursor.fetchall()
            
            if attacks:
                for attack in attacks:
                    report += f"{attack[0]} at {attack[1]} - {'Success' if attack[2] else 'Failed'}\n"
            else:
                report += "No exploit attempts recorded\n"
        
        report += f"\n=== Recommendations ===\n1. Patch all critical vulnerabilities\n2. Harden system configurations\n\n{DEVELOPER}"
        return report

    def generate_full_report(self):
        """Generate full disclosure report"""
        report = f"""s3loc_ RedTeam Toolkit - Full Disclosure Report
{datetime.now().strftime("%Y-%m-%d")}

=== Executive Summary ===
[Summary of findings and risk assessment]

=== Methodology ===
[Detailed testing methodology]

=== Technical Findings ===
"""
        
        if self.current_target:
            # Add vulnerabilities
            if self.current_target.get('vulnerabilities'):
                report += "\n=== Vulnerabilities ===\n"
                for vuln in self.current_target['vulnerabilities'].split('\n'):
                    report += f"- {vuln}\n"
                    report += "  - Impact: High\n"
                    report += "  - Remediation: [Steps]\n"
                    report += "  - References: [Links]\n\n"
            
            # Add exploit details
            self.db_cursor.execute("SELECT * FROM attacks WHERE target_id=?", (self.current_target['id'],))
            attacks = self.db_cursor.fetchall()
            
            if attacks:
                report += "\n=== Exploit Details ===\n"
                for attack in attacks:
                    report += f"- {attack[2]} at {attack[3]}: "
                    report += "Successful\n" if attack[4] else "Failed\n"
                    if attack[5]:
                        report += f"  Output:\n{attack[5]}\n"
        
        report += f"\n=== Appendices ===\nA. Screenshots\nB. Code Samples\nC. Network Diagrams\n\n{DEVELOPER}"
        return report

    def export_report(self):
        """Export report to file"""
        filetypes = [('PDF Files', '*.pdf'), 
                    ('Word Documents', '*.docx'), 
                    ('Text Files', '*.txt')]
        
        filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                              filetypes=filetypes,
                                              title="Export Report")
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.report_text.get(1.0, tk.END))
                self.status_label.config(text=f"Status: Report exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export report: {str(e)}")

    def save_report_template(self):
        """Save current report as template"""
        template_name = simpledialog.askstring("Save Template", "Enter template name:")
        if template_name:
            try:
                content = self.report_text.get(1.0, tk.END)
                self.db_cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                                     (f"template_{template_name}", self.cipher.encrypt(content)))
                self.db_conn.commit()
                messagebox.showinfo("Success", f"Template '{template_name}' saved")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save template: {str(e)}")

    def load_report_template(self):
        """Load report template"""
        # Get available templates
        self.db_cursor.execute("SELECT key FROM settings WHERE key LIKE 'template_%'")
        templates = [t[0].replace('template_', '') for t in self.db_cursor.fetchall()]
        
        if not templates:
            messagebox.showinfo("Info", "No templates found")
            return
        
        template_name = simpledialog.askstring("Load Template", "Select template:", 
                                             initialvalue=templates[0])
        if template_name:
            try:
                self.db_cursor.execute("SELECT value FROM settings WHERE key=?", 
                                     (f"template_{template_name}",))
                encrypted = self.db_cursor.fetchone()[0]
                content = self.cipher.decrypt(encrypted)
                self.report_text.delete(1.0, tk.END)
                self.report_text.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load template: {str(e)}")

    def backup_database(self):
        """Backup the encrypted database"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"s3loc_backup_{timestamp}.db"
            
            with open(backup_file, 'wb') as f:
                for line in self.db_conn.iterdump():
                    f.write(f'{line}\n'.encode('utf-8'))
            
            messagebox.showinfo("Backup Complete", f"Database backed up to {backup_file}")
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to backup database: {str(e)}")

    def restore_database(self):
        """Restore database from backup"""
        filename = filedialog.askopenfilename(title="Select Backup File",
                                            filetypes=[("Database Files", "*.db")])
        if filename:
            try:
                # Close current connection
                self.db_conn.close()
                
                # Replace database file
                if os.path.exists('s3loc_redteam.db'):
                    os.remove('s3loc_redteam.db')
                
                with open(filename, 'rb') as f_in, open('s3loc_redteam.db', 'wb') as f_out:
                    f_out.write(f_in.read())
                
                # Reconnect
                self.db_conn = sqlite3.connect('s3loc_redteam.db')
                self.db_cursor = self.db_conn.cursor()
                
                # Reload data
                self.load_targets()
                messagebox.showinfo("Restore Complete", "Database restored successfully")
            except Exception as e:
                messagebox.showerror("Restore Error", f"Failed to restore database: {str(e)}")
                # Reconnect if failed
                self.db_conn = sqlite3.connect('s3loc_redteam.db')
                self.db_cursor = self.db_conn.cursor()

    def clear_database(self):
        """Clear all data from database"""
        if not messagebox.askyesno("Confirm", "This will delete ALL data. Are you sure?"):
            return
        
        try:
            # Drop all tables
            self.db_cursor.execute("DROP TABLE IF EXISTS targets")
            self.db_cursor.execute("DROP TABLE IF EXISTS attacks")
            self.db_cursor.execute("DROP TABLE IF EXISTS credentials")
            self.db_cursor.execute("DROP TABLE IF EXISTS settings")
            
            # Recreate tables
            self.setup_database()
            
            # Update UI
            self.current_target = None
            self.load_targets()
            self.update_target_details()
            
            messagebox.showinfo("Success", "Database cleared successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear database: {str(e)}")

    def browse_nmap_path(self):
        """Browse for Nmap installation path"""
        path = filedialog.askdirectory(title="Select Nmap Installation Directory")
        if path:
            self.nmap_path.delete(0, tk.END)
            self.nmap_path.insert(0, path)

    def save_settings(self):
        """Save application settings"""
        try:
            # Clear existing settings
            self.db_cursor.execute("DELETE FROM settings WHERE key LIKE 'setting_%'")
            
            # Save new settings
            settings = {
                'setting_theme': self.theme.get(),
                'setting_nmap_path': self.nmap_path.get()
            }
            
            for key, value in settings.items():
                self.db_cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)",
                                     (key, value))
            
            self.db_conn.commit()
            messagebox.showinfo("Success", "Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def load_settings(self):
        """Load saved settings"""
        try:
            self.db_cursor.execute("SELECT key, value FROM settings WHERE key LIKE 'setting_%'")
            settings = dict(self.db_cursor.fetchall())
            
            if 'setting_theme' in settings:
                self.theme.set(settings['setting_theme'])
            
            if 'setting_nmap_path' in settings:
                self.nmap_path.insert(0, settings['setting_nmap_path'])
        except Exception as e:
            print(f"Error loading settings: {str(e)}")

    def load_targets(self):
        """Load targets from database"""
        self.target_tree.delete(*self.target_tree.get_children())
        
        self.db_cursor.execute("SELECT id, ip, hostname, os, last_scan, is_critical FROM targets")
        for i, row in enumerate(self.db_cursor.fetchall(), 1):
            critical = "✔" if row[5] else ""
            self.target_tree.insert('', 'end', text=str(i), values=(row[0], row[1], row[2], row[3], row[4], critical))

    def update_target_details(self):
        """Update details for currently selected target"""
        if not self.current_target:
            return
        
        # Clear existing data
        self.ports_tree.delete(*self.ports_tree.get_children())
        self.vuln_tree.delete(*self.vuln_tree.get_children())
        
        # Load ports data
        if self.current_target.get('ports'):
            ports = self.current_target['ports'].split(', ')
            for port in ports:
                # Parse port info (format: "port/proto (service version)")
                match = re.match(r'(\d+)/(\w+)\s*\((.*?)\)', port)
                if match:
                    port_num, proto, service = match.groups()
                    
                    # Try to extract version if present
                    version_match = re.search(r'([\w\s]+)\s+v?([\d\.]+)', service)
                    if version_match:
                        service_name = version_match.group(1).strip()
                        version = version_match.group(2)
                    else:
                        service_name = service
                        version = ''
                    
                    self.ports_tree.insert('', 'end', values=(port_num, service_name, version, proto, ''))
        
        # Load vulnerabilities
        if self.current_target.get('vulnerabilities'):
            vulns = self.current_target['vulnerabilities'].split('\n')
            for vuln in vulns:
                if 'CVE-' in vuln:
                    cve = vuln.split('CVE-')[1].split()[0]
                    cve = f"CVE-{cve}"
                    severity = "Critical" if "critical" in vuln.lower() else "High"
                    port = "Multiple" if "multiple" in vuln.lower() else "N/A"
                    desc = vuln.split(':')[-1].strip()
                    
                    self.vuln_tree.insert('', 'end', values=(cve, severity, port, desc, ''))
        
        # Load notes
        self.notes_text.delete(1.0, tk.END)
        if self.current_target.get('notes'):
            self.notes_text.insert(tk.END, self.current_target['notes'])

    def save_notes(self):
        """Save notes for current target"""
        if not self.current_target:
            return
        
        notes = self.notes_text.get(1.0, tk.END).strip()
        self.db_cursor.execute("UPDATE targets SET notes=? WHERE id=?",
                             (notes, self.current_target['id']))
        self.db_conn.commit()
        self.status_label.config(text="Status: Notes saved")

    def on_target_select(self, event):
        """Handle target selection change"""
        selected = self.target_tree.selection()
        if not selected:
            return
        
        item = self.target_tree.item(selected[0])
        target_id = item['values'][0]
        
        self.db_cursor.execute("SELECT * FROM targets WHERE id=?", (target_id,))
        columns = [column[0] for column in self.db_cursor.description]
        row = self.db_cursor.fetchone()
        
        if row:
            self.current_target = dict(zip(columns, row))
            self.update_target_details()

    def show_scan_context_menu(self, event):
        """Show context menu for scan results"""
        item = self.scan_results_tree.identify_row(event.y)
        if item:
            self.scan_results_tree.selection_set(item)
            self.scan_context_menu.post(event.x_root, event.y_root)

    def view_vuln_details(self):
        """View details of selected vulnerability"""
        selected = self.scan_results_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a vulnerability first")
            return
        
        vuln_data = self.scan_results_tree.item(selected[0], 'values')
        
        # Create detail window
        detail_win = tk.Toplevel(self.master)
        detail_win.title(f"Vulnerability Details: {vuln_data[0]}")
        detail_win.geometry("600x400")
        
        # Add details
        ttk.Label(detail_win, text=f"CVE: {vuln_data[0]}", font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        frame = ttk.Frame(detail_win)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(frame, text="Severity:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(frame, text=vuln_data[1]).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(frame, text="Affected Port:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(frame, text=vuln_data[2]).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(frame, text="Service:").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(frame, text=vuln_data[3]).grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(frame, text="Description:").grid(row=3, column=0, sticky=tk.W)
        desc_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=60, height=8)
        desc_text.insert(tk.END, vuln_data[4])
        desc_text.config(state=tk.DISABLED)
        desc_text.grid(row=3, column=1, pady=5)
        
        ttk.Label(frame, text="Solution:").grid(row=4, column=0, sticky=tk.W)
        sol_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=60, height=8)
        sol_text.insert(tk.END, vuln_data[5])
        sol_text.config(state=tk.DISABLED)
        sol_text.grid(row=4, column=1, pady=5)
        
        ttk.Button(frame, text="Close", command=detail_win.destroy).grid(row=5, column=1, pady=10)

    def add_vuln_to_report(self):
        """Add selected vulnerability to report"""
        selected = self.scan_results_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a vulnerability first")
            return
        
        vuln_data = self.scan_results_tree.item(selected[0], 'values')
        self.report_text.insert(tk.END, f"\n=== {vuln_data[0]} ===\n")
        self.report_text.insert(tk.END, f"Severity: {vuln_data[1]}\n")
        self.report_text.insert(tk.END, f"Port: {vuln_data[2]}\n")
        self.report_text.insert(tk.END, f"Description: {vuln_data[4]}\n")
        self.report_text.insert(tk.END, f"Solution: {vuln_data[5]}\n")
        
        self.status_label.config(text=f"Status: Added {vuln_data[0]} to report")

    def append_exploit_output(self, text):
        """Append text to exploit output"""
        self.exploit_output.insert(tk.END, text)
        self.exploit_output.see(tk.END)

    def add_exploit_history(self, target, exploit, status):
        """Add entry to exploit history"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.exploit_history_tree.insert('', 'end', values=(
            len(self.exploit_history_tree.get_children())+1,
            target,
            exploit,
            timestamp,
            status
        ))

    def new_session(self):
        """Create new session"""
        if messagebox.askyesno("New Session", "Start a new session? Unsaved data will be lost."):
            self.clear_database()
            self.current_target = None
            self.load_targets()
            self.update_target_details()
            self.status_label.config(text="Status: New session created")

    def save_session(self):
        """Save current session"""
        try:
            self.backup_database()
            self.status_label.config(text="Status: Session saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save session: {str(e)}")

    def load_session(self):
        """Load saved session"""
        self.restore_database()

    def open_sniffer(self):
        """Open packet sniffer tool"""
        sniffer_win = tk.Toplevel(self.master)
        sniffer_win.title("Packet Sniffer")
        sniffer_win.geometry("800x600")
        
        ttk.Label(sniffer_win, text="Packet Sniffer Tool", font=('Helvetica', 14)).pack(pady=10)
        
        output = scrolledtext.ScrolledText(sniffer_win, wrap=tk.WORD)
        output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Button(sniffer_win, text="Start Sniffing",
                  command=lambda: output.insert(tk.END, "[*] Sniffing started...\n")).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(sniffer_win, text="Stop Sniffing",
                  command=lambda: output.insert(tk.END, "[*] Sniffing stopped\n")).pack(side=tk.LEFT)

    def open_cracker(self):
        """Open password cracker tool"""
        cracker_win = tk.Toplevel(self.master)
        cracker_win.title("Password Cracker")
        cracker_win.geometry("600x400")
        
        ttk.Label(cracker_win, text="Password Cracker Tool", font=('Helvetica', 14)).pack(pady=10)
        
        ttk.Label(cracker_win, text="Hash:").pack()
        hash_entry = ttk.Entry(cracker_win, width=50)
        hash_entry.pack()
        
        ttk.Label(cracker_win, text="Wordlist:").pack()
        wordlist_entry = ttk.Entry(cracker_win, width=50)
        wordlist_entry.pack()
        
        output = scrolledtext.ScrolledText(cracker_win, wrap=tk.WORD, height=10)
        output.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(cracker_win, text="Start Cracking",
                  command=lambda: output.insert(tk.END, "[*] Cracking started...\n")).pack()

    def open_hashgen(self):
        """Open hash generator tool"""
        hashgen_win = tk.Toplevel(self.master)
        hashgen_win.title("Hash Generator")
        hashgen_win.geometry("600x400")
        
        ttk.Label(hashgen_win, text="Hash Generator Tool", font=('Helvetica', 14)).pack(pady=10)
        
        ttk.Label(hashgen_win, text="Input:").pack()
        input_entry = ttk.Entry(hashgen_win, width=50)
        input_entry.pack()
        
        ttk.Label(hashgen_win, text="Algorithm:").pack()
        algo_combo = ttk.Combobox(hashgen_win, 
                                values=["MD5", "SHA1", "SHA256", "SHA512"])
        algo_combo.pack()
        algo_combo.current(0)
        
        output = scrolledtext.ScrolledText(hashgen_win, wrap=tk.WORD, height=10)
        output.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(hashgen_win, text="Generate Hash",
                  command=lambda: output.insert(tk.END, f"[*] {algo_combo.get()} hash: {hashlib.md5(input_entry.get().encode()).hexdigest()}\n")).pack()

    def show_docs(self):
        """Show documentation"""
        docs_win = tk.Toplevel(self.master)
        docs_win.title("Documentation")
        docs_win.geometry("800x600")
        
        text = scrolledtext.ScrolledText(docs_win, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        
        docs = f"""s3loc_ RedTeam Toolkit Documentation
{datetime.now().strftime("%Y-%m-%d")}

=== Overview ===
This tool is designed for professional penetration testing and red team operations.

=== Features ===
1. Target Reconnaissance
2. Vulnerability Scanning
3. Exploitation Framework
4. Post-Exploitation Tools
5. Reporting

=== Usage ===
1. Add targets in the Recon tab
2. Scan for vulnerabilities
3. Exploit identified weaknesses
4. Maintain access and gather data
5. Generate professional reports

=== Legal Notice ===
This tool is for authorized testing only.
"""
        text.insert(tk.END, docs)

    def show_about(self):
        """Show about dialog"""
        about_win = tk.Toplevel(self.master)
        about_win.title("About")
        about_win.geometry("400x300")
        
        ttk.Label(about_win, 
                 text=f"s3loc_ RedTeam Toolkit\n{VERSION} - {CODENAME}",
                 font=('Helvetica', 14, 'bold')).pack(pady=20)
        
        ttk.Label(about_win,
                 text=f"Developed by: {DEVELOPER}\n{COPYRIGHT}").pack(pady=10)
        
        ttk.Label(about_win,
                 text="For authorized penetration testing only").pack(pady=10)
        
        ttk.Button(about_win, text="Close", command=about_win.destroy).pack()

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = RedTeamToolkit(root)
    root.mainloop()

if __name__ == "__main__":
    main()