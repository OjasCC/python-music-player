import pickle
import random
import threading
from datetime import *

from pyglet import *
from tkinter import *
from tkinter import filedialog
from pebble import concurrent


###### other ######
@concurrent.process
def ask():  # asks for directory but as a multiprocess :/
    root = Tk()
    root.withdraw()
    dir = filedialog.askdirectory()
    return dir


class PopupSliderButton(Button):  # creates a button which pops out a slider

    def __init__(self, parent, **kwargs):
        super().__init__(parent,
                         **kwargs)  # if class is given arguments during initialization this line adds those parameters to the parent button
        self.configure(command=self.toggle)  # pressing the button will show/hide the slider
        self.sliderframe = Frame(self.winfo_toplevel(), bd=1, relief="raised")  # frame of the slider
        self.slider = Scale(self.sliderframe, from_=0, to_=100, background=self.sliderframe.cget("background"),
                            showvalue=0, command=self.adjust_vol, orient='horizontal')  # the scale
        self.slider.set(player.volume*100)  # default value of volume scale is 100 (should be more than enough)
        self.slider.pack(fill="both", expand=True, padx=4, pady=4)  # making sure the slider looks and places properly

    def get(self):  # returns the value at which slider is currently present
        return self.slider.get()

    def inc_vol(self, event=None):  # increases the volume by 5
        self.slider.set((self.slider.get() + 10) if self.slider.get() < 100 else 100)
        player.volume = self.slider.get() / 100  # converts sliders return value between 0 to 1

    def dec_vol(self, event=None):  # decreases volume by 5
        self.slider.set((self.slider.get() - 10) if self.slider.get() > 0 else 0)
        player.volume = self.slider.get() / 100  # converts sliders return value between 0 to 1

    def toggle(self, event=None):  # changes visibility of the slider when pressed on the button
        if self.sliderframe.winfo_viewable():  # hides the slider
            self.sliderframe.place_forget()
        else:
            self.sliderframe.place(in_=self, x=25, y=30, anchor="sw")  # shows the slider

    def adjust_vol(self, event=None):  # if volume is changed by cursor this function automatically adjusts the volume
        player.volume = self.get() / 100


class PopupEntryButton(Button):  # same thing as popup slider but with entry widget

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.configure(command=self.toggle)
        self.entryframe = Frame(self.winfo_toplevel(), bd=1, relief="raised")

        self.entry = Entry(self.entryframe, validate='key', bg='light grey')
        self.entry['validatecommand'] = (self.entry.register(self.find), '%P')
        self.entry.pack(fill="both", expand=True, padx=4, pady=4)
        self.entry.bind('<Return>', self.toggle)

    def toggle(self, event=None):

        if search_btn['state'] == DISABLED:
            return 'break'
        if add_btn.winfo_ismapped()==True:
            return 'break'

        if self.entryframe.winfo_viewable():
            song_list.focus()
            song_list.activate(0)
            song_list.select_set(0)
            self.entryframe.place_forget()

        else:
            self.entry.delete(0, END)
            self.entryframe.place(in_=self, x=25, y=30, anchor="sw")
            self.entry.focus()

    def find(self, search_word, event=None):  # everytime the entry widget is changed , similar search results are shown
        global song_list
        global current_song_list
        menu_options(1)

        playlist_lbl.configure(text='"'+search_word+'" Results')
        current_song_list = []

        for i in actual_song_list:
            if search_word in i.lower():
                current_song_list.append(i)

        song_list.delete(0, END)
        if len(current_song_list) == 0:
            song_list.insert(END, "No Songs found...")

        song_list.insert(END, *[os.path.splitext(os.path.basename(a))[0] for a in current_song_list])

        if search_word=="":
            if dir_name=='':
                playlist_lbl.configure(text="All songs")
            else:
                playlist_lbl.configure(text=dir_name)



        return True


class play: #class to store playlist name and the songs in it
    def __init__(self, playlist_name, songs):
        self.playlist_name = playlist_name
        self.songs = songs


