import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk  
import re
import yt_dlp
import threading
import os
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

# Font Styles
F_HEADING = ("Segoe UI", 24, "bold")
F_SUBHEADING = ("Segoe UI", 16, "bold")
F_BODY = ("Segoe UI", 13)
F_SMALL = ("Segoe UI", 11)

ctk.set_appearance_mode("dark") 

# --- UI Action Functions ---
def toggle_theme():
    if theme_switch.get() == 1:
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")

def open_portfolio(event=None):
    webbrowser.open("https://georgerossis.pages.dev")

def open_patreon():
    webbrowser.open("https://www.patreon.com/posts/cup-of-coffee-154185123?utm_medium=clipboard_copy&utm_source=copyLink&utm_campaign=postshare_creator&utm_content=join_link")

def check_updates():
    # Make sure this matches the 4-digit format from your text file
    CURRENT_VERSION = "1.5.0.0"
    
    # Point directly to your existing version file on GitHub!
    UPDATE_URL = "https://raw.githubusercontent.com/Geoross/omicron/main/version.txt" 
    
    try:
        response = requests.get(UPDATE_URL, timeout=5)
        response.raise_for_status() 
        
        # We use a Regular Expression to hunt down this exact string: u'FileVersion', u'1.5.0.0'
        match = re.search(r"u'FileVersion',\s*u'([\d\.]+)'", response.text)
        
        if match:
            latest_version = match.group(1) # This plucks out exactly "1.5.0.0"
            download_link = "https://georgerossis.pages.dev" # Hardcode your portfolio here
            
            if latest_version > CURRENT_VERSION:
                msg = f"Good news! Version {latest_version} is fresh out of the oven.\n\nYou are currently on v{CURRENT_VERSION}.\n\nWould you like to grab the new batch?"
                if messagebox.askyesno("Update Available! 📡", msg):
                    webbrowser.open(download_link)
            else:
                messagebox.showinfo("Up to Date 🌟", f"You are running the latest version (v{CURRENT_VERSION}). The kitchen is fully stocked!")
        else:
            print("Couldn't parse the version file format.")
            
    except Exception as e:
        messagebox.showerror("Connection Error 🔌", "Couldn't reach the server to check for updates. Make sure you are connected to the internet!")
        
def show_disclaimer():
    msg = (
        "The 'Don't Sue Me' Disclaimer\n\n"
        "This app is a fun educational tool. If you use it to pirate movies, "
        "that's on you, buddy. You are responsible for having the rights to "
        "whatever you munch with this app.\n\n"
        "- sizon95"
    )
    messagebox.showinfo("Legal Mumbo Jumbo", msg)

def browse_path(var_to_update, title):
    folder = filedialog.askdirectory(title=title)
    if folder:
        var_to_update.set(folder)

def cancel_download(cancel_flag, status_label):
    cancel_flag['is_cancelled'] = True
    status_label.configure(text="Status: Whoa, stopping! 🛑", text_color=C_DANGER)

