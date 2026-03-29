import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk  
import re
import yt_dlp
import threading
import os
import time
import requests
from io import BytesIO
from PIL import Image
import webbrowser
import sys 

# --- The "Find My Files" Helper ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
    
# --- DYNAMIC COLOR THEME ---
C_BG_BASE = ("#F3F4F6", "#111827")        
C_CARD_BG = ("#FFFFFF", "#1F2937")        
C_TEXT_MAIN = ("#111827", "#F9FAFB")      
C_TEXT_MUTED = ("#6B7280", "#9CA3AF")     
C_ACCENT = ("#6366F1", "#818CF8")         
C_ACCENT_HOVER = ("#4F46E5", "#6366F1")
C_SUCCESS = ("#10B981", "#34D399")        
C_DANGER = ("#EF4444", "#F87171")         
C_WARNING = ("#F59E0B", "#FBBF24")        

F_HEADING = ("Segoe UI", 24, "bold")
F_SUBHEADING = ("Segoe UI", 16, "bold")
F_BODY = ("Segoe UI", 13)
F_SMALL = ("Segoe UI", 11)

ctk.set_appearance_mode("dark") 

# --- UI Action Functions ---
def toggle_theme():
    if theme_switch.get() == 1: ctk.set_appearance_mode("dark")
    else: ctk.set_appearance_mode("light")

def open_portfolio(event=None): webbrowser.open("https://georgerossis.pages.dev")
def open_patreon(): webbrowser.open("https://www.patreon.com/posts/cup-of-coffee-154185123?utm_medium=clipboard_copy&utm_source=copyLink&utm_campaign=postshare_creator&utm_content=join_link")

def check_updates(silent=False):
    CURRENT_VERSION = "2.0.0.0"
    UPDATE_URL = f"https://raw.githubusercontent.com/Geoross/omicron/main/version.txt?t={int(time.time())}"
    WHATSNEW_URL = f"https://raw.githubusercontent.com/Geoross/omicron/main/whatsnew.txt?t={int(time.time())}"
    
    try:
        response = requests.get(UPDATE_URL, timeout=5)
        response.raise_for_status() 
        match = re.search(r"u'FileVersion',\s*u'([\d\.]+)'", response.text)
        
        if match:
            latest_version = match.group(1)
            download_link = "https://georgerossis.pages.dev"
            
            if latest_version > CURRENT_VERSION:
                update_dot.place(relx=0.9, rely=0.1, anchor="center")
                
                if not silent:
                    whats_new_text = ""
                    try:
                        wn_response = requests.get(WHATSNEW_URL, timeout=3)
                        if wn_response.status_code == 200:
                            whats_new_text = f"\n\nWhat's New:\n{wn_response.text.strip()}\n"
                    except: pass 

                    msg = f"Good news! Version {latest_version} is fresh out of the oven.\n\nYou are currently on v{CURRENT_VERSION}.{whats_new_text}\nWould you like to grab the new batch?"
                    if messagebox.askyesno("Update Available! 📡", msg):
                        webbrowser.open(download_link)
            else:
                if not silent: messagebox.showinfo("Up to Date 🌟", f"You are running the latest version (v{CURRENT_VERSION}). The kitchen is fully stocked!")
        
    except Exception:
        if not silent: messagebox.showerror("Connection Error 🔌", "Couldn't reach the server to check for updates.")

def show_disclaimer():
    msg = ("The 'Don't Sue Me' Disclaimer\n\nThis app is a fun educational tool. If you use it to pirate movies, that's on you, buddy.\n\n- sizon95")
    messagebox.showinfo("Legal Mumbo Jumbo", msg)

def browse_path(var_to_update, title):
    folder = filedialog.askdirectory(title=title)
    if folder: var_to_update.set(folder)

def cancel_download(cancel_flag, status_label):
    cancel_flag['is_cancelled'] = True
    status_label.configure(text="Status: Whoa, stopping! 🛑", text_color=C_DANGER)

def open_save_folder(path):
    try: os.startfile(path)
    except: pass