class settings:
    def __init__(self,volume):
        self.volume=volume

###################

######### process ########
def choose_directory(event=None,n=1):  # allows user to choose directory and displays all the songs ONLY in that directory
    global dir_name
    global current_index
    global current_song_list

    if dir_btn['state'] == DISABLED:  # if button is disabled then this function will not be executed
        return 'break'

    if song_list.winfo_ismapped() == False: # if main song playing list is not shown, this function shows it
        show_all_songs()

    tmp_dir = dir_name
    player.pause()
    play_btn.configure(text=' ▶ ')

    player.delete()  # this ensures currently playing song isn't
    player.next_source()  # carried on when new directory is selected

    if n == 1:
        future = ask()  # starts multiprocess to ask directory :/
        dir_name = future.result()
    else:
        dir_name = ""  # setting dir_name="" makes the program look for songs in the current directory
   ###################
    if dir_name == '':
        if tmp_dir != '':
            files = os.listdir(tmp_dir)
            dir_name = tmp_dir
        else:
            return 'break'
    else:
        files = os.listdir(dir_name)
    ### this condition is just incase 'directory is asked' by mistake so on closing 'select folder' the current directory is not lost ####

    current_song_list.clear()
    song_list.delete(0, END)

    for file in files: #this loops starts adding the directory songs into the main song plsying list
        if file.endswith(extensions) and os.path.splitext(file)[0] not in [os.path.splitext(os.path.basename(a))[0] for
                                                                           a in current_song_list]:
            current_song_list.append(str(os.path.join(dir_name, file)))
            song_list.insert(END, os.path.splitext(file)[0])

    if len(current_song_list) == 0:  # checks if given directory has any songs in it or not
        song_list.insert(END, "No Songs found...")

    playlist_lbl.configure(text=dir_name) # sets the heading as the name of the directory which is loaded
    scroll.config(command=song_list.yview)
    if tmp_dir != dir_name: #if asking for directory is pressed by mistake this ensures the currently playing song is not lost
        current_index = 0


#####

def control_song(event=None, n=0):  # plays/pauses song accordingly , if n!=0 pauses the song
    try:
        global play_btn
        global current_index
        global dir_name
        global src

        if player.source == None:  # if no song was previously playing then it automatically starts the first song
            play_new_song()
            player.pause()

        if player.playing or n != 0:   #pauses
            player.pause()
            play_btn.configure(text=' ▶ ')
        else:
            player.play()
            play_btn.configure(text=' || ') #plays
    except:
        ()
    return 'break'


def play_new_song(event=None, isclicked=0):  # allows user to double left click on a new song to start playing
    global src
    global total_play_time_lbl
    global play_time_lbl
    global current_index
    global player
    global play_btn
    global adding_songs



    try:
        try:
            if song_list.get(current_index)[0] == '▶' and current_index != song_list.index(ACTIVE): #removes the playing symbol from previously playing song
                t = 0
                if current_index in song_list.curselection():
                    t = 1

                temp = song_list.get(current_index)[1:]
                song_list.delete(current_index)
                song_list.insert(current_index, temp)
                if t == 1:
                    song_list.select_set(current_index)



        except:
            ()

        try:
            if isclicked == 1:
                current_index = song_list.index(ACTIVE)

        except:
            ()

        src = media.load(current_song_list[current_index], streaming=False)
        player.pause()
        player.delete()
        player.next_source()
        player.queue(src)
        playing_slider.configure(to=src.duration)
        try:
            if not adding_songs.is_alive():
                stat_lbl.configure(text=os.path.splitext(os.path.basename(current_song_list[current_index]))[0])

        except:
            stat_lbl.configure(text=os.path.splitext(os.path.basename(current_song_list[current_index]))[0])


        try:
            t2 = 0
            if song_list.get(current_index)[0] != '▶':  #adds playing symbol to the song which is playing
                if current_index in song_list.curselection():
                    t2 = 1
                temp = song_list.get(current_index)
                song_list.delete(current_index)
                song_list.insert(current_index, '▶' + temp)
                if t2 == 1:
                    song_list.select_set(current_index)
                song_list.activate(current_index)


        except:()




        control_song()
        total_play_time_lbl.configure(text=str(timedelta(seconds=int(src.duration))))  #sets the total duration of the song length

    except:
        play_time_lbl.configure(text='0:00:00')
        total_play_time_lbl.configure(text='0:00:00')
        player.seek(0)
        control_song(n=-1)
        playing_slider.configure(to=0)

    return 'break'