def open_save_folder(path):
    try:
        os.startfile(path)
    except Exception as e:
        print(f"Could not open folder: {e}")

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

    lbl = ctk.CTkLabel(popup, text=f"Playlist: {info.get('title', 'Unknown')}", font=F_SUBHEADING, text_color=C_TEXT_MAIN)
    lbl.pack(pady=(20, 5), padx=20, anchor="w")
    
    desc_lbl = ctk.CTkLabel(popup, text="Choose which items you want to munch:", font=F_BODY, text_color=C_TEXT_MUTED)
    desc_lbl.pack(padx=20, anchor="w", pady=(0, 10))

    select_all_var = ctk.BooleanVar(value=True)
    checkbox_vars = []

    def toggle_all():
        state = select_all_var.get()
        for _, var in checkbox_vars:
            var.set(state)

    sa_cb = ctk.CTkCheckBox(popup, text="Select / Deselect All", variable=select_all_var, command=toggle_all, font=F_BODY, fg_color=C_ACCENT, text_color=C_TEXT_MAIN)
    sa_cb.pack(pady=(0, 10), padx=20, anchor="w")

    scroll = ctk.CTkScrollableFrame(popup, fg_color=C_CARD_BG, corner_radius=10)
    scroll.pack(pady=5, padx=20, fill="both", expand=True)

    for i, entry in enumerate(entries):
        if not entry: continue 
        var = ctk.BooleanVar(value=True) 
        checkbox_vars.append((i + 1, var)) 
        title = entry.get('title', f'Unknown Video {i+1}')
        cb = ctk.CTkCheckBox(scroll, text=f"{i+1}. {title}", variable=var, font=F_SMALL, text_color=C_TEXT_MAIN, fg_color=C_ACCENT)
        cb.pack(anchor="w", pady=5, padx=5)

    def confirm_selection():
        selected_indices = [str(idx) for idx, var in checkbox_vars if var.get()]
        if not selected_indices:
            messagebox.showwarning("Empty Plate", "You didn't select anything to munch!", parent=popup)
            return

        items_str = ",".join(selected_indices)
        popup.destroy()

        status_label.configure(text=f"Status: Selected {len(selected_indices)} videos. Firing up the oven... 🔥", text_color=C_WARNING)
        cancel_flag = {'is_cancelled': False}
        cancel_btn.configure(command=lambda: cancel_download(cancel_flag, status_label))
        
        threading.Thread(target=process_item, args=(url, quality, target_folder, True, thumb_label, title_label, status_label, progress_bar, cancel_flag, action_frame, cancel_btn, extra_opts, items_str), daemon=True).start()

    btn = ctk.CTkButton(popup, text="Confirm & Munch! 🦖", font=F_SUBHEADING, command=confirm_selection, fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER, text_color="white", height=40)
    btn.pack(pady=20, padx=20, fill="x")

# --- Fast Metadata Fetcher ---
def fetch_playlist_metadata(url, quality, target_folder, row_frame, thumb_label, title_label, status_label, progress_bar, action_frame, cancel_btn, extra_opts):
    ydl_opts = {'extract_flat': 'in_playlist', 'quiet': True, 'ignoreerrors': True, 'ffmpeg_location': resource_path("")}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        if 'entries' not in info:
            app.after(0, lambda: status_label.configure(text="Status: Not a playlist. Munching normally... 🦖", text_color=C_WARNING))
            cancel_flag = {'is_cancelled': False}
            cancel_btn.configure(command=lambda: cancel_download(cancel_flag, status_label))
            threading.Thread(target=process_item, args=(url, quality, target_folder, False, thumb_label, title_label, status_label, progress_bar, cancel_flag, action_frame, cancel_btn, extra_opts, None), daemon=True).start()
            return
            
        entries = info['entries']
        app.after(0, show_playlist_popup, info, entries, url, quality, target_folder, row_frame, thumb_label, title_label, status_label, progress_bar, action_frame, cancel_btn, extra_opts)
            
    except Exception as e:
        app.after(0, lambda: status_label.configure(text="Status: Couldn't read the playlist. Is it private? 🛑", text_color=C_DANGER))
        app.after(0, cancel_btn.destroy)