# --- SMART UI LOGIC ---
def update_ui_state(*args):
    # 1. Playlist locks out Slicing
    if playlist_var.get():
        start_entry.configure(state="disabled", fg_color=("gray80", "gray20"))
        end_entry.configure(state="disabled", fg_color=("gray80", "gray20"))
        start_var.set("")
        end_var.set("")
    else:
        start_entry.configure(state="normal", fg_color=C_BG_BASE)
        end_entry.configure(state="normal", fg_color=C_BG_BASE)

    # 2. Slicing locks out Subtitles
    if start_var.get().strip() or end_var.get().strip():
        subs_cb.configure(state="disabled", text_color=C_TEXT_MUTED)
        sub_lang_dropdown.configure(state="disabled", fg_color=("gray80", "gray20"))
        subs_var.set(False) 
    else:
        subs_cb.configure(state="normal", text_color=C_TEXT_MAIN)
        
        # 3. Only enable Language Dropdown if Subs are checked
        if subs_var.get():
            sub_lang_dropdown.configure(state="normal", fg_color=C_BG_BASE)
        else:
            sub_lang_dropdown.configure(state="disabled", fg_color=("gray80", "gray20"))

# --- Playlist Selection Popup UI ---
def show_playlist_popup(info, entries, url, quality, target_folder, row_frame, thumb_label, title_label, status_label, progress_bar, action_frame, cancel_btn, extra_opts):
    popup = ctk.CTkToplevel(app)
    popup.title("Select Menu")
    popup.geometry("550x650")
    popup.grab_set() 
    popup.configure(fg_color=C_BG_BASE)
    
    def on_closing():
        status_label.configure(text="Status: Playlist selection cancelled. 🛑", text_color=C_TEXT_MUTED)
        cancel_btn.destroy()
        popup.destroy()
    popup.protocol("WM_DELETE_WINDOW", on_closing)

    ctk.CTkLabel(popup, text=f"Playlist: {info.get('title', 'Unknown')}", font=F_SUBHEADING, text_color=C_TEXT_MAIN).pack(pady=(20, 5), padx=20, anchor="w")
    ctk.CTkLabel(popup, text="Choose which items you want to munch:", font=F_BODY, text_color=C_TEXT_MUTED).pack(padx=20, anchor="w", pady=(0, 10))

    select_all_var = ctk.BooleanVar(value=True)
    checkbox_vars = []

    def toggle_all():
        state = select_all_var.get()
        for _, var in checkbox_vars: var.set(state)

    ctk.CTkCheckBox(popup, text="Select / Deselect All", variable=select_all_var, command=toggle_all, font=F_BODY, fg_color=C_ACCENT).pack(pady=(0, 10), padx=20, anchor="w")

    scroll = ctk.CTkScrollableFrame(popup, fg_color=C_CARD_BG, corner_radius=10)
    scroll.pack(pady=5, padx=20, fill="both", expand=True)

    for i, entry in enumerate(entries):
        if not entry: continue 
        var = ctk.BooleanVar(value=True) 
        checkbox_vars.append((i + 1, var)) 
        cb = ctk.CTkCheckBox(scroll, text=f"{i+1}. {entry.get('title', 'Unknown Video')}", variable=var, font=F_SMALL, fg_color=C_ACCENT)
        cb.pack(anchor="w", pady=5, padx=5)

    def confirm_selection():
        selected_indices = [str(idx) for idx, var in checkbox_vars if var.get()]
        if not selected_indices: return
        popup.destroy()
        status_label.configure(text=f"Status: Selected {len(selected_indices)} videos. Firing up the oven... 🔥", text_color=C_WARNING)
        cancel_flag = {'is_cancelled': False}
        cancel_btn.configure(command=lambda: cancel_download(cancel_flag, status_label))
        threading.Thread(target=process_item, args=(url, quality, target_folder, True, thumb_label, title_label, status_label, progress_bar, cancel_flag, action_frame, cancel_btn, extra_opts, ",".join(selected_indices)), daemon=True).start()

    ctk.CTkButton(popup, text="Confirm & Munch! 🦖", font=F_SUBHEADING, command=confirm_selection, fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER, height=40).pack(pady=20, padx=20, fill="x")