def play_next_song(event=None): # if player presses the right arrow key or presses the next button, this command starts the next song
    global current_index

    try:  #removes the playing symbol from previously playing song
        if song_list.get(current_index)[0] == '▶':
            temp = song_list.get(current_index)[1:]
            song_list.delete(current_index)
            song_list.insert(current_index, temp)
    except:
        ()

    try:
        if loop_status == 1: # if looping a single mode is on then automatically plays the same song again
            ()

        elif shuffle == False: # if shuffle is off
            current_index = current_index + 1

        else: #if shuffle is on, a random new song will start playing
            current_index = random.randint(0, len(current_song_list) - 1)


    except:
        current_index = 1

    if current_index >= len(current_song_list): #if the end of the song list is reached then this plays the first song looping again
        current_index = 0

    try:
        current_song_list[current_index]
    except:
        player.seek(0)
        control_song(n=-1)
        return 'break'

    play_new_song() #actually plays the song

    if loop_status == 0 and current_index == 0 and shuffle == False: #if repeat all songs is off then the first song is selected but is paused
        control_song()

    return 'break'


def play_previous_song(event=None): #plays the previous song OR rewinds to the start of the song if pressed late
    global current_index
    if player.time > 5: #plays the song again from start if the song had been playing for more then 5 secs
        player.pause()
        player.delete()
        player.seek(0)
        player.play()
        return 'break'
    try: #removes the playing symbol from previously playing song
        if song_list.get(current_index)[0] == '▶':
            temp = song_list.get(current_index)[1:]
            song_list.delete(current_index)
            song_list.insert(current_index, temp)
    except:
        ()

    try:
        current_index = current_index - 1 #selecting the previous song
    except:
        current_index = -1 #no previous song is found

    if current_index < 0: # selects the last song going backwards from the front
        current_index = len(current_song_list) - 1

    try:
        current_song_list[current_index]
    except:
        player.seek(0)
        control_song(n=-1)
        return 'break'

    play_new_song()
    return 'break'


######
def hold(event=None): #if the song duration slider is held onto
    global slider_pressed
    slider_pressed = True


def rel(event=None): # if song duration slider is released
    global slider_pressed
    tmp = 0
    if player.playing: #to ensure on changing the slider the song doesn't start playing
        tmp = 1
    player.pause()
    player.delete()
    player.seek(playing_slider.get())

    if tmp == 1:
        player.play()
    slider_pressed = False


def loop_control(event=None):  # loop_status=1 (loop the current song), 2 (loop the playlist). 0 (play the entire playlist only once)
    global loop_status
    global loop_btn
    if loop_status == 0:
        loop_status = 1
        loop_btn.configure(text='↻1')


    elif loop_status == 1:
        loop_status = 2
        loop_btn.configure(text='↻')
    else:
        loop_status = 0
        loop_btn.configure(text='↻×')


def ctrl_shuffle(event=None): #change shuffle state
    global shuffle
    global shuffle_btn

    if shuffle == False:
        shuffle = True
        shuffle_btn.configure(text='🔀')
    else:
        shuffle = False
        shuffle_btn.configure(text='➡')


def min(event=None): #minimizes the entire player
    window.wm_state('iconic')
    song_list.focus()