def munch_it(event=None):
    url = url_entry.get()
    selected_quality = quality_dropdown.get()
    is_playlist = playlist_var.get() 
    
    extra_opts = {
        'subs': subs_var.get(),
        'start': start_var.get().strip(),
        'end': end_var.get().strip()
    }
    
    if not url:
        messagebox.showwarning("Hold up!", "You gotta feed me a link first!")
        return
    
    url_entry.delete(0, ctk.END)
    
    row_frame = ctk.CTkFrame(queue_frame, corner_radius=15, fg_color=C_CARD_BG, border_width=1, border_color=C_ACCENT)
    row_frame.pack(fill="x", pady=8, padx=5)
    
    thumb_label = ctk.CTkLabel(row_frame, text="Looking...", width=140, height=80, fg_color=("gray80", "gray20"), corner_radius=10)
    thumb_label.pack(side="left", padx=15, pady=15)
    
    info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
    info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=15)
    
    title_text = "Reading the Playlist Menu..." if is_playlist else "Sniffing the link..."
    title_label = ctk.CTkLabel(info_frame, text=title_text, font=F_SUBHEADING, text_color=C_TEXT_MAIN, anchor="w", justify="left")
    title_label.pack(fill="x")
    
    status_label = ctk.CTkLabel(info_frame, text=f"Status: Fetching details...", font=F_BODY, text_color=C_WARNING, anchor="w", justify="left")
    status_label.pack(fill="x", pady=(3, 8))

    progress_bar = ctk.CTkProgressBar(info_frame, height=10, progress_color=C_ACCENT, fg_color=("gray80", "gray20"))
    progress_bar.pack(fill="x", pady=(0, 8))
    progress_bar.set(0)

    action_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
    action_frame.pack(side="right", padx=15)

    cancel_btn = ctk.CTkButton(action_frame, text="✖", fg_color=C_DANGER, hover_color="#B91C1C", text_color="white", width=80, font=("Segoe UI", 12, "bold"))
    cancel_btn.pack(side="right")

    if selected_quality == "Just the Tunes (MP3)":
        target_folder = audio_path_var.get()
    else:
        target_folder = video_path_var.get()

    if is_playlist:
        threading.Thread(target=fetch_playlist_metadata, args=(url, selected_quality, target_folder, row_frame, thumb_label, title_label, status_label, progress_bar, action_frame, cancel_btn, extra_opts), daemon=True).start()
    else:
        cancel_flag = {'is_cancelled': False}
        cancel_btn.configure(command=lambda: cancel_download(cancel_flag, status_label))
        threading.Thread(target=process_item, args=(url, selected_quality, target_folder, False, thumb_label, title_label, status_label, progress_bar, cancel_flag, action_frame, cancel_btn, extra_opts, None), daemon=True).start()