def fetch_playlist_metadata(url, quality, target_folder, row_frame, thumb_label, title_label, status_label, progress_bar, action_frame, cancel_btn, extra_opts):
    ydl_opts = {'extract_flat': 'in_playlist', 'quiet': True, 'ignoreerrors': True, 'ffmpeg_location': resource_path("ffmpeg.exe")}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if 'entries' not in info:
            cancel_flag = {'is_cancelled': False}
            cancel_btn.configure(command=lambda: cancel_download(cancel_flag, status_label))
            threading.Thread(target=process_item, args=(url, quality, target_folder, False, thumb_label, title_label, status_label, progress_bar, cancel_flag, action_frame, cancel_btn, extra_opts, None), daemon=True).start()
            return
        app.after(0, show_playlist_popup, info, info['entries'], url, quality, target_folder, row_frame, thumb_label, title_label, status_label, progress_bar, action_frame, cancel_btn, extra_opts)
    except:
        app.after(0, lambda: status_label.configure(text="Status: Playlist access error. 🛑", text_color=C_DANGER))
        app.after(0, cancel_btn.destroy)

def munch_it(event=None):
    url = url_entry.get()
    if not url: return
    selected_quality = quality_dropdown.get()
    
    extra_opts = {
        'subs': subs_var.get(),
        'sub_lang': sub_lang_var.get(), 
        'art': art_var.get(), 
        'start': start_var.get().strip(), 
        'end': end_var.get().strip()
    }
    
    # Ghost Slices Prevented!
    url_entry.delete(0, ctk.END)
    start_var.set("")
    end_var.set("")
    
    row_frame = ctk.CTkFrame(queue_frame, corner_radius=15, fg_color=C_CARD_BG, border_width=1, border_color=C_ACCENT)
    row_frame.pack(fill="x", pady=8, padx=5)
    thumb_label = ctk.CTkLabel(row_frame, text="Looking...", width=140, height=80, fg_color=("gray80", "gray20"), corner_radius=10)
    thumb_label.pack(side="left", padx=15, pady=15)
    
    info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
    info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=15)
    title_label = ctk.CTkLabel(info_frame, text="Sniffing the link...", font=F_SUBHEADING, text_color=C_TEXT_MAIN, anchor="w", justify="left")
    title_label.pack(fill="x")
    status_label = ctk.CTkLabel(info_frame, text="Status: Fetching details...", font=F_BODY, text_color=C_WARNING, anchor="w", justify="left")
    status_label.pack(fill="x", pady=(3, 8))
    progress_bar = ctk.CTkProgressBar(info_frame, height=10, progress_color=C_ACCENT)
    progress_bar.pack(fill="x", pady=(0, 8))
    progress_bar.set(0)

    action_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
    action_frame.pack(side="right", padx=15)
    cancel_btn = ctk.CTkButton(action_frame, text="✖", fg_color=C_DANGER, width=80, font=("Segoe UI", 12, "bold"))
    cancel_btn.pack(side="right")

    target_folder = audio_path_var.get() if selected_quality == "Just the Tunes (MP3)" else video_path_var.get()
    
    if playlist_var.get():
        threading.Thread(target=fetch_playlist_metadata, args=(url, selected_quality, target_folder, row_frame, thumb_label, title_label, status_label, progress_bar, action_frame, cancel_btn, extra_opts), daemon=True).start()
    else:
        cancel_flag = {'is_cancelled': False}
        cancel_btn.configure(command=lambda: cancel_download(cancel_flag, status_label))
        threading.Thread(target=process_item, args=(url, selected_quality, target_folder, False, thumb_label, title_label, status_label, progress_bar, cancel_flag, action_frame, cancel_btn, extra_opts, None), daemon=True).start()