def add_all_songs(): #adds ALL the songs from the C: drive
    global current_song_list
    global song_list
    global stat_lbl
    global actual_song_list

    dir_btn['state'] = DISABLED
    playlist_btn['state'] = DISABLED
    search_btn['state'] = DISABLED

    current_song_list = []
    stat_lbl.configure(text='adding songs...')
    exclude = {'Program Files', 'Program Files (x86)'}
    for root, dirs, files in os.walk("C:\\"):
        dirs[:] = [d for d in dirs if d not in exclude]
        for file in files:
            if file.endswith(extensions) and os.path.splitext(file)[0] not in [os.path.splitext(os.path.basename(a))[0]
                                                                               for a in current_song_list]:
                current_song_list.append(str(os.path.join(root, file)))
                song_list.insert(END, os.path.splitext(file)[0])

    actual_song_list = current_song_list
    try:
        print("inside try")
        tmp_li=pickle.load(open("playlists.dat","rb"))
        print("found playlist.dat")
        tmp_li[0].songs = actual_song_list
        print("got tmp_li[0].songs")

    except:
        print("in except")
        tmp_li = [play("All", current_song_list)]


    pickle.dump(tmp_li, open("playlists.dat", "wb"))
    stat_lbl.configure(text='')

    if len(current_song_list) == 0:  # checks if there are any songs at all
        song_list.insert(END, "No Songs found...")
    dir_btn['state'] = NORMAL
    playlist_btn['state'] = NORMAL
    search_btn['state'] = NORMAL
    add_all_options()
    song_list.activate(0)
    song_list.select_set(0)
    menu_options(1)
    try:
        stat_lbl.configure(text=os.path.splitext(os.path.basename(current_song_list[current_index]))[0])
    except:()


def show_all_songs(event=None): #shows all the songs
    global entry_playlist
    global add_btn
    global playlist_box
    global song_list
    global current_song_list
    global adding_songs
    global playlists
    global actual_song_list
    global dir_name

    dir_name=''

    if add_btn.winfo_ismapped() == True: #if playlist selection list is visible
        entry_playlist.grid_forget()
        add_btn.grid_forget()
        playlist_box.grid_forget()

    if song_list.winfo_ismapped() == False: #if main song list is not shown
        song_list.grid(row=0, rowspan=2, sticky='nswe')

    playlist_lbl.configure(text="All Songs")

    song_list.focus()
    song_list.delete(0, END)

    try: #if playlists.dat file exist then it loads the 1 playlist which is ALL songs (by default)
        playlists = pickle.load(open("playlists.dat", "rb"))

        temp_li = [os.path.splitext(os.path.split(a)[1])[0] for a in playlists[0].songs]

        actual_song_list = playlists[0].songs #keeps an actual song list so that songs are not lost in search
        current_song_list = actual_song_list

        song_list.insert(END, *temp_li)

        if len(current_song_list) == 0:  # checks if given directory has any songs in it or not
            song_list.insert(END, "No Songs found...")
        try:
            temp = song_list.get(current_index)
            song_list.delete(current_index)
            song_list.insert(current_index, '▶' + temp)
        except:
            ()

        add_all_options()
        song_list.activate(0)
        song_list.select_set(0)
        menu_options(1)


    except: #if playlists.dat file is missing, creates a new file
        adding_songs = threading.Thread(target=add_all_songs)
        adding_songs.start()

    scroll.config(command=song_list.yview)


def delete_playlist():
    try:
        temp = pickle.load(open("playlists.dat", "rb"))
        del temp[playlist_box.index(ACTIVE) + 1]
        pickle.dump(temp, open("playlists.dat", "wb"))
    except:()
    show_playlists()


def remove_from_playlist():
    global playlist_number
    temp = pickle.load(open("playlists.dat", "rb"))

   # print(temp[playlist_number].playlist_name)
   # print(temp[playlist_number].songs)

    selected=song_list.curselection()

   # print(selected)
    temp[playlist_number].songs=[temp[playlist_number].songs[i] for i in range(0,len(temp[playlist_number].songs)) if i not in selected ]

    pickle.dump(temp,open("playlists.dat", "wb"))
   # print([i.playlist_name for i in temp])
    show_playlist_songs(playlist_n=playlist_number)