# --- The Download Engine ---
def process_item(url, quality, target_folder, is_playlist, thumb_label, title_label, status_label, progress_bar, cancel_flag, action_frame, cancel_btn, extra_opts, playlist_items_str):
    
    def progress_hook(d):
        if cancel_flag['is_cancelled']:
            raise Exception("USER_CANCELLED")
            
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percent = downloaded / total
                progress_bar.set(percent)
                speed = d.get('_speed_str', '').strip()
                
                if is_playlist:
                    idx = d.get('info_dict', {}).get('playlist_index', '?')
                    current_vid = d.get('info_dict', {}).get('title', 'Video')
                    status_label.configure(text=f"Status: Slurping #{idx} ({current_vid[:20]}...) - {percent*100:.1f}%", text_color=C_ACCENT)
                else:
                    status_label.configure(text=f"Status: Slurping bytes... {percent*100:.1f}% ({speed}) 🧃", text_color=C_ACCENT)
        
        elif d['status'] == 'finished':
            if is_playlist:
                status_label.configure(text="Status: Mixing batter for this item... 🥣", text_color=C_WARNING)
            else:
                progress_bar.set(1.0)
                status_label.configure(text="Status: Mixing batter (Merging)... 🥣", text_color=C_WARNING)

    ydl_opts = {
        'noplaylist': not is_playlist, 
        'quiet': True,
        'ignoreerrors': True,  
        'progress_hooks': [progress_hook],
        'ffmpeg_location': resource_path(""),
        'postprocessors': [] 
    }

    if is_playlist and playlist_items_str:
        ydl_opts['playlist_items'] = playlist_items_str

    if is_playlist:
        ydl_opts['outtmpl'] = os.path.join(target_folder, '%(playlist_title|Playlist)s', '%(playlist_index|0)s - %(title)s.%(ext)s')
        final_open_path = os.path.join(target_folder, '%(playlist_title|Playlist)s') 
    else:
        ydl_opts['outtmpl'] = os.path.join(target_folder, '%(title)s.%(ext)s')
        final_open_path = target_folder

    # --- PRO TOOL 1: Subtitle Grabber ---
    if extra_opts.get('subs') and quality != "Just the Tunes (MP3)":
        ydl_opts['writesubtitles'] = True
        ydl_opts['writeautomaticsub'] = True 
        ydl_opts['subtitleslangs'] = ['en']  
        ydl_opts['postprocessors'].append({'key': 'FFmpegEmbedSubtitle'})

    # --- PRO TOOL 2: Time-Slice Cutter ---
    if extra_opts.get('start') or extra_opts.get('end'):
        from yt_dlp.utils import download_range_func
        def time_to_sec(t_str):
            if not t_str: return None
            try:
                parts = list(map(int, t_str.split(':')))
                if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
                if len(parts) == 2: return parts[0]*60 + parts[1]
                return parts[0]
            except:
                return None
        
        start_sec = time_to_sec(extra_opts.get('start')) or 0
        end_sec = time_to_sec(extra_opts.get('end')) or 999999
        
        if start_sec > 0 or end_sec < 999999:
            ydl_opts['download_ranges'] = download_range_func(None, [(start_sec, end_sec)])
            ydl_opts['force_keyframes_at_cuts'] = True

    # Quality Logic
    if quality == "Just the Tunes (MP3)":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        })
    else:
        ydl_opts['merge_output_format'] = 'mp4'
        if quality == "Give me the 4K!":
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality == "Crisp 1080p":
            ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
        elif quality == "Decent 720p":
            ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
        elif quality == "Potato 480p":
            ydl_opts['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            status_label.configure(text=f"Status: Reading the final menu...", text_color=C_WARNING)
            
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown Title')
            
            thumbnail_url = None
            if is_playlist and 'entries' in info and len(info['entries']) > 0:
                for entry in info['entries']:
                    if entry:
                        thumbnail_url = entry.get('thumbnail', None)
                        break
                final_open_path = os.path.join(target_folder, info.get('title', 'Playlist').replace('/', '_'))
            else:
                thumbnail_url = info.get('thumbnail', None)

            title_label.configure(text=title)

            if thumbnail_url:
                try:
                    response = requests.get(thumbnail_url)
                    img_data = Image.open(BytesIO(response.content))
                    ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(140, 80))
                    thumb_label.configure(image=ctk_img, text="", corner_radius=10)
                except:
                    pass 

            ydl.download([url])
            
            if is_playlist:
                status_label.configure(text="Status: Ding! Selected items served. 🍕", text_color=C_SUCCESS)
            else:
                status_label.configure(text="Status: Ding! Served hot. 🍕", text_color=C_SUCCESS)
                
            cancel_btn.destroy() 
            
            open_btn = ctk.CTkButton(action_frame, text="📁", fg_color=C_SUCCESS, hover_color="#059669", text_color="white", width=120, font=("Segoe UI", 12, "bold"), command=lambda: open_save_folder(final_open_path))
            open_btn.pack(side="right")

    except Exception as e:
        if cancel_flag['is_cancelled'] or str(e) == "USER_CANCELLED":
            status_label.configure(text="Status: Thrown in the trash. 🗑️", text_color=C_TEXT_MUTED)
            if cancel_btn.winfo_exists():
                cancel_btn.destroy()
        else:
            status_label.configure(text="Status: Blegh. Bad link or YouTube is mad. 🤢", text_color=C_DANGER)
            print(f"Error: {e}")

# --- Set up the App Window ---
app = ctk.CTk()
app.title("Omicron")
app.geometry("1000x720")
app.resizable(False, True) 
app.configure(fg_color=C_BG_BASE)

icon_path = resource_path("omicron.ico")
if os.path.exists(icon_path):
    try:
        app.iconbitmap(icon_path)
    except Exception as e:
        pass

default_download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
video_path_var = ctk.StringVar(value=default_download_path)
audio_path_var = ctk.StringVar(value=default_download_path)

# --- Top Bar ---
top_bar = ctk.CTkFrame(app, fg_color="transparent")
top_bar.pack(fill="x", padx=30, pady=(30, 10))

title_stack = ctk.CTkFrame(top_bar, fg_color="transparent")
title_stack.pack(side="left")

app_title_lbl = ctk.CTkLabel(title_stack, text="OMICRON", font=F_HEADING, text_color=C_TEXT_MAIN)
app_title_lbl.pack(anchor="w")
author_lbl = ctk.CTkLabel(title_stack, text="We eat URLs for breakfast.", font=F_BODY, text_color=C_TEXT_MUTED)
author_lbl.pack(anchor="w")