def process_item(url, quality, target_folder, is_playlist, thumb_label, title_label, status_label, progress_bar, cancel_flag, action_frame, cancel_btn, extra_opts, playlist_items_str):
    def progress_hook(d):
        if cancel_flag['is_cancelled']: raise Exception("USER_CANCELLED")
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            if total > 0:
                percent = d.get('downloaded_bytes', 0) / total
                progress_bar.set(percent)
                status_label.configure(text=f"Status: Slurping bytes... {percent*100:.1f}% 🧃", text_color=C_ACCENT)
        elif d['status'] == 'finished':
            status_label.configure(text="Status: Mixing batter (Finalizing)... 🥣", text_color=C_WARNING)

    # Note: 'quiet' is set to True to prevent windowed .exe crashes!
    ydl_opts = {
        'noplaylist': not is_playlist, 
        'quiet': True, 
        'ignoreerrors': False, 
        'progress_hooks': [progress_hook],
        'ffmpeg_location': resource_path("ffmpeg.exe"), 
        'postprocessors': []
    }
    
    if is_playlist and playlist_items_str: ydl_opts['playlist_items'] = playlist_items_str
    
    ydl_opts['outtmpl'] = os.path.join(target_folder, '%(title)s.%(ext)s')

    if extra_opts.get('art'):
        ydl_opts['writethumbnail'] = True
        ydl_opts['postprocessors'].extend([{'key': 'EmbedThumbnail'}, {'key': 'FFmpegMetadata'}])

    if extra_opts.get('subs') and quality != "Just the Tunes (MP3)":
        lang_map = {
            "English": "en", 
            "Spanish": "es", 
            "Greek": "el", 
            "French": "fr", 
            "German": "de", 
            "Italian": "it", 
            "Japanese": "ja", 
            "All": "all"
        }
        chosen_lang = lang_map.get(extra_opts.get('sub_lang', "English"), "en")
        
        ydl_opts['writesubtitles'] = True
        ydl_opts['writeautomaticsub'] = True
        ydl_opts['subtitleslangs'] = [chosen_lang]
        ydl_opts['postprocessors'].extend([{'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'}, {'key': 'FFmpegEmbedSubtitle'}])

    # Slicing Math & Conversion
    s_sec = 0
    e_sec = float('inf')
    if extra_opts.get('start') or extra_opts.get('end'):
        def t_to_s(s):
            if not s: return None
            try:
                p = list(map(int, s.split(':')))
                if len(p) == 2: return p[0]*60 + p[1]
                if len(p) == 3: return p[0]*3600 + p[1]*60 + p[2]
                return int(s)
            except: return None
            
        s_sec = t_to_s(extra_opts.get('start')) or 0
        e_sec = t_to_s(extra_opts.get('end')) or float('inf') 
        
        if s_sec > 0 or e_sec != float('inf'):
            ydl_opts['download_ranges'] = lambda info, ydl: [{'start_time': s_sec, 'end_time': e_sec}]
            ydl_opts['force_keyframes_at_cuts'] = True

    if quality == "Just the Tunes (MP3)":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'].append({'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'})
    else:
        ydl_opts['merge_output_format'] = 'mp4'
        if quality == "Give me the 4K!": ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality == "Crisp 1080p": ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
        elif quality == "Decent 720p": ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
        else: ydl_opts['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # THE POLITE BUTLER: Check if the user sliced outside the video's actual length!
            duration = info.get('duration')
            if duration and s_sec >= duration:
                app.after(0, lambda: messagebox.showwarning("Slice Out of Bounds 🛑", f"You asked to start slicing at {s_sec} seconds, but this video is only {duration} seconds long!"))
                raise Exception("OUT_OF_BOUNDS")

            title_label.configure(text=info.get('title', 'Unknown Title'))
            if info.get('thumbnail'):
                img = Image.open(BytesIO(requests.get(info['thumbnail']).content))
                thumb_label.configure(image=ctk.CTkImage(img, img, size=(140, 80)), text="")
            ydl.download([url])
            status_label.configure(text="Status: Ding! Served hot. 🍕", text_color=C_SUCCESS)
            progress_bar.set(1.0); cancel_btn.destroy()
            ctk.CTkButton(action_frame, text="📁", fg_color=C_SUCCESS, width=120, command=lambda: open_save_folder(target_folder)).pack(side="right")
    
    except Exception as e:
        if cancel_flag['is_cancelled'] or str(e) == "USER_CANCELLED":
            status_label.configure(text="Status: Thrown in the trash. 🗑️", text_color=C_TEXT_MUTED)
        elif str(e) == "OUT_OF_BOUNDS":
            status_label.configure(text="Status: Slice time was too long! 🛑", text_color=C_DANGER)
        else:
            status_label.configure(text="Status: Munch failed. 🤢", text_color=C_DANGER)
            print(f"\n--- KITCHEN CRASH REPORT ---\n{e}\n----------------------------\n")
        
        if cancel_btn.winfo_exists(): cancel_btn.destroy()

# --- UI Setup ---
app = ctk.CTk(); app.title("Omicron"); app.geometry("1000x720"); app.resizable(True, True); app.configure(fg_color=C_BG_BASE)
icon_path = resource_path("omicron.ico")
if os.path.exists(icon_path):
    try: app.iconbitmap(icon_path)
    except: pass

video_path_var = ctk.StringVar(value=os.path.join(os.path.expanduser('~'), 'Downloads'))
audio_path_var = ctk.StringVar(value=os.path.join(os.path.expanduser('~'), 'Downloads'))

# Define interactive variables first
playlist_var = ctk.BooleanVar()
subs_var = ctk.BooleanVar()
art_var = ctk.BooleanVar()
sub_lang_var = ctk.StringVar(value="English")
start_var = ctk.StringVar()
end_var = ctk.StringVar()

# --- Header ---
top = ctk.CTkFrame(app, fg_color="transparent"); top.pack(fill="x", padx=30, pady=(30, 10))
tl = ctk.CTkFrame(top, fg_color="transparent"); tl.pack(side="left")
ctk.CTkLabel(tl, text="OMICRON", font=F_HEADING).pack(anchor="w")
ctk.CTkLabel(tl, text="We eat URLs for breakfast.", font=F_BODY, text_color=C_TEXT_MUTED).pack(anchor="w")
theme_switch = ctk.CTkSwitch(top, text="Dark Mode", command=toggle_theme); theme_switch.pack(side="right"); theme_switch.select()

# --- Card ---
card = ctk.CTkFrame(app, fg_color=C_CARD_BG, corner_radius=20); card.pack(fill="x", padx=30, pady=10)
ctk.CTkLabel(card, text="Feed me a link:", font=F_SUBHEADING).pack(pady=(15, 5))
ir = ctk.CTkFrame(card, fg_color="transparent"); ir.pack(pady=(0, 10), padx=20)
url_entry = ctk.CTkEntry(ir, width=420, placeholder_text="https://youtu.be/..."); url_entry.pack(side="left", padx=5); url_entry.bind("<Return>", munch_it)
quality_dropdown = ctk.CTkOptionMenu(ir, values=["Give me the 4K!", "Crisp 1080p", "Decent 720p", "Potato 480p", "Just the Tunes (MP3)"], width=170, fg_color=C_BG_BASE, button_color=C_ACCENT)
quality_dropdown.pack(side="left", padx=5); quality_dropdown.set("Crisp 1080p")
ctk.CTkButton(ir, text="Munch It! 🦖", command=munch_it, width=110, height=35, fg_color=C_ACCENT).pack(side="left", padx=5)

# --- Pro Options ---
opr = ctk.CTkFrame(card, fg_color="transparent"); opr.pack(pady=(0, 15), padx=20)

playlist_cb = ctk.CTkCheckBox(opr, text="Playlist 📜", variable=playlist_var, fg_color=C_ACCENT)
playlist_cb.pack(side="left", padx=10)

subs_cb = ctk.CTkCheckBox(opr, text="Subs 🔤", variable=subs_var, fg_color=C_ACCENT)
subs_cb.pack(side="left", padx=(10, 5))

# Replace your current sub_lang_dropdown with this:
sub_lang_dropdown = ctk.CTkOptionMenu(opr, 
    values=["English", "Spanish", "Greek", "French", "German", "Italian", "Japanese", "All"], 
    variable=sub_lang_var, width=80, height=24, font=F_SMALL, 
    fg_color=C_BG_BASE, button_color=C_ACCENT, state="disabled")
sub_lang_dropdown.pack(side="left", padx=(0, 10))

ctk.CTkCheckBox(opr, text="Embed Art 🎨", variable=art_var, fg_color=C_ACCENT).pack(side="left", padx=10)

ctk.CTkLabel(opr, text="Slice:", font=F_SMALL, text_color=C_TEXT_MUTED).pack(side="left", padx=(10, 5))

start_entry = ctk.CTkEntry(opr, textvariable=start_var, width=70, placeholder_text="00:00", fg_color=C_BG_BASE)
start_entry.pack(side="left", padx=2)

ctk.CTkLabel(opr, text="to", font=F_SMALL, text_color=C_TEXT_MUTED).pack(side="left", padx=2)

end_entry = ctk.CTkEntry(opr, textvariable=end_var, width=70, placeholder_text="02:30", fg_color=C_BG_BASE)
end_entry.pack(side="left", padx=2)

# Bind the UI logic AFTER all widgets are created
playlist_cb.configure(command=update_ui_state)
subs_cb.configure(command=update_ui_state)
start_var.trace_add("write", update_ui_state)
end_var.trace_add("write", update_ui_state)

# --- Pantry ---
kit = ctk.CTkFrame(app, fg_color="transparent"); kit.pack(fill="x", padx=30, pady=5)
ctk.CTkLabel(kit, text="Video Pantry:", font=F_SMALL).grid(row=0, column=0); ctk.CTkEntry(kit, textvariable=video_path_var, width=280, state="readonly").grid(row=0, column=1)
ctk.CTkButton(kit, text="Change", width=60, command=lambda: browse_path(video_path_var, "Select Video Folder")).grid(row=0, column=2, padx=5)
ctk.CTkLabel(kit, text="Audio Pantry:", font=F_SMALL).grid(row=0, column=3, padx=(30, 0)); ctk.CTkEntry(kit, textvariable=audio_path_var, width=280, state="readonly").grid(row=0, column=4)
ctk.CTkButton(kit, text="Change", width=60, command=lambda: browse_path(audio_path_var, "Select Audio Folder")).grid(row=0, column=5, padx=5)

queue_frame = ctk.CTkScrollableFrame(app, width=800, height=220, corner_radius=15, fg_color=C_CARD_BG); queue_frame.pack(pady=5, padx=30, fill="both", expand=True)

# --- Footer ---
foot = ctk.CTkFrame(app, fg_color="transparent"); foot.pack(side="bottom", fill="x", pady=(10, 15), padx=40)
ctk.CTkButton(foot, text="Legal Mumbo Jumbo", command=show_disclaimer, fg_color="transparent", text_color=C_TEXT_MUTED, width=80).pack(side="left")
ctk.CTkButton(foot, text="Tip the Chef 👨‍🍳", command=open_patreon, fg_color=C_WARNING, text_color="white", width=100).pack(side="left", padx=10)
uc = ctk.CTkFrame(foot, fg_color="transparent"); uc.pack(side="left", padx=10)
update_btn = ctk.CTkButton(uc, text="Updates 📡", command=lambda: check_updates(False), fg_color="transparent", border_width=1, text_color=C_TEXT_MUTED, width=70); update_btn.pack()
update_dot = ctk.CTkLabel(update_btn, text="", fg_color=C_DANGER, width=10, height=10, corner_radius=5)
sig = ctk.CTkLabel(foot, text="Cooked up by sizon95", text_color=C_ACCENT, font=("Segoe UI", 12, "bold", "underline"), cursor="hand2"); sig.pack(side="right"); sig.bind("<Button-1>", open_portfolio)

# --- THE SPLASH SCREEN (INTRO) ---
def play_intro_splash():
    app.withdraw() # Hide the main window
    splash = ctk.CTkToplevel(app)
    splash.overrideredirect(True) 
    splash.configure(fg_color=C_BG_BASE)

    # Center Splash Screen
    splash_width = 500
    splash_height = 300
    x = int((splash.winfo_screenwidth() / 2) - (splash_width / 2))
    y = int((splash.winfo_screenheight() / 2) - (splash_height / 2))
    splash.geometry(f"{splash_width}x{splash_height}+{x}+{y}")

    brand_lbl = ctk.CTkLabel(splash, text="OMICRON", font=("Segoe UI", 46, "bold"), text_color=C_ACCENT)
    brand_lbl.pack(expand=True, pady=(60, 0))
    dev_lbl = ctk.CTkLabel(splash, text="Cooked up by sizon95", font=("Segoe UI", 14, "italic"), text_color=C_TEXT_MUTED)
    dev_lbl.pack(pady=(0, 30))

    load_bar = ctk.CTkProgressBar(splash, width=300, height=8, progress_color=C_ACCENT, fg_color=("gray80", "gray20"))
    load_bar.pack(pady=(0, 50))
    load_bar.set(0)

    def animate_loading(step=0):
        if step <= 100:
            load_bar.set(step / 100)
            splash.after(20, lambda: animate_loading(step + 1))
        else:
            splash.destroy()
            app.deiconify() # Reveal the main app!
            app.after(1000, lambda: check_updates(silent=True)) # Silent update check

    animate_loading()

play_intro_splash()
app.mainloop()