########## playlist #########

def up(lst_box): #to go up and if out of options, loop back to the end
    lst_box.selection_clear(0, END)
    temp = lst_box.index(ACTIVE) - 1

    if temp == -1:
        temp = lst_box.size() - 1

    lst_box.activate(temp)
    lst_box.select_set(temp)
    lst_box.see(temp)
    return 'break'


def down(lst_box):#to go down and if out of options, loop back to the start
    lst_box.selection_clear(0, END)
    temp = lst_box.index(ACTIVE) + 1

    if temp == lst_box.size():
        temp = 0

    lst_box.activate(temp)
    lst_box.select_set(temp)
    lst_box.see(temp)

    return 'break'


def focus_on_enter(event=None): #focuses on the entry for adding a new playlisr
    global entry_playlist
    entry_playlist.focus()
    return 'break'


def show_playlists(event=None):
    global playlist_box
    global playlists
    global entry_playlist
    global add_btn
    global playlist_box
    global song_list
    global upper_frame

    if playlist_btn['state'] == DISABLED:
        return 'break'

    if add_btn.winfo_ismapped() == False:
        song_list.grid_forget()

        entry_playlist.grid(row=0, column=0, columnspan=2, sticky='nswe')
        add_btn.grid(row=0, column=1, sticky='w')
        playlist_box.grid(row=1, rowspan=2, sticky='nswe')
        playlist_box.insert(END, *['option 1 ', 'option 2'])

    playlist_box.delete(0, END)

    playlists = pickle.load(open("playlists.dat", "rb"))

    temp_li = ['≡ ' + a.playlist_name for a in playlists]
    if len(temp_li) > 1:
        playlist_box.insert(END, *temp_li[1:len(temp_li)])
    else:
        playlist_box.insert(END, "No Songs found...")
    playlist_box.activate(0)
    playlist_box.select_set(0)
    playlist_box.focus()
    menu_options(2)


def show_playlist_songs(event=None,playlist_n=-1):
    global current_song_list
    global playlist_number

    temp = pickle.load(open("playlists.dat", "rb"))
    if len(temp)==1:
        return 'break'

    menu_options(3)

    if playlist_n==-1:
        playlist_number = playlist_box.index(ACTIVE) + 1
    else:
        playlist_number =playlist_n

    if add_btn.winfo_ismapped() == True:
        entry_playlist.grid_forget()
        add_btn.grid_forget()
        playlist_box.grid_forget()

    if song_list.winfo_ismapped() == False:
        song_list.grid(row=0, rowspan=2, sticky='nswe')

    song_list.focus()
    song_list.delete(0, END)


    playlist_lbl.configure(text='≡ '+temp[playlist_number].playlist_name)
    current_song_list = temp[playlist_number].songs

    if len(current_song_list) == 0:
        song_list.insert(END, "No Songs found...")
        return 'break'

    song_list.insert(END, *[os.path.splitext(os.path.split(a)[1])[0] for a in current_song_list])
    song_list.activate(0)
    song_list.see(0)
    scroll.config(command=playlist_box.yview)


def add_song_to_playlist(playlist_number):
    temp = pickle.load(open("playlists.dat", "rb"))
    selected_temp = song_list.curselection()
    temp[playlist_number].songs.extend([current_song_list[i] for i in selected_temp])
    # print(temp[playlist_number].songs)
    pickle.dump(temp, open("playlists.dat", "wb"))


def add_all_options():
    global playlist_number
    playlist_number = []
    sub_popup.delete(0, END)
    temp = pickle.load(open("playlists.dat", "rb"))
    i = 1
    while True:
        try:

            sub_popup.add_command(label=temp[i].playlist_name, command=lambda ply_n=i: add_song_to_playlist(ply_n))

            i += 1
        except:
            break