theme_switch = ctk.CTkSwitch(top_bar, text="Dark Mode", font=F_BODY, text_color=C_TEXT_MAIN, progress_color=C_ACCENT, command=toggle_theme)
theme_switch.pack(side="right")
theme_switch.select() 

# --- Main Action Card ---
action_card = ctk.CTkFrame(app, fg_color=C_CARD_BG, corner_radius=20)
action_card.pack(fill="x", padx=30, pady=10)

instructions = ctk.CTkLabel(action_card, text="Feed me a link:", font=F_SUBHEADING, text_color=C_TEXT_MAIN)
instructions.pack(pady=(15, 5))

# Row 1: URL, Quality, Button
input_row = ctk.CTkFrame(action_card, fg_color="transparent")
input_row.pack(pady=(0, 10), padx=20)

url_entry = ctk.CTkEntry(input_row, width=420, placeholder_text="https://youtu.be/...", font=F_BODY, fg_color=C_BG_BASE, border_color=C_TEXT_MUTED)
url_entry.pack(side="left", padx=5)
url_entry.bind("<Return>", munch_it)

# --- Custom Clipboard Functions ---
def menu_copy():
    app.clipboard_clear()
    if url_entry.get(): 
        app.clipboard_append(url_entry.get())
        
def menu_cut():
    menu_copy()
    url_entry.delete(0, ctk.END)
    
def menu_paste():
    try:
        text = app.clipboard_get()
        url_entry.insert(ctk.END, text)
    except tk.TclError:
        pass 

# Menu belongs to `app` to prevent ghost window crashes!
context_menu = tk.Menu(app, tearoff=False, bg="#1F2937", fg="white", activebackground="#6366F1", borderwidth=0, font=("Segoe UI", 12))
context_menu.add_command(label="Cut", command=menu_cut)
context_menu.add_command(label="Copy", command=menu_copy)
context_menu.add_command(label="Paste", command=menu_paste)

def show_context_menu(event):
    context_menu.tk_popup(event.x_root, event.y_root)

url_entry.bind("<Button-3>", show_context_menu)

qualities = ["Give me the 4K!", "Crisp 1080p", "Decent 720p", "Potato 480p", "Just the Tunes (MP3)"]
quality_dropdown = ctk.CTkOptionMenu(input_row, values=qualities, font=F_BODY, width=170, fg_color=C_BG_BASE, text_color=C_TEXT_MAIN, button_color=C_ACCENT, button_hover_color=C_ACCENT_HOVER)
quality_dropdown.pack(side="left", padx=5)
quality_dropdown.set("Crisp 1080p") 

action_btn = ctk.CTkButton(input_row, text="Munch It! 🦖", font=F_SUBHEADING, command=munch_it, width=110, height=35, fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER, text_color="white")
action_btn.pack(side="left", padx=5)

# --- Row 2 - Pro Tools (Subtitles & Time Slice) ---
options_row = ctk.CTkFrame(action_card, fg_color="transparent")
options_row.pack(pady=(0, 15), padx=20)

playlist_var = ctk.BooleanVar(value=False)
playlist_cb = ctk.CTkCheckBox(options_row, text="Playlist Mode 📜", variable=playlist_var, font=F_BODY, text_color=C_TEXT_MAIN, fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER, border_color=C_TEXT_MUTED)
playlist_cb.pack(side="left", padx=10)

subs_var = ctk.BooleanVar(value=False)
subs_cb = ctk.CTkCheckBox(options_row, text="Grab Subtitles 🔤", variable=subs_var, font=F_BODY, text_color=C_TEXT_MAIN, fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER, border_color=C_TEXT_MUTED)
subs_cb.pack(side="left", padx=10)

slice_lbl = ctk.CTkLabel(options_row, text="Slice (Optional):", font=F_SMALL, text_color=C_TEXT_MUTED)
slice_lbl.pack(side="left", padx=(20, 5))

start_var = ctk.StringVar(value="")
start_entry = ctk.CTkEntry(options_row, textvariable=start_var, width=80, placeholder_text="00:00", font=F_SMALL, fg_color=C_BG_BASE, border_color=C_TEXT_MUTED)
start_entry.pack(side="left", padx=2)