def create_playlist(event=None):
    playlist_box.focus()

    if entry_playlist.get() == '':
        return 'break'

    temp = pickle.load(open("playlists.dat", "rb"))
    temp.insert(len(temp), play(entry_playlist.get(), []))
    pickle.dump(temp, open("playlists.dat", "wb"))

    sub_popup.add_command(label=entry_playlist.get())

    entry_playlist.delete(0, END)
    show_playlists()
    add_all_options()


def mouse_popup(event):
    global popup_menu
    global adding_songs

    try:
        if adding_songs.is_alive():
            return 'break'
    except:
        ()

    try:
        popup_menu.tk_popup(event.x_root, event.y_root)
    except:
        ()


def key_popup(event):
    global popup_menu
    global adding_songs

    try:
        if adding_songs.is_alive():
            return 'break'
    except:
        ()
    selection = event.widget.curselection()
    if selection:
        item = selection[0]
        rootx = event.widget.winfo_rootx()
        rooty = event.widget.winfo_rooty()
        itemx, itemy, itemwidth, itemheight = event.widget.bbox(item)
        popup_menu.tk_popup(rootx + event.widget.winfo_width() - 10, rooty + itemy + 10)


def menu_options(option_number): #option=1 for all songs, option=2 for playlist select, option =3 for playlist_songs
    popup_menu.delete(0, END)
    popup_menu.add_command(label="cancel")
    popup_menu.add_separator()
    if option_number==1:
        popup_menu.add_cascade(label="add to..", menu=sub_popup)


    elif option_number==2:
        popup_menu.add_command(label="delete playlist",command=delete_playlist)

    else:

        popup_menu.add_command(label="remove from playlist", command=remove_from_playlist)

def handle_focus_in(event=None):
    entry_playlist.delete(0, END)
    entry_playlist.config(fg='black')


def handle_focus_out(event=None):
    entry_playlist.delete(0,END)
    entry_playlist.config(fg='grey')
    entry_playlist.insert(0, "create new playlist...")

##########################
def load_settings():
    try:
        temp = pickle.load(open("settings.dat", "rb"))
        player.volume = temp.volume
    except:
        player.volume=1
        pickle.dump(settings(volume=player.volume), open("settings.dat", "wb"))


def save_settings():
   # print(player.volume)
    pickle.dump(settings(volume=player.volume),open("settings.dat","wb"))
    window.destroy()

def refresh(event=None):
    global adding_songs
    try:
        if adding_songs.is_alive():
            return 'break'
    except:()
         # print("avoided")

    show_all_songs()
    adding_songs = threading.Thread(target=add_all_songs)
    adding_songs.start()

###### decorations #######

def add_frames():
    global lower_frame
    global upper_frame
    global left_frame
    global top_frame
    top_frame = Frame(window, background="pink")
    lower_frame = Frame(window, background=var_color)
    upper_frame = Frame(window)
    left_frame = Frame(window, background="white")

    top_frame.grid(row=0, column=1, sticky="nsew")
    upper_frame.grid(row=1, column=1, sticky="nsew")
    lower_frame.grid(row=2, column=1, sticky="nsew")
    left_frame.grid(row=0, column=0, sticky="nsew", rowspan=3)

    # window.grid_columnconfigure(0, weight=0)
    window.grid_rowconfigure(0, weight=0)
    window.grid_rowconfigure(1, weight=1)

    window.grid_columnconfigure(1, weight=3)
    # window.grid_rowconfigure(0, weight=3)

    lower_frame.grid_columnconfigure(0, weight=5)  # back button frame
    lower_frame.grid_columnconfigure(1, weight=1)  # play button frame
    lower_frame.grid_columnconfigure(2, weight=5)  # forward button frame

    lower_frame.grid_rowconfigure(0, weight=1)  # all 3 control buttons frame
    left_frame.rowconfigure(4, weight=1)

    upper_frame.grid_columnconfigure(0, weight=1)

    upper_frame.grid_rowconfigure(0, weight=2)
    upper_frame.grid_rowconfigure(1, weight=1)

    top_frame.grid_columnconfigure(0, weight=1)


def add_widgets():
    global play_btn
    global back_btn
    global forward_btn

    global loop_btn
    global shuffle_btn
    global volume_btn

    global playing_slider

    global playlist_btn
    global dir_btn

    global scroll
    global song_list

    global play_time_lbl
    global total_play_time_lbl

    global search_btn
    global all_btn

    global stat_lbl

    global playlist_lbl

    global refresh_btn
    global info_btn
    #### playlist widgets ####
    global entry_playlist
    global add_btn
    global playlist_box

    global popup_menu
    global sub_popup
    ###########################
    playlist_lbl = Label(top_frame, text='ALL')
    playlist_lbl.grid(row=0, rowspan=2, sticky='new')

    scroll = Scrollbar(upper_frame)  # song list scroll bar
    scroll.grid(row=0, column=1, rowspan=2, sticky='nsew')  #

    song_list = Listbox(upper_frame, yscrollcommand=scroll.set, activestyle='none',selectbackground='grey',selectmode=EXTENDED)  # song list box
    song_list.grid(row=0, rowspan=2, sticky='nswe')

    song_list.focus()  # focuses on song list else manual clicking on listbox would be required

    window.unbind_all("<<NextWindow>>")

    song_list.bind('<Right>', play_next_song)  # controls playing next/previous song play with arrow keys
    song_list.bind('<Left>', play_previous_song)  #
    song_list.bind('<Up>', lambda event: up(lst_box=song_list))
    song_list.bind('<Down>', lambda event: down(lst_box=song_list))
    song_list.bind('<space>', control_song)  # space controls play/pause
    song_list.bind('<Double-1>', lambda event: play_new_song(isclicked=1))  # double left click on new song plays it
    song_list.bind('<Return>', lambda event: play_new_song(isclicked=1))  # double left click on new song plays it
    song_list.bind('a', show_all_songs)
    song_list.bind("<Button-3>", mouse_popup)
    song_list.bind("o", key_popup)
    song_list.bind('r',refresh)

    #################   main control buttons   ######################
    back_btn = Button(lower_frame, text="◀◀", command=play_previous_song)  # back button
    back_btn.grid(column=0, row=0, sticky='e')  #

    play_btn = Button(lower_frame, text=" ▶ ", command=control_song)  # play button
    play_btn.grid(column=1, row=0)  #

    forward_btn_btn = Button(lower_frame, text="▶▶", command=play_next_song)  # forward button
    forward_btn_btn.grid(column=2, row=0, sticky='w')  #

    loop_btn = Button(lower_frame, text='↻', command=loop_control)  # loop button
    loop_btn.grid(column=2, row=0)  #
    song_list.bind('l', loop_control)

    shuffle_btn = Button(lower_frame, text='➡', command=ctrl_shuffle)  # 🔀
    shuffle_btn.grid(row=0, column=0)
    song_list.bind('s', ctrl_shuffle)

    playing_slider = Scale(lower_frame, orient='horizontal', length=350, showvalue=0)
    playing_slider.grid(row=1, columnspan=3)
    playing_slider.bind('<ButtonPress-1>', hold)
    playing_slider.bind('<ButtonRelease-1>', rel)

    ################### current time shower #################

    play_time_lbl = Label(lower_frame, text='0:00:00',bg=var_color,fg='white')
    play_time_lbl.grid(row=1, column=0, sticky='w')


    total_play_time_lbl = Label(lower_frame, text='0:00:00',bg=var_color,fg='white')
    total_play_time_lbl.grid(row=1, column=2, sticky='e')

    ##########################################################

    ############### left keys ###################

    search_btn = PopupEntryButton(left_frame, text='🔍', width=3)
    search_btn.grid(row=0, sticky='s')
    song_list.bind('q', search_btn.toggle)

    volume_btn = PopupSliderButton(left_frame, text='🔈', width=3)
    volume_btn.grid(row=1, column=0)
    song_list.bind('v', volume_btn.toggle)
    song_list.bind('-', volume_btn.dec_vol)
    song_list.bind('=', volume_btn.inc_vol)

    all_btn = Button(left_frame, text='All', width=3, command=show_all_songs)
    all_btn.grid(row=2)
    song_list.bind('p', show_playlists)  # pressing p' changed to playlist mode

    playlist_btn = Button(left_frame, text='≡', width=3, command=show_playlists)
    playlist_btn.grid(row=3, sticky='n')

    dir_btn = Button(left_frame, text='dir', command=choose_directory, width=3)  # options button
    song_list.bind('d', choose_directory)  # pressing 'd' asks for directory
    dir_btn.grid(row=4, sticky='n')

    ############## playlist #############

    entry_playlist = Entry(top_frame, bg='light grey')
    entry_playlist.config(fg='grey')
    entry_playlist.insert(0, "create new playlist...")
    entry_playlist.bind("<Return>", create_playlist)
    entry_playlist.bind("<FocusIn>", handle_focus_in)
    entry_playlist.bind("<FocusOut>", handle_focus_out)

    add_btn = Button(top_frame, text="+", command=create_playlist)

    playlist_box = Listbox(upper_frame, yscrollcommand=scroll.set, activestyle='none', selectmode=SINGLE,selectbackground="grey")
    playlist_box.bind('a', show_all_songs)
    playlist_box.bind('j', focus_on_enter)
    playlist_box.bind('<Right>', play_next_song)  # controls playing next/previous song play with arrow keys
    playlist_box.bind('<Left>', play_previous_song)  #
    playlist_box.bind('<Up>', lambda event: up(lst_box=playlist_box))
    playlist_box.bind('<Down>', lambda event: down(lst_box=playlist_box))
    playlist_box.bind('<space>', control_song)  # space controls play/pause
    playlist_box.bind('s', ctrl_shuffle)
    playlist_box.bind('l', loop_control)
    playlist_box.bind('d', choose_directory)
    playlist_box.bind('<Double-1>', show_playlist_songs)
    playlist_box.bind('<Return>', show_playlist_songs)
    playlist_box.bind("<Button-3>", mouse_popup)
    playlist_box.bind("o", key_popup)
    playlist_box.bind('r', refresh)
    popup_menu = Menu(window, tearoff=0)

    sub_popup = Menu(popup_menu, tearoff=0)
    sub_popup.add_command(label="cancel")
    sub_popup.add_separator()

    ######################################
    refresh_btn=Button(left_frame,text="🗘",width=3,command=refresh)
    refresh_btn.grid(row=4,sticky='s')


    stat_lbl = Label(lower_frame, text='',bg=var_color,fg='white')
    stat_lbl.grid(row=2, column=0, columnspan=3)

    song_list.bind('<Escape>', min)
    playlist_box.bind('<Escape>', min)


##########################

def play_timer():
    global play_time_lbl
    global playing_slider
    global slider_pressed

    try:
        if player.time >= src.duration:
            play_next_song()

    except:
        control_song(n=-1)

    if slider_pressed == False:
        play_time_lbl.configure(text=str(timedelta(seconds=int(player.time))))
        playing_slider.set(int(player.time))
        slider_pressed = False
    else:
        play_time_lbl.configure(text=str(timedelta(seconds=int(playing_slider.get()))))

    play_time_lbl.after(1000, play_timer)


### defaults ###
current_index = 0
current_time = 0.0
slider_pressed = False
loop_status = 2
shuffle = False
current_song_list = []
actual_song_list = []
extensions = ("mp3")
var_color="#383a3b"
#################

if __name__ == "__main__":
    player = media.Player()
    src = ""
    dir_name = ""
    window = Tk()

    window.title("Py3Player")
    window.geometry("500x300")
    window.resizable(False, False)

    load_settings()
    add_frames()
    add_widgets()

    show_all_songs()


    play_timer()
    window.protocol("WM_DELETE_WINDOW", save_settings)
    window.mainloop()