to_lbl = ctk.CTkLabel(options_row, text="to", font=F_SMALL, text_color=C_TEXT_MUTED)
to_lbl.pack(side="left", padx=2)

end_var = ctk.StringVar(value="")
end_entry = ctk.CTkEntry(options_row, textvariable=end_var, width=80, placeholder_text="02:30", font=F_SMALL, fg_color=C_BG_BASE, border_color=C_TEXT_MUTED)
end_entry.pack(side="left", padx=2)

# --- The Kitchen (Settings) ---
kitchen_card = ctk.CTkFrame(app, fg_color="transparent")
kitchen_card.pack(fill="x", padx=30, pady=5)

video_lbl = ctk.CTkLabel(kitchen_card, text="Video Pantry:", font=F_SMALL, text_color=C_TEXT_MUTED)
video_lbl.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="e")
video_entry = ctk.CTkEntry(kitchen_card, textvariable=video_path_var, width=280, font=F_SMALL, state="readonly", fg_color=C_CARD_BG, border_width=0)
video_entry.grid(row=0, column=1, padx=5, pady=5)
video_browse_btn = ctk.CTkButton(kitchen_card, text="Change", width=60, font=F_SMALL, fg_color=C_TEXT_MUTED, hover_color="gray", command=lambda: browse_path(video_path_var, "Select Video Folder"))
video_browse_btn.grid(row=0, column=2, padx=5, pady=5)

audio_lbl = ctk.CTkLabel(kitchen_card, text="Audio Pantry:", font=F_SMALL, text_color=C_TEXT_MUTED)
audio_lbl.grid(row=0, column=3, padx=(30, 10), pady=5, sticky="e")
audio_entry = ctk.CTkEntry(kitchen_card, textvariable=audio_path_var, width=280, font=F_SMALL, state="readonly", fg_color=C_CARD_BG, border_width=0)
audio_entry.grid(row=0, column=4, padx=5, pady=5)
audio_browse_btn = ctk.CTkButton(kitchen_card, text="Change", width=60, font=F_SMALL, fg_color=C_TEXT_MUTED, hover_color="gray", command=lambda: browse_path(audio_path_var, "Select Audio Folder"))
audio_browse_btn.grid(row=0, column=5, padx=5, pady=5)

# --- The Oven (Queue Area) ---
queue_lbl = ctk.CTkLabel(app, text="The Oven (Queue)", font=F_SUBHEADING, text_color=C_TEXT_MAIN)
queue_lbl.pack(anchor="w", padx=35, pady=(10, 0))

queue_frame = ctk.CTkScrollableFrame(app, width=800, height=220, corner_radius=15, fg_color=C_CARD_BG)
queue_frame.pack(pady=5, padx=30, fill="both", expand=True)

# --- Footer Section ---
footer_frame = ctk.CTkFrame(app, fg_color="transparent")
footer_frame.pack(side="bottom", fill="x", pady=(10, 15), padx=40)

disclaimer_btn = ctk.CTkButton(footer_frame, text="Legal Mumbo Jumbo", command=show_disclaimer, fg_color="transparent", text_color=C_TEXT_MUTED, hover_color=C_CARD_BG[1], font=F_SMALL, width=80)
disclaimer_btn.pack(side="left")

tip_btn = ctk.CTkButton(footer_frame, text="Tip the Chef 👨‍🍳", command=open_patreon, fg_color=C_WARNING, hover_color="#D97706", text_color="white", font=F_SMALL, width=100)
tip_btn.pack(side="left", padx=10) 

update_btn = ctk.CTkButton(footer_frame, text="Updates 📡", command=check_updates, fg_color="transparent", border_width=1, border_color=C_TEXT_MUTED, text_color=C_TEXT_MUTED, hover_color=C_CARD_BG[1], font=F_SMALL, width=70)
update_btn.pack(side="left", padx=10)

signature_label = ctk.CTkLabel(footer_frame, text="Cooked up by sizon95", text_color=C_ACCENT, font=("Segoe UI", 12, "bold", "underline"), cursor="hand2")
signature_label.pack(side="right")
signature_label.bind("<Button-1>", open_portfolio) 

app.mainloop()